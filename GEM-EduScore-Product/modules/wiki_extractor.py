"""Safe, bounded extraction of education evidence from team wiki pages."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import ipaddress
from pathlib import Path
import random
import re
import socket
import time
from typing import Callable
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser


WIKI_USER_AGENT = "GEM-EduScore/0.6 (user-initiated education evaluation; compatible browser fetch)"
MAX_PAGE_BYTES = 5 * 1024 * 1024
MAX_SCRIPT_BUNDLE_BYTES = 4 * 1024 * 1024
MAX_TOTAL_CHARACTERS = 120_000
DEFAULT_MAX_PAGES = 6
FETCH_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}
RELATED_KEYWORDS = {
    "education": 15,
    "educational": 14,
    "communication": 12,
    "engagement": 12,
    "outreach": 11,
    "inclusivity": 9,
    "inclusive": 8,
    "human-practices": 8,
    "human practices": 8,
    "public": 5,
    "contribution": 4,
    "implementation": 3,
}
EXCLUDED_SUFFIXES = (
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".zip", ".png", ".jpg", ".jpeg",
    ".gif", ".svg", ".webp", ".mp3", ".mp4", ".css", ".js", ".json", ".xml",
)


class WikiExtractionError(ValueError):
    """Raised with an actionable, user-facing wiki ingestion message."""


@dataclass(frozen=True)
class WikiPageInfo:
    title: str
    url: str
    characters: int


@dataclass(frozen=True)
class WikiExtractionInfo:
    name: str
    extension: str
    characters: int
    words: int
    lines: int
    preview: str
    page_count: int
    pages: list[dict]
    start_url: str


FetchHTML = Callable[[str], tuple[str, str]]


def extract_wiki_material(
    start_url: str,
    *,
    crawl_related: bool = True,
    max_pages: int = DEFAULT_MAX_PAGES,
    fetcher: FetchHTML | None = None,
) -> tuple[str, dict]:
    """Fetch one wiki or a bounded set of same-team education-related pages."""
    start_url = normalize_public_url(start_url)
    max_pages = max(1, min(int(max_pages), 12))
    production_fetch = fetcher is None
    fetcher = fetcher or _fetch_html

    if production_fetch and not _robots_allows(start_url):
        raise WikiExtractionError("该站点的 robots.txt 不允许自动读取此页面。")

    queue: list[tuple[int, str]] = [(100, start_url)]
    queued = {start_url}
    visited: set[str] = set()
    pages: list[tuple[WikiPageInfo, str]] = []
    scope = _site_scope(start_url)
    total_characters = 0
    bundle_cache: dict[str, str] = {}

    while queue and len(pages) < max_pages and total_characters < MAX_TOTAL_CHARACTERS:
        queue.sort(key=lambda item: item[0], reverse=True)
        _, requested_url = queue.pop(0)
        if requested_url in visited:
            continue
        visited.add(requested_url)
        try:
            final_url, html = fetcher(requested_url)
        except WikiExtractionError:
            if not pages:
                raise
            continue
        except Exception as exc:
            if not pages:
                raise WikiExtractionError(f"无法读取 Wiki：{type(exc).__name__}。请检查网址和网络连接。") from exc
            continue

        final_url = normalize_public_url(final_url)
        if not _within_scope(final_url, scope):
            if not pages:
                raise WikiExtractionError("Wiki 重定向到了其他站点，已为安全起见停止读取。")
            continue

        title, text, links = _parse_html(final_url, html)
        if len(text) < 120:
            spa_title, spa_text, spa_links = _extract_spa_page(
                final_url,
                html,
                bundle_cache=bundle_cache,
            )
            if spa_text:
                title = spa_title or title
                text = spa_text
                links.extend(spa_links)
            else:
                if not pages:
                    raise WikiExtractionError(
                        "检测到前端渲染页面，但未能从其公开脚本中定位当前页面正文。"
                        "该 Wiki 可能使用了分块加载、加密数据或不受支持的渲染方式。"
                    )
                continue

        remaining = MAX_TOTAL_CHARACTERS - total_characters
        text = text[:remaining]
        page_info = WikiPageInfo(title=title, url=final_url, characters=len(text))
        pages.append((page_info, text))
        total_characters += len(text)

        if crawl_related:
            for link_url, anchor_text in links:
                normalized_link = _normalize_link(final_url, link_url)
                if not normalized_link or normalized_link in queued or normalized_link in visited:
                    continue
                if not _within_scope(normalized_link, scope):
                    continue
                score = _related_score(normalized_link, anchor_text)
                if score <= 0:
                    continue
                queue.append((score, normalized_link))
                queued.add(normalized_link)

    if not pages:
        raise WikiExtractionError("没有从该 Wiki 读取到可分析的公开正文。")

    material_blocks = []
    for index, (page, text) in enumerate(pages, 1):
        material_blocks.append(
            f"[WIKI PAGE {index}]\nTitle: {page.title}\nURL: {page.url}\n\n{text}\n[/WIKI PAGE {index}]"
        )
    material = "\n\n".join(material_blocks)
    page_dicts = [asdict(page) for page, _ in pages]
    info = WikiExtractionInfo(
        name=f"Wiki · {urlsplit(start_url).netloc}",
        extension="WIKI",
        characters=len(material),
        words=len(material.split()),
        lines=len(material.splitlines()),
        preview="\n".join(f"{page.title} — {page.url}" for page, _ in pages),
        page_count=len(pages),
        pages=page_dicts,
        start_url=start_url,
    )
    return material, asdict(info)


def normalize_public_url(url: str) -> str:
    """Normalize and validate a public HTTP(S) URL, blocking local network targets."""
    raw = url.strip()
    if not raw:
        raise WikiExtractionError("请填写 Wiki 页面网址。")
    if "://" not in raw:
        raw = f"https://{raw}"
    raw, _ = urldefrag(raw)
    parsed = urlsplit(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise WikiExtractionError("Wiki 地址必须是公开的 http:// 或 https:// 网页。")
    if parsed.username or parsed.password:
        raise WikiExtractionError("Wiki 地址不能包含用户名或密码。")
    try:
        port = parsed.port
    except ValueError as exc:
        raise WikiExtractionError("Wiki 地址中的端口格式不正确。") from exc
    if port not in {None, 80, 443}:
        raise WikiExtractionError("出于安全考虑，Wiki 地址只允许使用 80 或 443 端口。")
    _validate_public_host(parsed.hostname)
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))


def _validate_public_host(hostname: str) -> None:
    lowered = hostname.rstrip(".").lower()
    if lowered in {"localhost", "localhost.localdomain"} or lowered.endswith((".local", ".internal")):
        raise WikiExtractionError("不能读取本机或内网 Wiki 地址。")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(lowered, None, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise WikiExtractionError("无法解析 Wiki 域名，请检查网址是否正确。") from exc
    if not addresses:
        raise WikiExtractionError("无法解析 Wiki 域名。")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise WikiExtractionError("不能读取指向本机、内网或保留地址的 Wiki。")


def _fetch_html(url: str) -> tuple[str, str]:
    try:
        import httpx
    except ImportError as exc:
        raise WikiExtractionError("缺少网页读取组件。请重新运行双击启动器以安装依赖。") from exc

    current = url
    headers = {
        "User-Agent": WIKI_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    }
    with httpx.Client(timeout=httpx.Timeout(20.0, connect=8.0), follow_redirects=False, headers=headers) as client:
        for _ in range(6):
            current = normalize_public_url(current)
            last_error: Exception | None = None
            for attempt in range(FETCH_ATTEMPTS):
                try:
                    with client.stream("GET", current) as response:
                        if response.status_code in RETRYABLE_STATUS_CODES and attempt < FETCH_ATTEMPTS - 1:
                            response.read()
                            _retry_pause(attempt, response.headers.get("retry-after"))
                            continue
                        if response.status_code in {301, 302, 303, 307, 308}:
                            location = response.headers.get("location")
                            if not location:
                                raise WikiExtractionError("Wiki 返回了无目标地址的重定向。")
                            current = urljoin(current, location)
                            break
                        response.raise_for_status()
                        content_type = response.headers.get("content-type", "").lower()
                        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                            raise WikiExtractionError("该网址不是可读取的 HTML Wiki 页面。")
                        length = response.headers.get("content-length")
                        if length and int(length) > MAX_PAGE_BYTES:
                            raise WikiExtractionError("Wiki 单页超过 5 MB，已停止读取。")
                        chunks = []
                        total = 0
                        for chunk in response.iter_bytes():
                            total += len(chunk)
                            if total > MAX_PAGE_BYTES:
                                raise WikiExtractionError("Wiki 单页超过 5 MB，已停止读取。")
                            chunks.append(chunk)
                        encoding = response.encoding or "utf-8"
                        return str(response.url), b"".join(chunks).decode(encoding, errors="replace")
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    if exc.response.status_code in RETRYABLE_STATUS_CODES and attempt < FETCH_ATTEMPTS - 1:
                        _retry_pause(attempt, exc.response.headers.get("retry-after"))
                        continue
                    raise WikiExtractionError(f"Wiki 返回 HTTP {exc.response.status_code}。请确认页面公开可访问。") from exc
                except httpx.RequestError as exc:
                    last_error = exc
                    if attempt < FETCH_ATTEMPTS - 1:
                        _retry_pause(attempt)
                        continue
                    raise WikiExtractionError("连接 Wiki 失败。平台已自动重试；请稍后再试或检查站点状态。") from exc
            else:
                if isinstance(last_error, httpx.HTTPStatusError):
                    raise WikiExtractionError(f"Wiki 返回 HTTP {last_error.response.status_code}。请稍后再试。") from last_error
                raise WikiExtractionError("连接 Wiki 失败。平台已自动重试，请稍后再试。") from last_error
            continue
    raise WikiExtractionError("Wiki 重定向次数过多，已停止读取。")


def _robots_allows(url: str) -> bool:
    parsed = urlsplit(url)
    robots_url = urlunsplit((parsed.scheme, parsed.netloc, "/robots.txt", "", ""))
    try:
        _, robots_text = _fetch_text_resource(robots_url, max_bytes=512_000)
    except Exception:
        return True
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(robots_text.splitlines())
    return parser.can_fetch(WIKI_USER_AGENT, url)


def _fetch_text_resource(url: str, *, max_bytes: int) -> tuple[str, str]:
    try:
        import httpx
    except ImportError as exc:
        raise WikiExtractionError("缺少网页读取组件。") from exc
    current = url
    headers = {"User-Agent": WIKI_USER_AGENT, "Accept": "text/plain,application/javascript,*/*;q=0.8"}
    with httpx.Client(timeout=httpx.Timeout(20.0, connect=8.0), follow_redirects=False, headers=headers) as client:
        for _ in range(4):
            current = normalize_public_url(current)
            response = None
            last_error: Exception | None = None
            for attempt in range(FETCH_ATTEMPTS):
                try:
                    response = client.get(current)
                    transient_resource_status = response.status_code in RETRYABLE_STATUS_CODES or (
                        response.status_code == 404 and "/assets/" in urlsplit(current).path
                    )
                    if transient_resource_status and attempt < FETCH_ATTEMPTS - 1:
                        _retry_pause(attempt, response.headers.get("retry-after"))
                        continue
                    break
                except httpx.RequestError as exc:
                    last_error = exc
                    if attempt < FETCH_ATTEMPTS - 1:
                        _retry_pause(attempt)
                        continue
                    raise WikiExtractionError("读取 Wiki 公开资源失败，平台已自动重试。") from exc
            if response is None:
                raise WikiExtractionError("读取 Wiki 公开资源失败。") from last_error
            if response.status_code in {301, 302, 303, 307, 308}:
                current = urljoin(current, response.headers.get("location", ""))
                continue
            response.raise_for_status()
            if len(response.content) > max_bytes:
                raise WikiExtractionError("Wiki 公开资源过大，已停止读取。")
            return str(response.url), response.text
    raise WikiExtractionError("robots.txt 重定向次数过多。")


def _retry_pause(attempt: int, retry_after: str | None = None) -> None:
    """Brief bounded backoff for transient CDN and network failures."""
    delay = min(4.0, 0.45 * (2**attempt) + random.uniform(0.05, 0.25))
    if retry_after:
        try:
            delay = min(5.0, max(delay, float(retry_after)))
        except ValueError:
            pass
    time.sleep(delay)


def _parse_html(page_url: str, html: str) -> tuple[str, str, list[tuple[str, str]]]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise WikiExtractionError("缺少 HTML 正文提取组件。请重新运行双击启动器。") from exc

    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.find("h1") or soup.find("title")
    title = title_node.get_text(" ", strip=True) if title_node else urlsplit(page_url).path.rstrip("/").split("/")[-1]
    links = [
        (str(anchor.get("href", "")), anchor.get_text(" ", strip=True))
        for anchor in soup.find_all("a", href=True)
    ]

    for image in soup.find_all("img"):
        alt = str(image.get("alt", "")).strip()
        if alt and len(alt) > 3:
            image.insert_after(f" [Image description: {alt}] ")
    for tag in soup.find_all(["script", "style", "noscript", "svg", "form", "button", "dialog"]):
        tag.decompose()

    root = soup.find("main") or soup.find("article") or soup.find(attrs={"role": "main"}) or soup.body or soup
    for tag in root.find_all(["nav", "footer", "header", "aside"]):
        tag.decompose()
    text = _clean_web_text(root.get_text("\n", strip=True))
    return title or "Wiki page", text, links


def _extract_spa_page(
    page_url: str,
    html: str,
    *,
    bundle_cache: dict[str, str],
) -> tuple[str, str, list[tuple[str, str]]]:
    """Extract a route component from a public Vite/React-style JavaScript bundle."""
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise WikiExtractionError("缺少 SPA Wiki 解析组件。请重新运行双击启动器。") from exc

    soup = BeautifulSoup(html, "html.parser")
    script_urls = []
    for script in soup.find_all("script", src=True):
        script_type = str(script.get("type", "")).lower()
        source = str(script.get("src", "")).strip()
        if not source or (script_type and script_type != "module" and not source.lower().endswith(".js")):
            continue
        try:
            absolute = normalize_public_url(urljoin(page_url, source))
        except WikiExtractionError:
            absolute = None
        if absolute and urlsplit(absolute).netloc == urlsplit(page_url).netloc:
            script_urls.append(absolute)

    loaded_bundles = 0
    fetch_errors: list[Exception] = []
    for script_url in script_urls[:4]:
        if script_url not in bundle_cache:
            try:
                _, bundle_cache[script_url] = _fetch_text_resource(
                    script_url,
                    max_bytes=MAX_SCRIPT_BUNDLE_BYTES,
                )
            except Exception as exc:
                fetch_errors.append(exc)
                continue
        loaded_bundles += 1
        bundle = bundle_cache[script_url]
        component_name, route_title = _find_route_component(bundle, page_url)
        if not component_name:
            continue
        component_source = _extract_component_source(bundle, component_name)
        if not component_source:
            continue
        strings = _extract_js_content_strings(component_source)
        text = _clean_web_text("\n".join(strings))
        if len(text) < 120:
            continue
        route_links = _extract_spa_route_links(bundle, page_url)
        return route_title or "Wiki page", text, route_links
    if script_urls and loaded_bundles == 0 and fetch_errors:
        raise WikiExtractionError(
            "已识别前端渲染页面，但其公开脚本资源暂时读取失败。平台已自动重试；"
            "这通常是 Wiki CDN 短暂波动，请稍后再试。"
        ) from fetch_errors[-1]
    return "", "", []


def _find_route_component(bundle: str, page_url: str) -> tuple[str | None, str | None]:
    routes = _route_candidates(page_url)
    for route in routes:
        escaped = re.escape(route)
        patterns = [
            rf'title:"([^"]+)",path:"{escaped}",component:([A-Za-z_$][\w$]*)',
            rf'path:"{escaped}",component:([A-Za-z_$][\w$]*)',
            rf'path:"{escaped}",element:[A-Za-z_$][\w$]*\.jsx\(([A-Za-z_$][\w$]*),',
            rf'path:"{escaped}",element:[A-Za-z_$][\w$]*\.createElement\(([A-Za-z_$][\w$]*),',
        ]
        match = re.search(patterns[0], bundle)
        if match:
            return match.group(2), _decode_js_string(match.group(1))
        match = re.search(patterns[1], bundle)
        if match:
            return match.group(1), None
        for pattern in patterns[2:]:
            match = re.search(pattern, bundle)
            if match:
                return match.group(1), _route_title_hint(bundle, route)
    return None, None


def _route_candidates(page_url: str) -> list[str]:
    path = urlsplit(page_url).path.rstrip("/") or "/"
    parts = [part for part in path.split("/") if part]
    candidates = [path]
    if re.fullmatch(r"20\d{2}\.igem\.wiki", urlsplit(page_url).hostname or "") and len(parts) >= 2:
        candidates.insert(0, "/" + "/".join(parts[1:]))
    if path.endswith(".html"):
        candidates.append(path[:-5])
        candidates.append("/" + Path(path).stem)
    candidates.append("/" + (parts[-1] if parts else ""))
    candidates.extend(candidate.lstrip("/") for candidate in list(candidates) if candidate != "/")
    return list(dict.fromkeys(candidates))


def _route_title_hint(bundle: str, route: str) -> str | None:
    route_with_slash = "/" + route.lstrip("/")
    match = re.search(rf'title:"([^"]+)",path:"{re.escape(route_with_slash)}"', bundle)
    return _decode_js_string(match.group(1)) if match else None


def _extract_component_source(bundle: str, component_name: str) -> str | None:
    patterns = [
        f"function {component_name}(",
        f"const {component_name}=",
        f"let {component_name}=",
        f"var {component_name}=",
        f",{component_name}=",
        f";{component_name}=",
    ]
    start = next((bundle.find(pattern) for pattern in patterns if bundle.find(pattern) >= 0), -1)
    if start < 0:
        return None
    open_brace = bundle.find("{", start)
    if open_brace < 0:
        return None
    end = _matching_js_brace(bundle, open_brace)
    return bundle[start : end + 1] if end is not None else None


def _matching_js_brace(source: str, open_brace: int) -> int | None:
    depth = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = False
    index = open_brace
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if line_comment:
            if character in "\r\n":
                line_comment = False
            index += 1
            continue
        if block_comment:
            if character == "*" and following == "/":
                block_comment = False
                index += 2
                continue
            index += 1
            continue
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            index += 1
            continue
        if character in {'"', "'", "`"}:
            quote = character
        elif character == "/" and following == "/":
            line_comment = True
            index += 2
            continue
        elif character == "/" and following == "*":
            block_comment = True
            index += 2
            continue
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _extract_js_content_strings(source: str) -> list[str]:
    strings: list[str] = []
    index = 0
    while index < len(source):
        if source[index] not in {'"', "'", "`"}:
            index += 1
            continue
        quote = source[index]
        start = index
        index += 1
        raw = []
        escaped = False
        while index < len(source):
            character = source[index]
            if escaped:
                raw.extend(["\\", character])
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                break
            else:
                raw.append(character)
            index += 1
        value = _decode_js_string("".join(raw))
        context = source[max(0, start - 40) : start]
        if _is_js_content_string(value, context):
            strings.append(value.strip())
        index += 1
    return list(dict.fromkeys(strings))


def _decode_js_string(value: str) -> str:
    replacements = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v"}

    def replace_escape(match: re.Match[str]) -> str:
        token = match.group(1)
        if token in replacements:
            return replacements[token]
        if token.startswith("x") and len(token) == 3:
            return chr(int(token[1:], 16))
        if token.startswith("u{"):
            return chr(int(token[2:-1], 16))
        if token.startswith("u") and len(token) == 5:
            return chr(int(token[1:], 16))
        return token

    return re.sub(r"\\(u\{[0-9A-Fa-f]+\}|u[0-9A-Fa-f]{4}|x[0-9A-Fa-f]{2}|.)", replace_escape, value)


def _is_js_content_string(value: str, context: str) -> bool:
    text = " ".join(value.split()).strip()
    if len(text) < 3 or "${" in text:
        return False
    lowered = text.lower()
    if lowered in {
        "onest", "div", "span", "section", "main", "article", "aside", "nav", "header", "footer",
        "figure", "button", "ul", "ol", "li", "h1", "h2", "h3", "p", "a", "br", "img",
        "row", "container", "container-fluid", "col", "col-12", "col-lg-9", "col-lg-3",
    }:
        return False
    if re.search(r"(?:className|class|href|id|style)\s*:\s*$", context):
        return False
    if lowered.startswith("#"):
        return False
    if lowered.startswith(("http://", "https://", "data:", "/assets/")):
        return False
    if any(lowered.endswith(suffix) for suffix in EXCLUDED_SUFFIXES):
        return False
    if lowered.endswith("-section") or re.fullmatch(r"#[0-9a-f]{3,8}", lowered):
        return False
    if any(token in lowered for token in ("sans-serif", "linear-gradient", "object-fit", "font-weight")):
        return False
    if "rgba(" in lowered or ("px" in lowered and re.search(r"\d", lowered)):
        return False
    if re.fullmatch(r"(?:\d+(?:\.\d+)?(?:px|rem|em|%|vh|vw)|normal|inherit|center|contain|cover)", lowered):
        return False
    if re.fullmatch(r"(?:\d+(?:\.\d+)?(?:px|rem|em|%|vh|vw)?\s*){1,4}", lowered):
        return False
    letters = sum(character.isalpha() for character in text)
    short_named_term = bool(
        re.fullmatch(r"[A-Za-z][A-Za-z0-9+._-]{1,15}", text)
        and re.search(r"(?:title|children)\s*:\s*$", context)
    )
    if letters < 3 and not short_named_term:
        return False
    if " " not in text and re.fullmatch(r"[a-z][a-z0-9_-]{0,28}", text):
        return "title:" in context or "children:" in context
    return True


def _extract_spa_route_links(bundle: str, page_url: str) -> list[tuple[str, str]]:
    links = []
    for match in re.finditer(r'title:"([^"]+)",path:"([^"]+)"', bundle):
        title = _decode_js_string(match.group(1))
        route = _decode_js_string(match.group(2))
        if not route.startswith("/"):
            continue
        links.append((_spa_route_href(page_url, route), title))
    return list(dict.fromkeys(links))


def _spa_route_href(page_url: str, route: str) -> str:
    parsed = urlsplit(page_url)
    parts = [part for part in parsed.path.split("/") if part]
    if re.fullmatch(r"20\d{2}\.igem\.wiki", parsed.hostname or "") and parts:
        route = f"/{parts[0]}{route}"
    return urlunsplit((parsed.scheme, parsed.netloc, route, "", ""))


def _clean_web_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    cleaned: list[str] = []
    previous = None
    for line in lines:
        if not line or line == previous:
            continue
        cleaned.append(line)
        previous = line
    return "\n".join(cleaned).strip()


def _normalize_link(base_url: str, href: str) -> str | None:
    href = href.strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    absolute = urljoin(base_url, href)
    path = urlsplit(absolute).path.lower()
    if path.endswith(EXCLUDED_SUFFIXES):
        return None
    absolute, _ = urldefrag(absolute)
    parsed = urlsplit(absolute)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    if parsed.username or parsed.password or port not in {None, 80, 443}:
        return None
    normalized_path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), normalized_path, parsed.query, ""))


def _related_score(url: str, anchor_text: str) -> int:
    haystack = f"{urlsplit(url).path.lower()} {anchor_text.lower()}"
    return max((score for keyword, score in RELATED_KEYWORDS.items() if keyword in haystack), default=0)


def _site_scope(url: str) -> tuple[str, str | None]:
    parsed = urlsplit(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    team_prefix = None
    if re.fullmatch(r"20\d{2}\.igem\.wiki", parsed.hostname or "") and path_parts:
        team_prefix = f"/{path_parts[0].lower()}"
    return parsed.netloc.lower(), team_prefix


def _within_scope(url: str, scope: tuple[str, str | None]) -> bool:
    parsed = urlsplit(url)
    host, team_prefix = scope
    if parsed.netloc.lower() != host:
        return False
    if team_prefix is None:
        return True
    path = parsed.path.lower().rstrip("/") or "/"
    return path == team_prefix or path.startswith(f"{team_prefix}/")
