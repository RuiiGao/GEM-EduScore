"""Language consistency tests for model payloads, dashboards and downloads."""

from __future__ import annotations

import unittest

from modules.localization import language_compliance_issues, select_language_variant
from modules.report_schema import (
    EvaluationPayload,
    format_markdown_report,
    localize_payload,
    prepare_dashboard,
)
from tests.test_llm_client import make_payload


def make_bilingual_payload() -> EvaluationPayload:
    data = make_payload()
    data["report_title"] = "[[ZH]]教育评价报告[[EN]]Education Evaluation Report"
    data["summary"] = "[[ZH]]这是中文摘要。[[EN]]This is the English summary."
    data["dimensions"][0]["name"] = "[[ZH]]目标与受众匹配[[EN]]Goal & Audience Alignment"
    data["dimensions"][0]["reason"] = "[[ZH]]评价理由。[[EN]]Evaluation reason."
    data["evidence_profile"]["strong_evidence"][0]["statement"] = (
        "[[ZH]]已实施工作坊。[[EN]]A workshop was implemented."
    )
    return EvaluationPayload.model_validate(data)


class LocalizationTests(unittest.TestCase):
    def test_language_marker_selection(self) -> None:
        value = "[[ZH]]中文内容[[EN]]English content"
        self.assertEqual(select_language_variant(value, "zh"), "中文内容")
        self.assertEqual(select_language_variant(value, "en"), "English content")
        self.assertEqual(select_language_variant(value, "bilingual"), "中文内容\n\nEnglish content")

    def test_localized_views_preserve_scores_and_direct_quotes(self) -> None:
        payload = make_bilingual_payload()
        chinese = localize_payload(payload, "zh")
        english = localize_payload(payload, "en")
        bilingual = localize_payload(payload, "bilingual")

        self.assertEqual(chinese.summary, "这是中文摘要。")
        self.assertEqual(english.summary, "This is the English summary.")
        self.assertIn("这是中文摘要。", bilingual.summary)
        self.assertIn("This is the English summary.", bilingual.summary)
        self.assertEqual(chinese.dimensions[0].score, english.dimensions[0].score)
        self.assertEqual(chinese.dimensions[0].evidence_quotes, ["Evidence excerpt"])
        self.assertEqual(
            chinese.evidence_profile.strong_evidence[0].source_quote,
            "We delivered the workshop.",
        )

    def test_report_templates_follow_selected_language(self) -> None:
        payload = make_bilingual_payload()
        chinese = localize_payload(payload, "zh")
        english = localize_payload(payload, "en")
        chinese_report = format_markdown_report(chinese, prepare_dashboard(chinese, "zh"), "zh")
        english_report = format_markdown_report(english, prepare_dashboard(english, "en"), "en")

        self.assertIn("## 总体评估", chinese_report)
        self.assertNotIn("## Overall Assessment", chinese_report)
        self.assertIn("## Overall Assessment", english_report)
        self.assertNotIn("## 总体评估", english_report)
        self.assertIn("We delivered the workshop.", chinese_report)

    def test_chinese_check_ignores_quotes_but_flags_english_analysis(self) -> None:
        data = make_payload()
        issues = language_compliance_issues(data, "zh")
        self.assertIn("dimensions[0].reason", issues)
        self.assertNotIn("dimensions[0].evidence_quotes[0]", issues)
        self.assertNotIn("evidence_profile.strong_evidence[0].source_quote", issues)

    def test_chinese_prose_can_retain_english_proper_names(self) -> None:
        data = make_payload()
        data["summary"] = "EPFL iGEM 团队通过 Dive into STEM（STEM 探索活动）开展了面向学生的实验教学。"
        self.assertNotIn("summary", language_compliance_issues(data, "zh"))

    def test_chinese_check_catches_english_sentence_after_short_chinese_prefix(self) -> None:
        data = make_payload()
        data["dimensions"][1]["improvement"] = (
            "建议：More evidence of how the activities are informed by education goals "
            "would substantiate the learning design quality."
        )
        self.assertIn("dimensions[1].improvement", language_compliance_issues(data, "zh"))

    def test_bilingual_check_requires_explicit_language_pairs(self) -> None:
        data = make_payload()
        issues = language_compliance_issues(data, "bilingual")
        self.assertIn("summary", issues)
        data["summary"] = "[[ZH]]中文摘要。[[EN]]English summary."
        self.assertNotIn("summary", language_compliance_issues(data, "bilingual"))


if __name__ == "__main__":
    unittest.main()
