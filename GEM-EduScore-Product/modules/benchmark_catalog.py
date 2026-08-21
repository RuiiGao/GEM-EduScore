"""Curated, source-linked education award benchmark portfolio."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from .localization import OutputLanguage, localized_text
from .report_schema import DIMENSION_IDS, DIMENSION_NAMES, DIMENSION_NAMES_ZH, DIMENSION_WEIGHTS


CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "benchmark_cases" / "education_award_catalog.json"
DEFAULT_BENCHMARK_IDS = ["japan_united_2023", "korea_hs_2022", "cca_san_diego_2021", "tas_taipei_2020"]


@lru_cache(maxsize=1)
def load_benchmark_catalog() -> tuple[dict[str, Any], ...]:
    cases = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("教育基准库为空。")
    seen: set[str] = set()
    for case in cases:
        case_id = str(case.get("id", ""))
        if not case_id or case_id in seen:
            raise ValueError("教育基准库包含重复或缺失的案例 ID。")
        seen.add(case_id)
        profile = case.get("profile", {})
        if set(profile) != set(DIMENSION_IDS) or any(not 1 <= int(value) <= 6 for value in profile.values()):
            raise ValueError(f"基准案例 {case_id} 的十维画像无效。")
    return tuple(cases)


def benchmark_label(case: dict[str, Any], language: OutputLanguage = "zh") -> str:
    award = localized_text(case["award_zh"], case["award_en"], language)
    return f"{case['team']} {case['year']} · {award}"


def get_benchmark_cases(case_ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
    catalog = list(load_benchmark_catalog())
    if case_ids is None:
        return catalog
    requested = list(dict.fromkeys(case_ids))
    by_id = {case["id"]: case for case in catalog}
    return [by_id[case_id] for case_id in requested if case_id in by_id]


def build_benchmark_reference(case_ids: Iterable[str], language: OutputLanguage = "zh") -> str:
    """Build compact evidence context for the LLM without presenting profile scores as official judging data."""
    cases = get_benchmark_cases(case_ids)
    if not cases:
        cases = get_benchmark_cases(DEFAULT_BENCHMARK_IDS)
    blocks = [
        "GEM-EduScore multi-case education benchmark portfolio.",
        "Award facts and source URLs identify public precedents. Dimension profiles are product-side analytical aids, not official iGEM scores.",
        "Use the cases collectively: identify recurring excellence patterns and compare the current project without ranking teams.",
    ]
    for case in cases:
        if language == "zh":
            features = case["features_zh"]
            summary = case["summary_zh"]
        elif language == "bilingual":
            features = [f"[[ZH]]{zh}[[EN]]{en}" for zh, en in zip(case["features_zh"], case["features_en"])]
            summary = f"[[ZH]]{case['summary_zh']}[[EN]]{case['summary_en']}"
        else:
            features = case["features_en"]
            summary = case["summary_en"]
        blocks.extend(
            [
                "",
                f"CASE: {benchmark_label(case, language)}",
                f"DIVISION: {case['division']}",
                f"OFFICIAL_WINNER: {'yes' if case['official_winner'] else 'no; curated portfolio'}",
                f"SUMMARY: {summary}",
                "REUSABLE FEATURES:",
                *[f"- {feature}" for feature in features],
                f"PUBLIC EVIDENCE: {case['wiki_url']}",
                f"AWARD / PROVENANCE SOURCE: {case['award_source_url']}",
            ]
        )
    return "\n".join(blocks)


def analyze_benchmark_portfolio(
    dashboard: dict[str, Any],
    case_ids: Iterable[str],
    language: OutputLanguage = "zh",
) -> dict[str, Any]:
    cases = get_benchmark_cases(case_ids)
    if not cases:
        cases = get_benchmark_cases(DEFAULT_BENCHMARK_IDS)
    current_scores = {item["id"]: int(item["score"]) for item in dashboard["dimensions"]}
    average_profile = {
        dimension_id: round(mean(int(case["profile"][dimension_id]) for case in cases), 2)
        for dimension_id in DIMENSION_IDS
    }
    portfolio_score = sum(((average_profile[item] - 1) / 5) * DIMENSION_WEIGHTS[item] for item in DIMENSION_IDS)
    rows = []
    for dimension_id in DIMENSION_IDS:
        current = current_scores[dimension_id]
        reference = average_profile[dimension_id]
        rows.append(
            {
                "id": dimension_id,
                "name": DIMENSION_NAMES_ZH[dimension_id] if language == "zh" else DIMENSION_NAMES[dimension_id],
                "current": current,
                "benchmark_average": reference,
                "gap": round(current - reference, 2),
            }
        )
    matches = []
    for case in cases:
        distance = mean(abs(current_scores[item] - int(case["profile"][item])) for item in DIMENSION_IDS)
        matches.append({"case": case, "distance": round(distance, 2), "similarity": round(max(0, 100 - distance / 5 * 100), 1)})
    matches.sort(key=lambda item: item["distance"])
    gaps = sorted(rows, key=lambda item: item["gap"])
    return {
        "cases": cases,
        "average_profile": average_profile,
        "portfolio_score": round(portfolio_score, 1),
        "rows": rows,
        "largest_gaps": gaps[:3],
        "best_match": matches[0],
        "matches": matches,
    }


def benchmark_case_options(language: OutputLanguage = "zh") -> dict[str, str]:
    return {benchmark_label(case, language): case["id"] for case in load_benchmark_catalog()}
