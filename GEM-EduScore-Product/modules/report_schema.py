"""Structured evaluation contract and deterministic dashboard calculations."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from .localization import OutputLanguage, localize_payload_data, localized_text


DIMENSION_IDS = [f"D{i}" for i in range(1, 11)]
DIMENSION_WEIGHTS = {
    "D1": 8,
    "D2": 12,
    "D3": 14,
    "D4": 14,
    "D5": 12,
    "D6": 12,
    "D7": 10,
    "D8": 8,
    "D9": 5,
    "D10": 5,
}
EVIDENCE_VALUES = {"E0": 0.0, "E1": 0.33, "E2": 0.67, "E3": 1.0}
DIMENSION_NAMES = {
    "D1": "Goal & Audience Alignment",
    "D2": "Education Design Quality",
    "D3": "Learning Interaction",
    "D4": "Educational Outcome Assessment",
    "D5": "Feedback & Iteration",
    "D6": "Documentation & Reusability",
    "D7": "Participant Empowerment",
    "D8": "Accessibility & Inclusivity",
    "D9": "Sustainability",
    "D10": "Ethics & Responsibility",
}
DIMENSION_NAMES_ZH = {
    "D1": "目标与受众匹配",
    "D2": "教学设计质量",
    "D3": "双向学习与互动",
    "D4": "教育效果评价与证据",
    "D5": "反馈与迭代",
    "D6": "文档化与可复用性",
    "D7": "参与者赋能",
    "D8": "公平性与可及性",
    "D9": "持续性与长期影响",
    "D10": "伦理与责任意识",
}


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceItem(ContractModel):
    record_id: str
    statement: str
    source_quote: str
    status: Literal["Planned", "Implemented", "Observed Outcome", "Not Evidenced"]
    strength: Literal["E0", "E1", "E2", "E3"]
    source_url: str | None = None

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip()
        return value if value.startswith(("https://", "http://")) else None


class EvidenceProfile(ContractModel):
    strong_evidence: list[EvidenceItem]
    missing_evidence: list[str]


class DimensionEvaluation(ContractModel):
    id: Literal["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10"]
    name: str
    score: int
    evidence_strength: Literal["E0", "E1", "E2", "E3"]
    evidence_quotes: list[str]
    reason: str
    why_not_higher: str
    improvement: str


class BenchmarkGap(ContractModel):
    dimension: str
    current_practice: str
    benchmark_practice: str
    gap: str
    opportunity: str
    priority: Literal["High", "Medium", "Low"]


class ImprovementRoadmap(ContractModel):
    short_term: list[str]
    medium_term: list[str]
    long_term: list[str]


class EvaluationPayload(ContractModel):
    report_title: str
    practice_name: str
    team: str
    year: str
    evaluation_scope: str
    summary: str
    audiences: list[str]
    goals: list[str]
    activities: list[str]
    evidence_profile: EvidenceProfile
    dimensions: list[DimensionEvaluation]
    strengths: list[str]
    benchmark_name: str
    benchmark_features: list[str]
    benchmark_similarities: list[str]
    benchmark_gaps: list[BenchmarkGap]
    recommendations: ImprovementRoadmap
    conclusion: str

    @model_validator(mode="after")
    def validate_dimensions(self) -> "EvaluationPayload":
        ids = [item.id for item in self.dimensions]
        if sorted(ids, key=lambda value: int(value[1:])) != DIMENSION_IDS:
            raise ValueError("dimensions must contain D1 through D10 exactly once")
        for item in self.dimensions:
            if not 1 <= item.score <= 6:
                raise ValueError(f"{item.id} score must be between 1 and 6")
        return self


def localize_payload(payload: EvaluationPayload, language: OutputLanguage) -> EvaluationPayload:
    """Select a language view without altering scores, enums or source quotations."""
    return EvaluationPayload.model_validate(localize_payload_data(payload.model_dump(), language))


def prepare_dashboard(payload: EvaluationPayload, language: OutputLanguage = "zh") -> dict:
    """Add deterministic scores and chart fields to validated model output."""
    dimensions: list[dict] = []
    design_score = 0.0
    evidence_coverage = 0.0

    for item in sorted(payload.dimensions, key=lambda value: int(value.id[1:])):
        weight = DIMENSION_WEIGHTS[item.id]
        normalized = (item.score - 1) / 5
        contribution = normalized * weight
        evidence_contribution = EVIDENCE_VALUES[item.evidence_strength] * weight
        design_score += contribution
        evidence_coverage += evidence_contribution
        dimensions.append(
            {
                **item.model_dump(),
                "weight": weight,
                "normalized_score": round(normalized * 100, 1),
                "contribution": round(contribution, 1),
                "evidence_contribution": round(evidence_contribution, 1),
                "short_name": item.name[:12],
            }
        )

    strongest = max(dimensions, key=lambda value: (value["score"], value["evidence_contribution"]))
    weakest = min(dimensions, key=lambda value: (value["score"], -value["weight"]))
    if evidence_coverage >= 70:
        confidence = localized_text("较高", "High", language)
    elif evidence_coverage >= 40:
        confidence = localized_text("中等", "Moderate", language)
    else:
        confidence = localized_text("有限", "Limited", language)

    return {
        **payload.model_dump(),
        "dimensions": dimensions,
        "design_score": round(design_score, 1),
        "evidence_coverage": round(evidence_coverage, 1),
        "confidence": confidence,
        "strongest_dimension": strongest,
        "priority_dimension": weakest,
    }


def format_markdown_report(
    payload: EvaluationPayload,
    dashboard: dict,
    language: OutputLanguage = "en",
) -> str:
    """Build a consistent downloadable report from the structured result."""
    t = lambda zh, en: localized_text(zh, en, language)
    statuses = {
        "Planned": t("已规划", "Planned"),
        "Implemented": t("已实施", "Implemented"),
        "Observed Outcome": t("已观察到成果", "Observed Outcome"),
        "Not Evidenced": t("未发现证据", "Not Evidenced"),
    }
    priorities = {
        "High": t("高", "High"),
        "Medium": t("中", "Medium"),
        "Low": t("低", "Low"),
    }
    lines = [
        f"# {payload.report_title}",
        "",
        f"**{t('评价对象', 'Evaluation Object')}:** {payload.practice_name}",
        f"**{t('团队 / 年份', 'Team / Year')}:** {payload.team} / {payload.year}",
        f"**{t('评价范围', 'Evaluation Scope')}:** {payload.evaluation_scope}",
        "",
        f"> {t('本报告为 GEM-EduScore 诊断结果，不是 iGEM 官方评分或排名。', 'This is a GEM-EduScore diagnostic report, not an official iGEM score or ranking.')}",
        "",
        f"## {t('总体评估', 'Overall Assessment')}",
        "",
        f"- {t('教育设计得分', 'Education Design Score')}: **{dashboard['design_score']:.1f} / 100**",
        f"- {t('证据覆盖率', 'Evidence Coverage')}: **{dashboard['evidence_coverage']:.1f}%**",
        f"- {t('评价可信度', 'Evaluation Confidence')}: **{dashboard['confidence']}**",
        "",
        payload.summary,
        "",
        f"## 1. {t('教育实践概览', 'Education Practice Overview')}",
        "",
        f"### {t('目标受众', 'Target Audiences')}",
        *[f"- {item}" for item in payload.audiences],
        "",
        f"### {t('教育目标', 'Education Goals')}",
        *[f"- {item}" for item in payload.goals],
        "",
        f"### {t('主要活动 / 记录', 'Main Activities / Records')}",
        *[f"- {item}" for item in payload.activities],
        "",
        f"## 2. {t('证据概况', 'Evidence Profile')}",
        "",
        f"### {t('有力证据', 'Strong Evidence')}",
    ]
    for item in payload.evidence_profile.strong_evidence:
        lines.extend(
            [
                f"- **{item.record_id} · {item.strength} · {statuses[item.status]}:** {item.statement}",
                f"  - {t('证据原文', 'Evidence')}: “{item.source_quote}”",
            ]
        )
        if item.source_url:
            lines.append(f"  - {t('来源', 'Source')}: {item.source_url}")
    lines.extend(["", f"### {t('缺失证据', 'Missing Evidence')}", *[f"- {item}" for item in payload.evidence_profile.missing_evidence]])

    lines.extend(
        [
            "",
            f"## 3. {t('量规评价', 'Rubric Evaluation')}",
            "",
            f"| {t('维度', 'Dimension')} | {t('得分', 'Score')} | {t('权重', 'Weight')} | {t('证据', 'Evidence')} | {t('加权贡献', 'Contribution')} |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for item in dashboard["dimensions"]:
        lines.append(
            f"| {item['id']} {item['name']} | {item['score']} / 6 | {item['weight']}% | "
            f"{item['evidence_strength']} | {item['contribution']:.1f} |"
        )
    for item in payload.dimensions:
        lines.extend(
            [
                "",
                f"### {item.id} · {item.name} — {item.score}/6 ({item.evidence_strength})",
                "",
                f"**{t('评价理由', 'Reason')}:** {item.reason}",
                "",
                f"**{t('为何不能更高', 'Why not higher')}:** {item.why_not_higher}",
                "",
                f"**{t('改进建议', 'Improvement')}:** {item.improvement}",
            ]
        )

    lines.extend(["", f"## 4. {t('基准比较', 'Benchmark Comparison')}", "", f"**{t('比较基准', 'Benchmark')}:** {payload.benchmark_name}", ""])
    lines.extend(f"- {item}" for item in payload.benchmark_similarities)
    lines.extend(["", f"### {t('差距分析', 'Gap Analysis')}"])
    for gap in payload.benchmark_gaps:
        lines.extend(
            [
                "",
                f"- **{gap.dimension} · {priorities[gap.priority]} {t('优先级', 'priority')}:** {gap.gap}",
                f"  - {t('当前实践', 'Current')}: {gap.current_practice}",
                f"  - {t('基准实践', 'Benchmark')}: {gap.benchmark_practice}",
                f"  - {t('改进机会', 'Opportunity')}: {gap.opportunity}",
            ]
        )

    lines.extend(["", f"## 5. {t('改进路线', 'Improvement Roadmap')}", "", f"### {t('短期行动', 'Short-term Actions')}"])
    lines.extend(f"- {item}" for item in payload.recommendations.short_term)
    lines.extend(["", f"### {t('中期策略', 'Medium-term Strategies')}"])
    lines.extend(f"- {item}" for item in payload.recommendations.medium_term)
    lines.extend(["", f"### {t('长期发展', 'Long-term Development')}"])
    lines.extend(f"- {item}" for item in payload.recommendations.long_term)
    lines.extend(["", f"## {t('结论', 'Conclusion')}", "", payload.conclusion, ""])
    return "\n".join(lines)


def output_adapter_instructions() -> str:
    return """
