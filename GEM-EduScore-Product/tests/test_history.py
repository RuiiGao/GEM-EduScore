from __future__ import annotations

import unittest
from unittest.mock import patch

import app


class HistoryStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state: dict = {}
        self.session_patch = patch.object(app.st, "session_state", self.state)
        self.session_patch.start()

    def tearDown(self) -> None:
        self.session_patch.stop()

    def test_add_history_record_is_newest_first_and_limited(self) -> None:
        for index in range(app.HISTORY_LIMIT + 3):
            app.add_history_record("single", f"Report {index}", "source", {"index": index})

        history = self.state["evaluation_history"]
        self.assertEqual(len(history), app.HISTORY_LIMIT)
        self.assertEqual(history[0]["title"], f"Report {app.HISTORY_LIMIT + 2}")
        self.assertEqual(history[-1]["title"], "Report 3")

    def test_reset_preserves_history_and_managed_count(self) -> None:
        history = [{"id": "one", "title": "Saved"}]
        self.state.update(
            {
                "evaluation_history": history,
                "managed_analysis_count": 2,
                "evaluation_ready": True,
                "llm_result": object(),
            }
        )

        app.reset_evaluation_session()

        self.assertEqual(self.state["evaluation_history"], history)
        self.assertEqual(self.state["managed_analysis_count"], 2)
        self.assertNotIn("evaluation_ready", self.state)
        self.assertTrue(self.state["evaluation_reset_notice"])

    def test_restore_comparison_switches_workspace(self) -> None:
        comparison = {"label_a": "A", "label_b": "B"}
        record = {
            "type": "comparison",
            "title": "A vs B",
            "payload": {"comparison_results": comparison},
        }

        app.restore_history_record(record)

        self.assertEqual(self.state["analysis_workspace"], "双项目对比分析")
        self.assertEqual(self.state["comparison_results"], comparison)
        self.assertEqual(self.state["result_mode"], "comparison")
        self.assertTrue(self.state["evaluation_ready"])

    def test_restore_single_rehydrates_report_state(self) -> None:
        result = object()
        record = {
            "type": "single",
            "title": "Saved report",
            "payload": {
                "llm_result": result,
                "document_info": {"name": "source.pdf"},
                "benchmark_ids": ["case-a"],
                "report_language": "zh",
                "demo_mode": False,
            },
        }

        app.restore_history_record(record)

        self.assertEqual(self.state["analysis_workspace"], "单项目深度评估")
        self.assertIs(self.state["llm_result"], result)
        self.assertEqual(self.state["document_info"]["name"], "source.pdf")
        self.assertEqual(self.state["result_mode"], "live")
        self.assertTrue(self.state["evaluation_ready"])


if __name__ == "__main__":
    unittest.main()
