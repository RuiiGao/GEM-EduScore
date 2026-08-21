"""Curated improvement roadmap for the API-free prototype."""

from __future__ import annotations

from typing import Any


def get_improvement_roadmap() -> list[dict[str, Any]]:
    return [
        {
            "stage": "短期",
            "timeline": "1–3 个月",
            "theme": "先把影响记录下来",
            "accent": "#2DD4BF",
            "actions": [
                "为核心活动加入简短的前测与后测",
                "建立参与者问卷、教师观察和作品归档模板",
                "统一记录目标、受众、过程、反馈与结果",
            ],
            "impact": "优先改善 D4、D5 与 Evidence Coverage",
        },
        {
            "stage": "中期",
            "timeline": "3–12 个月",
            "theme": "把活动沉淀成可复用资产",
            "accent": "#818CF8",
            "actions": [
                "整理教案、课件、材料清单和实施协议",
                "建立反馈分析与活动迭代机制",
                "为不同年龄、资源和语言场景提供适配版本",
            ],
            "impact": "重点改善 D5、D6 与 D8",
        },
        {
            "stage": "长期",
            "timeline": "1 年以上",
            "theme": "形成可持续教育系统",
            "accent": "#F59E0B",
            "actions": [
                "发展稳定学校与社区合作伙伴",
                "建设教育资源库并跟踪参与者后续发展",
                "建立年度活动、跨届维护与持续评估机制",
            ],
            "impact": "重点改善 D7 与 D9，并增强长期影响",
        },
    ]