PRODUCT OUTPUT ADAPTER — REQUIRED

The Master Prompt defines the analysis workflow and report meaning. For the
product UI, transport that complete evaluation as the provided structured
EvaluationPayload schema instead of free-form Markdown. Populate every field.

Rules:
- Return exactly ten dimension objects, D1 through D10, each scored 1–6 using the supplied Rubric.
- Use only direct source excerpts in evidence_quotes and source_quote.
- Missing information must be described as Not Evidenced; never invent evidence.
- Do not calculate an overall score or evidence coverage. The application calculates both deterministically.
- Benchmark comparison identifies patterns and gaps, never team ranking.
- Keep each list focused: normally 3–7 high-value items.
""".strip()


def compatibility_schema_instructions() -> str:
    """Return a compact schema guide suitable for OpenAI-compatible chat models."""
    return """
CHAT COMPATIBILITY OUTPUT SHAPE — RETURN ONE JSON OBJECT ONLY

Use exactly these top-level keys. Do not wrap the object in Markdown fences:
{
  "report_title": "string",
  "practice_name": "string",
  "team": "string",
  "year": "string",
  "evaluation_scope": "string",
  "summary": "string",
  "audiences": ["string"],
  "goals": ["string"],
  "activities": ["string"],
  "evidence_profile": {
    "strong_evidence": [{
      "record_id": "R01", "statement": "string", "source_quote": "direct quote",
      "status": "Planned|Implemented|Observed Outcome|Not Evidenced",
      "strength": "E0|E1|E2|E3", "source_url": "exact Wiki URL or null"
    }],
    "missing_evidence": ["string"]
  },
  "dimensions": [{
    "id": "D1 through D10", "name": "string", "score": 1,
    "evidence_strength": "E0|E1|E2|E3", "evidence_quotes": ["direct quote"],
    "reason": "string", "why_not_higher": "string", "improvement": "string"
  }],
  "strengths": ["string"],
  "benchmark_name": "string",
  "benchmark_features": ["string"],
  "benchmark_similarities": ["string"],
  "benchmark_gaps": [{
    "dimension": "D1-D10 or dimension name", "current_practice": "string",
    "benchmark_practice": "string", "gap": "string", "opportunity": "string",
    "priority": "High|Medium|Low"
  }],
  "recommendations": {
    "short_term": ["string"], "medium_term": ["string"], "long_term": ["string"]
  },
  "conclusion": "string"
}

