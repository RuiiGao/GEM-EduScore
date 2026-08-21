"""Static benchmark comparison data for the first UI prototype."""

from __future__ import annotations

from typing import Any


def get_benchmark_comparison() -> dict[str, Any]:
    return {
        "benchmark_name": "HK-United 2024 Education Portfolio",
        "benchmark_features": [
            "面向不同年龄与学习条件的受众适配",
            "游戏、图书、视频和数字资源组成的多模态设计",
            "主动参与和动手实践",
            "问卷、反馈与参与数据支持的效果评价",
            "可复用教学资源与长期可访问内容",
        ],
        "shared_strengths": [
            "均覆盖不同受众并重视科学传播",
            "均采用多样活动形式增强参与感",
            "均具备将合成生物学转化为学习体验的基础",
        ],
        "gaps": [
            {
                "dimension": "D4 · 效果评价",
                "current": "主要记录活动实施、参与情况与作品",
                "benchmark": "收集问卷、反馈和参与数据",
                "opportunity": "建立前测—过程观察—后测的标准评价流程",
                "priority": "高",
            },
            {
                "dimension": "D5 · 反馈迭代",
                "current": "存在反思，但修改与再验证记录有限",
                "benchmark": "形成反馈、分析与改进流程",
                "opportunity": "记录反馈如何改变下一轮活动，并比较前后效果",
                "priority": "高",
            },
            {
                "dimension": "D6 · 文档复用",
                "current": "活动资料丰富，但尚未形成标准教学包",
                "benchmark": "沉淀游戏、手册、协议和数字资源",
                "opportunity": "发布教案、材料清单、实施指南和评价模板",
                "priority": "中",
            },
            {
                "dimension": "D9 · 持续发展",
                "current": "提出长期愿景，实施和跟踪证据不足",
                "benchmark": "强调资源复用与长期可访问性",
                "opportunity": "建立长期学校合作和年度教育项目",
                "priority": "中",
            },
        ],
        "disclaimer": "基准比较用于识别可借鉴的实践模式，不构成团队排名或官方评价。",
    }
