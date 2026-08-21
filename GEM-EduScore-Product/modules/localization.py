"""Language policy and localized text helpers for GEM-EduScore."""

from __future__ import annotations

import re
from typing import Any, Literal


OutputLanguage = Literal["zh", "en", "bilingual"]
LANGUAGE_LABELS: dict[OutputLanguage, str] = {
    "zh": "中文",
    "en": "English",
    "bilingual": "中英双语 / Bilingual",
}

ZH_MARKER = "[[ZH]]"
EN_MARKER = "[[EN]]"


def language_prompt_instructions(language: OutputLanguage) -> str:
    """Return strict model-output language rules for the selected report mode."""
    common = (
        "LANGUAGE POLICY — REQUIRED\n"
        "Direct evidence quotations (source_quote and evidence_quotes), source URLs, IDs, "
        "enum values, team names and proper names must remain faithful to the source. "
        "Do not translate or paraphrase a direct quotation."
    )
    if language == "zh":
        return (
            f"{common}\nWrite every other human-readable generated field in natural Simplified Chinese. "
            "This includes the title, summary, dimension names, analysis, gaps and recommendations. "
            "Do not mix English headings or explanatory sentences into the Chinese report. "
            "Retain necessary English proper names, acronyms and official activity names from the source. "
            "When an English name or technical term may be unclear, give a concise Chinese explanation on first use, "
            "for example: Dive into STEM（STEM 探索活动）. English source quotations remain unchanged."
        )
    if language == "en":
        return (
            f"{common}\nWrite every other human-readable generated field in clear English. "
            "This includes the title, summary, dimension names, analysis, gaps and recommendations. "
            "Do not mix Chinese headings or explanatory sentences into the English report."
        )
    return (
        f"{common}\nFor every other human-readable generated string, provide a meaning-equivalent "
        f"Simplified Chinese and English pair in exactly this form: {ZH_MARKER}中文内容{EN_MARKER}English content. "
        "Use the markers once per string and never put them in quotation, URL, ID, enum, team-name, year, "
        "practice_name or benchmark_name fields. Both language versions must express the same evidence-based "
        "claim and must never use different scores or evidence levels."
    )


def localized_text(zh: str, en: str, language: OutputLanguage) -> str:
    if language == "zh":
        return zh
    if language == "en":
        return en
    return f"{zh} / {en}"


def select_language_variant(text: str, language: OutputLanguage) -> str:
    """Select one side of a bilingual model string, or render both cleanly."""
    value = str(text or "").strip()
    match = re.match(r"^\s*\[\[ZH\]\](.*?)\[\[EN\]\](.*?)\s*$", value, flags=re.DOTALL)
    if not match:
        return value
    zh_value, en_value = (part.strip() for part in match.groups())
    if language == "zh":
        return zh_value
    if language == "en":
        return en_value
    return f"{zh_value}\n\n{en_value}"


# Only these generated fields are localized. Direct quotations and source metadata
# are deliberately excluded so the evidence chain remains auditable.
LOCALIZABLE_KEYS = {
    "report_title",
    "evaluation_scope",
    "summary",
    "audiences",
    "goals",
    "activities",
    "statement",
    "missing_evidence",
    "name",
    "reason",
    "why_not_higher",
    "improvement",
    "strengths",
    "benchmark_features",
    "benchmark_similarities",
    "dimension",
    "current_practice",
    "benchmark_practice",
    "gap",
    "opportunity",
    "short_term",
    "medium_term",
    "long_term",
    "conclusion",
}
INLINE_BILINGUAL_KEYS = {"report_title", "name", "dimension"}
ANALYTIC_PROSE_KEYS = {
    "summary",
    "statement",
    "missing_evidence",
    "reason",
    "why_not_higher",
    "improvement",
    "strengths",
    "benchmark_features",
    "benchmark_similarities",
    "current_practice",
    "benchmark_practice",
    "gap",
    "opportunity",
    "short_term",
    "medium_term",
    "long_term",
    "conclusion",
}


def language_compliance_issues(data: Any, language: OutputLanguage) -> list[str]:
    """Return generated-field paths that do not follow the requested language policy."""
    issues: list[str] = []
    for path, value, key in _iter_localizable_strings(data):
        text = value.strip()
        if len(text) < 3:
            continue
        if language == "bilingual":
            if ZH_MARKER not in text or EN_MARKER not in text:
                issues.append(path)
            continue

        cjk_count = len(re.findall(r"[\u3400-\u9fff]", text))
        latin_count = len(re.findall(r"[A-Za-z]", text))
        language_letters = cjk_count + latin_count
        if language_letters == 0:
            continue
        if language == "zh":
            # English proper names are welcome inside Chinese prose. A generated
            # field with no meaningful Chinese context, however, needs repair.
            latin_words = re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*", text)
            looks_like_english_sentence = (
                key in ANALYTIC_PROSE_KEYS
                and len(latin_words) >= 5
                and cjk_count < 8
                and bool(re.search(r"[.!?。！？]", text))
            )
            if looks_like_english_sentence or (
                latin_count >= 10 and (cjk_count == 0 or cjk_count / language_letters < 0.18)
            ):
                issues.append(path)
        elif cjk_count >= 4 and cjk_count / language_letters > 0.18:
            issues.append(path)
    return issues


def _iter_localizable_strings(value: Any, *, key: str | None = None, path: str = ""):
    if isinstance(value, dict):
        for item_key, item in value.items():
            item_path = f"{path}.{item_key}" if path else item_key
            yield from _iter_localizable_strings(item, key=item_key, path=item_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"
            if isinstance(item, str) and key in LOCALIZABLE_KEYS:
                yield item_path, item, key
            else:
                yield from _iter_localizable_strings(item, path=item_path)
    elif isinstance(value, str) and key in LOCALIZABLE_KEYS:
        yield path, value, key


def localize_payload_data(value: Any, language: OutputLanguage, *, key: str | None = None) -> Any:
    """Recursively select localized generated fields while preserving evidence quotes."""
    if isinstance(value, dict):
        return {item_key: localize_payload_data(item, language, key=item_key) for item_key, item in value.items()}
    if isinstance(value, list):
        if key in LOCALIZABLE_KEYS:
            localized_items = []
            for item in value:
                if isinstance(item, str):
                    selected = select_language_variant(item, language)
                    localized_items.append(selected.replace("\n\n", " / ") if language == "bilingual" else selected)
                else:
                    localized_items.append(localize_payload_data(item, language))
            return localized_items
        return [localize_payload_data(item, language) for item in value]
    if isinstance(value, str) and key in LOCALIZABLE_KEYS:
        selected = select_language_variant(value, language)
        if language == "bilingual" and key in INLINE_BILINGUAL_KEYS:
            return selected.replace("\n\n", " / ")
        return selected
    return value
