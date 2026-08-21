"""Deterministic rubric calculations for the API-free prototype."""

from __future__ import annotations

from typing import Any


EVIDENCE_VALUES = {"E0": 0.0, "E1": 0.33, "E2": 0.67, "E3": 1.0}


DIMENSIONS: list[dict[str, Any]] = [
    {
        "id": "D1",
        "name": "目标与受众匹配",
        "short_name": "目标受众",
        "score": 4,
        "weight": 8,
        "evidence": "E2",
        "strength": "目标、受众与儿童友好的活动形式之间存在清晰对应。",
        "gap": "缺少系统受众调研及其影响课程设计的记录。",
    },
    {
        "id": "D2",
        "name": "教学设计质量",
        "short_name": "教学设计",
        "score": 5,
        "weight": 12,
        "evidence": "E2",
        "strength": "知识输入、互动、实践与创造任务构成完整学习链。",
        "gap": "尚无根据课堂反馈动态调整学习路径的证据。",
    },
    {
        "id": "D3",
        "name": "双向学习与互动",
        "short_name": "学习互动",
        "score": 4,
        "weight": 14,
        "evidence": "E2",
        "strength": "包含问答、游戏、小组讨论和参与者设计任务。",
        "gap": "参与者尚未被证明参与共同设计或持续合作。",
    },
    {
        "id": "D4",
        "name": "教育效果评价与证据",
        "short_name": "效果评价",
        "score": 1,
        "weight": 14,
        "evidence": "E0",
        "strength": "材料能够证明活动发生并记录了部分参与者产出。",
        "gap": "缺少前后测、系统问卷及与目标对应的学习变化数据。",
    },
    {
        "id": "D5",
        "name": "反馈与迭代",
        "short_name": "反馈迭代",
        "score": 1,
        "weight": 12,
        "evidence": "E0",
        "strength": "现有材料中存在活动反思意识。",
        "gap": "没有反馈收集、分析、修改和再次验证的完整闭环。",
    },
    {
        "id": "D6",
        "name": "文档化与可复用性",
        "short_name": "文档复用",
        "score": 2,
        "weight": 12,
        "evidence": "E1",
        "strength": "活动过程和部分展示材料得到记录。",
        "gap": "缺少标准教案、活动协议、复现指南和本地化建议。",
    },
    {
        "id": "D7",
        "name": "参与者赋能与 SynBio 参与",
        "short_name": "参与赋能",
        "score": 4,
        "weight": 10,
        "evidence": "E2",
        "strength": "参与者从知识接触推进到模型制作和方案设计。",
        "gap": "缺少后续自主实践、长期项目或社区贡献证据。",
    },
    {
        "id": "D8",
        "name": "公平性与可及性",
        "short_name": "可及包容",
        "score": 3,
        "weight": 8,
        "evidence": "E1",
        "strength": "游戏与模型体现了面向儿童的基本年龄适配。",
        "gap": "未系统记录语言、地域、经济和特殊需求适配。",
    },
    {
        "id": "D9",
        "name": "持续性与长期影响",
        "short_name": "长期影响",
        "score": 1,
        "weight": 5,
        "evidence": "E0",
        "strength": "提出了终身学习框架的长期愿景。",
        "gap": "缺少周期活动、持续资源、稳定合作和跟踪记录。",
    },
    {
        "id": "D10",
        "name": "伦理与责任意识",
        "short_name": "伦理责任",
        "score": 1,
        "weight": 5,
        "evidence": "E0",
        "strength": "当前材料不足以确认明确优势。",
        "gap": "未发现生物伦理、技术风险或社会影响讨论证据。",
    },
]


def evaluate_demo_case() -> dict[str, Any]:
    """Calculate the documented demo result from fixed rubric inputs."""
    dimensions: list[dict[str, Any]] = []
    design_score = 0.0
    evidence_coverage = 0.0

    for item in DIMENSIONS:
        dimension = dict(item)
        normalized = (dimension["score"] - 1) / 5
        contribution = normalized * dimension["weight"]
        evidence_contribution = EVIDENCE_VALUES[dimension["evidence"]] * dimension["weight"]
        dimension["normalized_score"] = round(normalized * 100, 1)
        dimension["contribution"] = round(contribution, 1)
        dimension["evidence_contribution"] = round(evidence_contribution, 1)
        dimensions.append(dimension)
        design_score += contribution
        evidence_coverage += evidence_contribution

    return {
        "design_score": round(design_score, 1),
        "evidence_coverage": round(evidence_coverage, 1),
        "confidence": "有限",
        "headline": "教学设计具备良好基础，当前主要瓶颈是教育效果证据与反馈闭环。",
        "dimensions": dimensions,
        "strongest": ["D2 教学设计质量", "D1 目标与受众匹配", "D3 双向学习与互动"],
        "priorities": ["D4 效果评价", "D5 反馈迭代", "D6 文档复用"],
    }
