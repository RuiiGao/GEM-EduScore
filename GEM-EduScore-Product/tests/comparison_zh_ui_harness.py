"""Chinese comparison harness that proves both sides use the same locale view."""

from __future__ import annotations

from copy import deepcopy

import streamlit as st

import app
from modules import DEFAULT_BENCHMARK_IDS
from modules.llm_client import LLMResult
from modules.report_schema import EvaluationPayload, format_markdown_report, prepare_dashboard
from tests.test_llm_client import make_chinese_payload, make_payload


english_a = EvaluationPayload.model_validate(make_payload())
english_b_data = deepcopy(make_payload())
english_b_data["practice_name"] = "Beta Education Wiki"
english_b_data["team"] = "Team Beta"
english_b_data["dimensions"][1]["improvement"] = "More evidence would strengthen the learning design quality."
english_b = EvaluationPayload.model_validate(english_b_data)

chinese_a = EvaluationPayload.model_validate(make_chinese_payload())
chinese_b_data = make_chinese_payload()
chinese_b_data["practice_name"] = "Beta Education Wiki"
chinese_b_data["team"] = "Team Beta"
chinese_b_data["dimensions"][1]["improvement"] = "补充教育目标如何指导活动设计的直接证据。"
chinese_b = EvaluationPayload.model_validate(chinese_b_data)


def result(english_payload: EvaluationPayload, chinese_payload: EvaluationPayload, response_id: str) -> LLMResult:
    english_dashboard = prepare_dashboard(english_payload, "en")
    chinese_dashboard = prepare_dashboard(chinese_payload, "zh")
    return LLMResult(
        report_markdown=format_markdown_report(english_payload, english_dashboard, "en"),
        dashboard=english_dashboard,
        model="test-model",
        endpoint="responses",
        response_id=response_id,
        input_tokens=1000,
        output_tokens=600,
        duration_seconds=2.0,
        output_language="zh",
        localized_dashboards={"zh": chinese_dashboard},
        localized_reports={"zh": format_markdown_report(chinese_payload, chinese_dashboard, "zh")},
    )


st.session_state["comparison_results"] = {
    "result_a": result(english_a, chinese_a, "comparison_zh_a"),
    "result_b": result(english_b, chinese_b, "comparison_zh_b"),
    "info_a": {"name": "alpha.md", "characters": 1000},
    "info_b": {"name": "beta.md", "characters": 2000},
    "label_a": "项目甲",
    "label_b": "项目乙",
    "language": "zh",
    "benchmark_ids": list(DEFAULT_BENCHMARK_IDS),
}

app.inject_styles()
app.render_project_comparison()
