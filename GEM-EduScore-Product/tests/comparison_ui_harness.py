"""Streamlit harness for the complete two-project comparison workspace."""

from __future__ import annotations

from copy import deepcopy

import streamlit as st

import app
from modules import DEFAULT_BENCHMARK_IDS
from modules.llm_client import LLMResult
from modules.report_schema import EvaluationPayload, format_markdown_report, prepare_dashboard
from tests.test_llm_client import make_payload


payload_a_data = make_payload()
payload_a_data["practice_name"] = "Alpha Education Portfolio"
payload_a_data["team"] = "Team Alpha"
payload_a = EvaluationPayload.model_validate(payload_a_data)

payload_b_data = deepcopy(payload_a_data)
payload_b_data["practice_name"] = "Beta Education Wiki"
payload_b_data["team"] = "Team Beta"
payload_b_data["summary"] = "A second education practice with stronger outcome assessment and accessibility evidence."
payload_b_data["dimensions"][0]["score"] = 2
payload_b_data["dimensions"][3]["score"] = 5
payload_b_data["dimensions"][7]["score"] = 5
payload_b = EvaluationPayload.model_validate(payload_b_data)

dashboard_a = prepare_dashboard(payload_a, "en")
dashboard_b = prepare_dashboard(payload_b, "en")


def result(payload: EvaluationPayload, dashboard: dict, response_id: str) -> LLMResult:
    return LLMResult(
        report_markdown=format_markdown_report(payload, dashboard, "en"),
        dashboard=dashboard,
        model="test-model",
        endpoint="responses",
        response_id=response_id,
        input_tokens=1000,
        output_tokens=600,
        duration_seconds=2.0,
        output_language="en",
    )


st.session_state["comparison_results"] = {
    "result_a": result(payload_a, dashboard_a, "comparison_a"),
    "result_b": result(payload_b, dashboard_b, "comparison_b"),
    "info_a": {"name": "alpha.md", "characters": 1000},
    "info_b": {"name": "https://2025.igem.wiki/beta/education", "characters": 2000},
    "label_a": "Team Alpha",
    "label_b": "Team Beta",
    "language": "en",
    "benchmark_ids": list(DEFAULT_BENCHMARK_IDS),
}

app.inject_styles()
app.render_project_comparison()
