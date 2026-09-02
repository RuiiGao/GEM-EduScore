"""Tests for bounded, same-team Wiki evidence extraction."""

from __future__ import annotations

import socket
import unittest
from unittest.mock import patch

from modules.wiki_extractor import (
    _extract_component_source,
    _extract_js_content_strings,
    _find_route_component,
    WikiExtractionError,
    extract_wiki_material,
    normalize_public_url,
)


PUBLIC_DNS_RESULT = [
    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
]


def _page(title: str, body: str, links: str = "") -> str:
    return f"""
    <html><head><title>{title}</title><script>ignore_script()</script></head>
    <body><nav>Repeated navigation</nav><main><h1>{title}</h1>
    <p>{body}</p><img alt="Workshop evidence photo">{links}</main><footer>Footer</footer></body></html>
    """


class WikiExtractorTests(unittest.TestCase):
    def setUp(self) -> None:
        long_context = (
            "The team documented audiences, learning goals, interactive workshops, participant feedback, "
            "outcome evaluation and iteration. " * 3
        )
        self.pages = {
            "https://2025.igem.wiki/test-team/": _page(
                "Test Team",
                long_context,
                '<a href="/test-team/education">Education</a>'
                '<a href="/test-team/communication">Public Engagement</a>'
                '<a href="/other-team/education">Other Team Education</a>'
                '<a href="/test-team/static/handbook.pdf">PDF handbook</a>',
            ),
            "https://2025.igem.wiki/test-team/education": _page("Education", long_context),
            "https://2025.igem.wiki/test-team/communication": _page("Communication", long_context),
        }

    def fetcher(self, url: str) -> tuple[str, str]:
        return url, self.pages[url]

    @patch("modules.wiki_extractor.socket.getaddrinfo", return_value=PUBLIC_DNS_RESULT)
    def test_discovers_only_related_pages_within_same_team(self, _: object) -> None:
        material, info = extract_wiki_material(
            "https://2025.igem.wiki/test-team/",
            crawl_related=True,
            max_pages=6,
            fetcher=self.fetcher,
        )
        self.assertEqual(info["page_count"], 3)
        self.assertIn("/test-team/education", material)
        self.assertIn("/test-team/communication", material)
        self.assertNotIn("/other-team/education", material)
        self.assertNotIn("ignore_script", material)
        self.assertNotIn("Repeated navigation", material)
        self.assertIn("Image description: Workshop evidence photo", material)

    @patch("modules.wiki_extractor.socket.getaddrinfo", return_value=PUBLIC_DNS_RESULT)
    def test_single_page_mode_does_not_crawl_links(self, _: object) -> None:
        _, info = extract_wiki_material(
            "https://2025.igem.wiki/test-team/",
            crawl_related=False,
            max_pages=6,
            fetcher=self.fetcher,
        )
        self.assertEqual(info["page_count"], 1)

    @patch("modules.wiki_extractor.socket.getaddrinfo", return_value=PUBLIC_DNS_RESULT)
    def test_vite_spa_extracts_route_component_from_bundle(self, _: object) -> None:
        shell = (
            '<html><head><title>McGill - iGEM 2025</title>'
            '<script type="module" src="/test-team/assets/index-demo.js"></script>'
            '</head><body><div id="root"></div></body></html>'
        )
        bundle = (
            'function s5(){return e.jsxs("p",{children:['
            '"Our education program defined audiences, goals and an interactive workshop. ",'
            '"Participants completed activities, provided feedback, and informed the next iteration. ",'
            '"The team published reusable teaching materials and documented observed learning outcomes."'
            ']})}'
            'const routes=[{title:"Education",path:"/education",component:s5},'
            '{title:"Inclusivity",path:"/inclusivity",component:q5}]'
        )

        def shell_fetcher(url: str) -> tuple[str, str]:
            return url, shell

        with patch(
            "modules.wiki_extractor._fetch_text_resource",
            return_value=("https://2025.igem.wiki/test-team/assets/index-demo.js", bundle),
        ):
            material, info = extract_wiki_material(
                "https://2025.igem.wiki/test-team/education",
                crawl_related=False,
                fetcher=shell_fetcher,
            )
        self.assertEqual(info["pages"][0]["title"], "Education")
        self.assertIn("Participants completed activities", material)
        self.assertNotIn("index-demo.js", material)

    def test_private_network_url_is_blocked(self) -> None:
        with self.assertRaisesRegex(WikiExtractionError, "本机、内网"):
            normalize_public_url("http://127.0.0.1/wiki")

    def test_react_router_element_route_used_by_epfl_is_supported(self) -> None:
        bundle = (
            'const search=[{title:"Education",path:"/education",keywords:["outreach"]}],x=1,'
            'fV=()=>{return s.jsxs("main",{children:['
            's.jsx("h2",{children:"Our Commitment to Educational Outreach"}),'
            's.jsx("p",{children:"Students completed hands-on synthetic biology workshops and reflected on learning outcomes."})'
            ']})},routes=s.jsx(Xt,{path:"education",element:s.jsx(fV,{})})'
        )
        component, title = _find_route_component(
            bundle,
            "https://2025.igem.wiki/epfl/education",
        )
        self.assertEqual(component, "fV")
        self.assertEqual(title, "Education")
        source = _extract_component_source(bundle, component)
        self.assertIsNotNone(source)
        text = "\n".join(_extract_js_content_strings(source or ""))
        self.assertIn("hands-on synthetic biology workshops", text)

    @patch("modules.wiki_extractor.socket.getaddrinfo", return_value=PUBLIC_DNS_RESULT)
    def test_spa_resource_failure_reports_transient_cdn_problem(self, _: object) -> None:
        shell = (
            '<html><head><title>SPA Wiki</title>'
            '<script type="module" src="/test-team/assets/index-demo.js"></script>'
            '</head><body><div id="root"></div></body></html>'
        )

        with patch(
            "modules.wiki_extractor._fetch_text_resource",
            side_effect=WikiExtractionError("temporary failure"),
        ):
            with self.assertRaisesRegex(WikiExtractionError, "CDN"):
                extract_wiki_material(
                    "https://2025.igem.wiki/test-team/education",
                    crawl_related=False,
                    fetcher=lambda url: (url, shell),
                )

    @patch("modules.wiki_extractor.socket.getaddrinfo", return_value=PUBLIC_DNS_RESULT)
    def test_missing_scheme_defaults_to_https(self, _: object) -> None:
        self.assertEqual(normalize_public_url("2025.igem.wiki/test-team/education"),
                         "https://2025.igem.wiki/test-team/education")


if __name__ == "__main__":
    unittest.main()
