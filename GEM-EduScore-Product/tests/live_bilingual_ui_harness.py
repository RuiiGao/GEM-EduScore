"""Streamlit test harness for the bilingual result and three downloads."""

from __future__ import annotations

import streamlit as st

import app
from modules.llm_client import LLMResult
from modules.report_schema import format_markdown_report, localize_payload, prepare_dashboard
from tests.test_localization import make_bilingual_payload


payload = make_bilingual_payload()
dashboards = {}
reports = {}
for language in ("zh", "en", "bilingual"):
    localized = localize_payload(payload, language)
    dashboards[language] = prepare_dashboard(localized, language)
    reports[language] = format_markdown_report(localized, dashboards[language], language)

st.session_state["llm_result"] = LLMResult(
    report_markdown=reports["bilingual"],
    dashboard=dashboards["bilingual"],
    model="test-model",
    endpoint="chat_completions",
    response_id="chat_bilingual_ui",
    input_tokens=1000,
    output_tokens=800,
    duration_seconds=2.5,
    output_language="bilingual",
    localized_dashboards=dashboards,
    localized_reports=reports,
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