The dimensions array must contain D1, D2, D3, D4, D5, D6, D7, D8, D9 and D10 exactly once.
If a field is not supported by the material, use an empty list or an explicit Not Evidenced statement.
""".strip()


def normalize_compatibility_payload(data: Any, language: OutputLanguage = "en") -> dict:
    """Conservatively adapt partial compatible-chat JSON to the strict product contract.

    The adapter never invents supporting evidence: missing rubric fields become E0 / score 1
    and are labelled as not evidenced. This lets smaller compatible models remain usable while
    keeping dashboard calculations deterministic and transparent.
    """
    if not isinstance(data, dict):
        raise ValueError("chat response must be a JSON object")

    def fallback(zh: str, en: str) -> str:
        if language == "bilingual":
            return f"[[ZH]]{zh}[[EN]]{en}"
        return localized_text(zh, en, language)

    dimension_names = {
        dimension_id: fallback(DIMENSION_NAMES_ZH[dimension_id], DIMENSION_NAMES[dimension_id])
        for dimension_id in DIMENSION_IDS
    }

    for wrapper_key in ("evaluation_report", "report", "result", "data"):
        wrapped = data.get(wrapper_key)
        if isinstance(wrapped, dict) and not any(key in data for key in ("dimensions", "report_title")):
            data = wrapped
            break

    raw_dimensions = data.get("dimensions", data.get("rubric_evaluation", data.get("scores", [])))
    dimensions_by_id: dict[str, dict] = {}
    if isinstance(raw_dimensions, dict):
        for key, value in raw_dimensions.items():
            item = value if isinstance(value, dict) else {"score": value}
            item = {**item, "id": item.get("id", key)}
            dimension_id = _dimension_id(item.get("id"))
            if dimension_id:
                dimensions_by_id[dimension_id] = item
    elif isinstance(raw_dimensions, list):
        for index, value in enumerate(raw_dimensions, 1):
            item = value if isinstance(value, dict) else {"score": value}
            dimension_id = _dimension_id(item.get("id", item.get("dimension", f"D{index}")))
            if dimension_id:
                dimensions_by_id[dimension_id] = item

    dimensions = []
    for dimension_id in DIMENSION_IDS:
        item = dimensions_by_id.get(dimension_id, {})
        evidence_strength = _evidence_strength(
            item.get("evidence_strength", item.get("evidence", item.get("strength")))
        )
        dimensions.append(
            {
                "id": dimension_id,
                "name": _text(item.get("name", item.get("dimension_name")), dimension_names[dimension_id]),
                "score": _score(item.get("score", item.get("rating"))),
                "evidence_strength": evidence_strength,
                "evidence_quotes": _string_list(
                    item.get("evidence_quotes", item.get("quotes", item.get("source_quote", [])))
                ),
                "reason": _text(
                    item.get("reason", item.get("analysis")),
                    fallback("模型的结构化输出中未发现证据。", "Not Evidenced in the structured model output."),
                ),
                "why_not_higher": _text(
                    item.get("why_not_higher", item.get("gap")),
                    fallback("返回结构未提供足以支持更高评分的证据。", "The returned structure did not provide sufficient evidence for a higher score."),
                ),
                "improvement": _text(
                    item.get("improvement", item.get("recommendation")),
                    fallback("记录活动、学习成果及其直接支持证据。", "Document the activity, learning outcome and direct supporting evidence."),
                ),
            }
        )

    raw_profile = data.get("evidence_profile", {})
    if not isinstance(raw_profile, dict):
        raw_profile = {}
    strong_evidence = []
    raw_strong = raw_profile.get("strong_evidence", data.get("strong_evidence", []))
    if isinstance(raw_strong, list):
        for index, value in enumerate(raw_strong, 1):
            if not isinstance(value, dict):
                continue
            strong_evidence.append(
                {
                    "record_id": _text(value.get("record_id", value.get("id")), f"R{index:02d}"),
                    "statement": _text(value.get("statement", value.get("title")), fallback("已记录的证据条目", "Documented evidence item")),
                    "source_quote": _text(value.get("source_quote", value.get("quote")), "Not Evidenced"),
                    "status": _status(value.get("status")),
                    "strength": _evidence_strength(value.get("strength", value.get("evidence_strength"))),
                    "source_url": _source_url(value.get("source_url", value.get("url"))),
                }
            )

    raw_recommendations = data.get("recommendations", data.get("improvement_roadmap", {}))
    if not isinstance(raw_recommendations, dict):
        raw_recommendations = {"short_term": _string_list(raw_recommendations)}

    raw_gaps = data.get("benchmark_gaps", [])
    benchmark_gaps = []
    if isinstance(raw_gaps, list):
        for value in raw_gaps:
            if not isinstance(value, dict):
                continue
            benchmark_gaps.append(
                {
                    "dimension": _text(value.get("dimension"), fallback("跨维度", "Cross-dimension")),
                    "current_practice": _text(value.get("current_practice", value.get("current")), fallback("未发现证据", "Not Evidenced")),
                    "benchmark_practice": _text(value.get("benchmark_practice", value.get("benchmark")), fallback("未发现证据", "Not Evidenced")),
                    "gap": _text(value.get("gap"), fallback("证据差距需要进一步复核。", "Evidence gap requires further review.")),
                    "opportunity": _text(value.get("opportunity"), fallback("收集可比较的成果证据。", "Collect comparable outcome evidence.")),
                    "priority": _priority(value.get("priority")),
                }
            )

    return {
        "report_title": _text(data.get("report_title", data.get("title")), fallback("GEM-EduScore 教育评价报告", "GEM-EduScore Education Evaluation Report")),
        "practice_name": _text(data.get("practice_name", data.get("project_name")), "Uploaded Education Practice"),
        "team": _text(data.get("team", data.get("team_name")), "Not Evidenced"),
        "year": _text(data.get("year"), "Not Evidenced"),
        "evaluation_scope": _text(data.get("evaluation_scope", data.get("scope")), fallback("用户提交的教育材料", "Uploaded Education material")),
        "summary": _text(data.get("summary", data.get("overall_assessment")), fallback("模型返回了部分结构化评价。", "The model returned a partial structured assessment.")),
        "audiences": _string_list(data.get("audiences", data.get("target_audiences", []))),
        "goals": _string_list(data.get("goals", data.get("education_goals", []))),
        "activities": _string_list(data.get("activities", data.get("main_activities", []))),
        "evidence_profile": {
            "strong_evidence": strong_evidence,
            "missing_evidence": _string_list(
                raw_profile.get("missing_evidence", data.get("missing_evidence", [fallback("需要进一步提取证据。", "Further evidence extraction is required.")]))
            ),
        },
        "dimensions": dimensions,
        "strengths": _string_list(data.get("strengths", [])),
        "benchmark_name": _text(data.get("benchmark_name"), "HK-United 2024 Education Portfolio"),
        "benchmark_features": _string_list(data.get("benchmark_features", [])),
        "benchmark_similarities": _string_list(data.get("benchmark_similarities", data.get("similarities", []))),
        "benchmark_gaps": benchmark_gaps,
        "recommendations": {
            "short_term": _string_list(raw_recommendations.get("short_term", raw_recommendations.get("short_term_actions", []))),
            "medium_term": _string_list(raw_recommendations.get("medium_term", raw_recommendations.get("medium_term_actions", []))),
            "long_term": _string_list(raw_recommendations.get("long_term", raw_recommendations.get("long_term_actions", []))),
        },
        "conclusion": _text(data.get("conclusion"), fallback("优先完善证据收集与迭代改进。", "Prioritize evidence collection and iterative improvement.")),
    }


def _text(value: Any, default: str) -> str:
    text = str(value).strip() if value is not None else ""
    return text or default


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        pieces = [piece.strip(" -•\t") for piece in value.splitlines() if piece.strip(" -•\t")]
        return pieces or ([value.strip()] if value.strip() else [])
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if item is not None and str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _dimension_id(value: Any) -> str | None:
    match = re.search(r"D\s*(10|[1-9])", str(value or ""), flags=re.IGNORECASE)
    return f"D{match.group(1)}" if match else None


def _score(value: Any) -> int:
    match = re.search(r"-?\d+(?:\.\d+)?", str(value or ""))
    if not match:
        return 1
    return max(1, min(6, round(float(match.group(0)))))


def _evidence_strength(value: Any) -> str:
    match = re.search(r"E\s*([0-3])", str(value or ""), flags=re.IGNORECASE)
    return f"E{match.group(1)}" if match else "E0"


def _status(value: Any) -> str:
    text = str(value or "").strip().lower()
    mapping = {
        "planned": "Planned",
        "implemented": "Implemented",
        "observed outcome": "Observed Outcome",
        "not evidenced": "Not Evidenced",
    }
    return mapping.get(text, "Not Evidenced")


def _priority(value: Any) -> str:
    text = str(value or "").strip().lower()
    return {"high": "High", "medium": "Medium", "low": "Low"}.get(text, "Medium")


def _source_url(value: Any) -> str | None:
    text = str(value or "").strip()
    return text if text.startswith(("https://", "http://")) else None
