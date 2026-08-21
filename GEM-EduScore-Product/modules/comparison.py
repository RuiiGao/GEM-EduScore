"""Deterministic comparison of two independently evaluated education projects."""

from __future__ import annotations

from typing import Any

from .localization import OutputLanguage, localized_text


def compare_projects(
    dashboard_a: dict[str, Any],
    dashboard_b: dict[str, Any],
    label_a: str,
    label_b: str,
    language: OutputLanguage = "zh",
) -> dict[str, Any]:
    t = lambda zh, en: localized_text(zh, en, language)
    by_id_a = {item["id"]: item for item in dashboard_a["dimensions"]}
    by_id_b = {item["id"]: item for item in dashboard_b["dimensions"]}
    rows = []
    advantages_a = []
    advantages_b = []
    shared_gaps = []
    for dimension_id in by_id_a:
        item_a = by_id_a[dimension_id]
        item_b = by_id_b[dimension_id]
        delta = int(item_a["score"]) - int(item_b["score"])
        if delta > 0:
            lead = label_a
            advantages_a.append(dimension_id)
        elif delta < 0:
            lead = label_b
            advantages_b.append(dimension_id)
        else:
            lead = t("持平", "Tie")
        if int(item_a["score"]) <= 3 and int(item_b["score"]) <= 3:
            shared_gaps.append(dimension_id)
        rows.append(
            {
                "id": dimension_id,
                "name_a": item_a["name"],
                "name_b": item_b["name"],
                "score_a": int(item_a["score"]),
                "score_b": int(item_b["score"]),
                "delta": delta,
                "evidence_a": item_a["evidence_strength"],
                "evidence_b": item_b["evidence_strength"],
                "lead": lead,
                "improvement_a": item_a["improvement"],
                "improvement_b": item_b["improvement"],
            }
        )

    design_delta = round(float(dashboard_a["design_score"]) - float(dashboard_b["design_score"]), 1)
    evidence_delta = round(float(dashboard_a["evidence_coverage"]) - float(dashboard_b["evidence_coverage"]), 1)
    recommendations = []
    for row in sorted(rows, key=lambda value: abs(value["delta"]), reverse=True):
        if row["delta"] >= 2:
            recommendations.append(
                t(
                    f"{label_b} 可重点借鉴 {label_a} 在 {row['id']}（{row['name_a']}）上的证据与设计方式。",
                    f"{label_b} can learn from {label_a}'s evidence and design in {row['id']} ({row['name_a']}).",
                )
            )
        elif row["delta"] <= -2:
            recommendations.append(
                t(
                    f"{label_a} 可重点借鉴 {label_b} 在 {row['id']}（{row['name_b']}）上的证据与设计方式。",
                    f"{label_a} can learn from {label_b}'s evidence and design in {row['id']} ({row['name_b']}).",
                )
            )
    if shared_gaps:
        recommendations.append(
            t(
                f"双方共同薄弱维度为 {', '.join(shared_gaps)}，适合共同建设评价工具、反馈流程或可复用资源。",
                f"Shared weak dimensions are {', '.join(shared_gaps)}; both projects could co-develop assessment tools, feedback loops, or reusable resources.",
            )
        )
    if not recommendations:
        recommendations.append(t("双方画像接近，建议重点核对证据强度与长期影响记录。", "The profiles are close; compare evidence strength and long-term impact records next."))

    return {
        "label_a": label_a,
        "label_b": label_b,
        "rows": rows,
        "design_delta": design_delta,
        "evidence_delta": evidence_delta,
        "advantages_a": advantages_a,
        "advantages_b": advantages_b,
        "shared_gaps": shared_gaps,
        "recommendations": recommendations[:6],
    }


def format_comparison_markdown(
    comparison: dict[str, Any],
    dashboard_a: dict[str, Any],
    dashboard_b: dict[str, Any],
    language: OutputLanguage = "zh",
) -> str:
    t = lambda zh, en: localized_text(zh, en, language)
    lines = [
        f"# GEM-EduScore · {comparison['label_a']} vs {comparison['label_b']}",
        "",
        f"> {t('本报告为诊断性对比，不构成 iGEM 官方排名。', 'This is a diagnostic comparison, not an official iGEM ranking.')}",
        "",
        f"## {t('总体对比', 'Overall Comparison')}",
        "",
        f"- {comparison['label_a']}: {dashboard_a['design_score']:.1f}/100 · {t('证据覆盖率', 'Evidence coverage')} {dashboard_a['evidence_coverage']:.1f}%",
        f"- {comparison['label_b']}: {dashboard_b['design_score']:.1f}/100 · {t('证据覆盖率', 'Evidence coverage')} {dashboard_b['evidence_coverage']:.1f}%",
        "",
        f"## {t('十维对照', 'Ten-dimension Comparison')}",
        "",
        f"| {t('维度', 'Dimension')} | {comparison['label_a']} | {comparison['label_b']} | Δ A-B | {t('领先', 'Lead')} |",
        "|---|---:|---:|---:|---|",
    ]
    for row in comparison["rows"]:
        lines.append(f"| {row['id']} {row['name_a']} | {row['score_a']}/6 | {row['score_b']}/6 | {row['delta']:+d} | {row['lead']} |")
    lines.extend(["", f"## {t('互相借鉴建议', 'Cross-learning Recommendations')}", ""])
    lines.extend(f"- {item}" for item in comparison["recommendations"])
    return "\n".join(lines)
