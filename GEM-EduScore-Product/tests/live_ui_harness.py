"""Streamlit test harness for a complete structured live result."""

from __future__ import annotations

import streamlit as st

import app
from modules.llm_client import LLMResult
from modules.report_schema import EvaluationPayload, format_markdown_report, prepare_dashboard
from tests.test_llm_client import make_payload


payload = EvaluationPayload.model_validate(make_payload())
dashboard = prepare_dashboard(payload, "en")
st.session_state["llm_result"] = LLMResult(
    report_markdown=format_markdown_report(payload, dashboard, "en"),
    dashboard=dashboard,
    model="test-model",
    endpoint="responses",
    response_id="resp_ui_test",
    input_tokens=1000,
    output_tokens=500,
    duration_seconds=2.5,
    output_language="en",
)
st.session_state["document_info"] = {
    "name": "test_education.md",
    "extension": "MD",
    "characters": 1200,
    "lines": 80,
    "preview": "Test Education Portfolio",
}

app.inject_styles()
app.render_live_report()
