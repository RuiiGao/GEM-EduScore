from __future__ import annotations

import unittest

from modules.benchmark_catalog import (
    DEFAULT_BENCHMARK_IDS,
    analyze_benchmark_portfolio,
    build_benchmark_reference,
    load_benchmark_catalog,
)
from modules.comparison import compare_projects, format_comparison_markdown
from modules.report_schema import EvaluationPayload, prepare_dashboard
from tests.test_llm_client import make_payload


class BenchmarkCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dashboard = prepare_dashboard(EvaluationPayload.model_validate(make_payload()), "en")

    def test_catalog_contains_multiple_verified_winners(self) -> None:
        cases = load_benchmark_catalog()
        winners = [case for case in cases if case["official_winner"]]
        self.assertGreaterEqual(len(winners), 5)
        self.assertTrue(all(case["wiki_url"].startswith("https://") for case in cases))

    def test_reference_contains_selected_cases_and_provenance_boundary(self) -> None:
        reference = build_benchmark_reference(DEFAULT_BENCHMARK_IDS[:2], "en")
        self.assertIn("Japan-United", reference)
        self.assertIn("Korea_HS", reference)
        self.assertIn("not official iGEM scores", reference)

    def test_portfolio_analysis_builds_ten_dimension_average(self) -> None:
        analysis = analyze_benchmark_portfolio(self.dashboard, DEFAULT_BENCHMARK_IDS, "en")
        self.assertEqual(len(analysis["rows"]), 10)
        self.assertEqual(len(analysis["cases"]), 4)
        self.assertGreater(analysis["portfolio_score"], 0)

    def test_pairwise_comparison_is_deterministic(self) -> None:
        stronger = {**self.dashboard, "dimensions": [dict(item) for item in self.dashboard["dimensions"]]}
        stronger["dimensions"][0]["score"] = 6
        comparison = compare_projects(stronger, self.dashboard, "A", "B", "en")
        markdown = format_comparison_markdown(comparison, stronger, self.dashboard, "en")

        self.assertEqual(comparison["rows"][0]["delta"], 2)
        self.assertEqual(comparison["rows"][0]["lead"], "A")
        self.assertIn("Ten-dimension Comparison", markdown)


if __name__ == "__main__":
    unittest.main()
