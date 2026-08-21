"""Dependency-free contract tests for both supported API modes."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from modules.llm_client import LLMConfig, generate_evaluation_report
from modules.localization import LOCALIZABLE_KEYS
from modules.prompt_loader import PromptBundle
from modules.report_schema import EvaluationPayload


PROMPTS = PromptBundle(
    master_prompt="Master instructions",
    rubric_reference="Rubric reference",
    benchmark_reference="Benchmark reference",
)


def make_payload() -> dict:
    names = [
        "Goal & Audience Alignment",
        "Education Design Quality",
        "Learning Interaction",
        "Educational Outcome Assessment",
        "Feedback & Iteration",
        "Documentation & Reusability",
        "Participant Empowerment",
        "Accessibility & Inclusivity",
        "Sustainability",
        "Ethics & Responsibility",
    ]
    return {
        "report_title": "GEM-EduScore Education Evaluation Report",
        "practice_name": "Test Education Portfolio",
        "team": "Test Team",
        "year": "2026",
        "evaluation_scope": "Complete portfolio",
        "summary": "A test education practice with documented activities.",
        "audiences": ["Students"],
        "goals": ["Improve understanding"],
        "activities": ["Workshop"],
        "evidence_profile": {
            "strong_evidence": [
                {
                    "record_id": "R01",
                    "statement": "A workshop was implemented.",
                    "source_quote": "We delivered the workshop.",
                    "status": "Implemented",
                    "strength": "E2",
                    "source_url": "https://2025.igem.wiki/test-team/education",
                }
            ],
            "missing_evidence": ["No pre/post test was evidenced."],
        },
        "dimensions": [
            {
                "id": f"D{index}",
                "name": name,
                "score": 4 if index <= 3 else 2,
                "evidence_strength": "E2" if index <= 3 else "E1",
                "evidence_quotes": ["Evidence excerpt"] if index <= 3 else [],
                "reason": "The material supports this level.",
                "why_not_higher": "Stronger outcome evidence is missing.",
                "improvement": "Collect stronger evidence.",
            }
            for index, name in enumerate(names, 1)
        ],
        "strengths": ["Clear goals"],
        "benchmark_name": "HK-United 2024 Education Portfolio",
        "benchmark_features": ["Audience-adaptive design"],
        "benchmark_similarities": ["Both use interactive activities"],
        "benchmark_gaps": [
            {
                "dimension": "D4",
                "current_practice": "Activity records",
                "benchmark_practice": "Outcome surveys",
                "gap": "Outcome measurement is missing",
                "opportunity": "Add aligned pre/post tests",
                "priority": "High",
            }
        ],
        "recommendations": {
            "short_term": ["Add a questionnaire"],
            "medium_term": ["Build reusable materials"],
            "long_term": ["Establish long-term partnerships"],
        },
        "conclusion": "Prioritize evidence collection and iteration.",
    }


def make_chinese_payload() -> dict:
    def rewrite(value: object, key: str | None = None) -> object:
        if isinstance(value, dict):
            return {item_key: rewrite(item, item_key) for item_key, item in value.items()}
        if isinstance(value, list):
            if key in LOCALIZABLE_KEYS:
                return ["中文分析与说明：该字段已依据原始证据转换为中文表述，并保留必要专有名词。" if isinstance(item, str) else rewrite(item) for item in value]
            return [rewrite(item) for item in value]
        if isinstance(value, str) and key in LOCALIZABLE_KEYS:
            return "中文分析与说明：该字段已依据原始证据转换为中文表述，并保留必要专有名词。"
        return value

    return rewrite(make_payload())  # type: ignore[return-value]


class FakeResponsesClient:
    last_kwargs = None

    def __init__(self, **_: object) -> None:
        self.responses = self

    def parse(self, **kwargs: object) -> SimpleNamespace:
        type(self).last_kwargs = kwargs
        return SimpleNamespace(
            id="resp_test",
            output_text=json.dumps(make_payload()),
            output_parsed=EvaluationPayload.model_validate(make_payload()),
            usage=SimpleNamespace(input_tokens=120, output_tokens=80),
        )


class FakeChatClient:
    last_kwargs = None

    def __init__(self, **_: object) -> None:
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs: object) -> SimpleNamespace:
        type(self).last_kwargs = kwargs
        return SimpleNamespace(
            id="chat_test",
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(make_payload())), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50),
        )


class PartialQwenChatClient:
    last_kwargs = None

    def __init__(self, **_: object) -> None:
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs: object) -> SimpleNamespace:
        type(self).last_kwargs = kwargs
        partial_payload = {
            "title": "Partial Qwen Evaluation",
            "project_name": "Compatibility Test Portfolio",
            "summary": "The model returned useful analysis but omitted product fields.",
            "dimensions": [
                {
                    "id": "D1",
                    "name": "Goal alignment",
                    "score": "4/6",
                    "evidence": "E2",
                    "analysis": "The audience and goal are stated.",
                }
            ],
        }
        return SimpleNamespace(
            id="chat_partial",
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(partial_payload)), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=90, completion_tokens=40),
        )


class TruncatedQwenChatClient:
    def __init__(self, **_: object) -> None:
        self.chat = SimpleNamespace(completions=self)

    def create(self, **_: object) -> SimpleNamespace:
        truncated = (
            '{"report_title":"Truncated report","practice_name":"Qwen portfolio",'
            '"summary":"Useful partial result","dimensions":[{"id":"D1","score":5'
        )
        return SimpleNamespace(
            id="chat_truncated",
            choices=[SimpleNamespace(message=SimpleNamespace(content=truncated), finish_reason="length")],
            usage=SimpleNamespace(prompt_tokens=120, completion_tokens=8192),
        )


class RepairingChatClient:
    calls = 0

    def __init__(self, **_: object) -> None:
        self.chat = SimpleNamespace(completions=self)

    def create(self, **_: object) -> SimpleNamespace:
        type(self).calls += 1
        content = "I could not format the report as JSON."
        if type(self).calls >= 2:
            content = json.dumps({"title": "Repaired", "summary": "Recovered readable assessment."})
        return SimpleNamespace(
            id=f"repair_{type(self).calls}",
            choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=60, completion_tokens=30),
        )


class BadRequestError(Exception):
    pass


class JsonObjectOnlyClient:
    calls = 0
    last_kwargs = None

    def __init__(self, **_: object) -> None:
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs: object) -> SimpleNamespace:
        type(self).calls += 1
        type(self).last_kwargs = kwargs
        if kwargs.get("response_format", {}).get("type") == "json_schema":
            raise BadRequestError("json_schema is not supported")
        return SimpleNamespace(
            id="json_object_fallback",
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(make_payload())), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=80, completion_tokens=40),
        )


class LanguageRepairingClient:
    calls = 0

    def __init__(self, **_: object) -> None:
        self.chat = SimpleNamespace(completions=self)

    def create(self, **_: object) -> SimpleNamespace:
        type(self).calls += 1
        payload = make_payload() if type(self).calls == 1 else make_chinese_payload()
        return SimpleNamespace(
            id=f"language_{type(self).calls}",
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload, ensure_ascii=False)), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=80),
        )


class LLMClientTests(unittest.TestCase):
    def test_responses_api_contract(self) -> None:
        result = generate_evaluation_report(
            "Education material",
            LLMConfig(api_key="test", endpoint="responses"),
            PROMPTS,
            client_factory=FakeResponsesClient,
        )
        self.assertIn("Evaluation Report", result.report_markdown)
        self.assertEqual(len(result.dashboard["dimensions"]), 10)
        self.assertEqual(result.input_tokens, 120)
        self.assertFalse(FakeResponsesClient.last_kwargs["store"])
        self.assertIn("Master instructions", FakeResponsesClient.last_kwargs["instructions"])
        self.assertIs(FakeResponsesClient.last_kwargs["text_format"], EvaluationPayload)

    def test_chat_completions_contract(self) -> None:
        result = generate_evaluation_report(
            "Education material",
            LLMConfig(api_key="test", endpoint="chat_completions"),
            PROMPTS,
            client_factory=FakeChatClient,
        )
        self.assertIn("Test Education Portfolio", result.report_markdown)
        self.assertEqual(result.dashboard["benchmark_gaps"][0]["priority"], "High")
        self.assertIn("https://2025.igem.wiki/test-team/education", result.report_markdown)
        self.assertEqual(result.output_tokens, 50)
        self.assertEqual(FakeChatClient.last_kwargs["messages"][0]["role"], "system")
        self.assertEqual(FakeChatClient.last_kwargs["response_format"]["type"], "json_schema")
        self.assertEqual(FakeChatClient.last_kwargs["max_tokens"], 8192)
        self.assertIn("CHAT COMPATIBILITY OUTPUT SHAPE", FakeChatClient.last_kwargs["messages"][0]["content"])

    def test_partial_qwen_payload_is_conservatively_completed(self) -> None:
        result = generate_evaluation_report(
            "Education material",
            LLMConfig(
                api_key="test",
                endpoint="chat_completions",
                base_url="https://api.siliconflow.cn",
                model="Qwen/Qwen3-8B",
            ),
            PROMPTS,
            client_factory=PartialQwenChatClient,
        )
        self.assertTrue(result.compatibility_repaired)
        self.assertEqual(len(result.dashboard["dimensions"]), 10)
        self.assertEqual(result.dashboard["dimensions"][0]["score"], 4)
        self.assertEqual(result.dashboard["dimensions"][1]["score"], 1)
        self.assertEqual(result.dashboard["dimensions"][1]["evidence_strength"], "E0")
        self.assertEqual(PartialQwenChatClient.last_kwargs["extra_body"], {"enable_thinking": False})

    def test_truncated_json_is_partially_recovered(self) -> None:
        result = generate_evaluation_report(
            "Education material",
            LLMConfig(api_key="test", endpoint="chat_completions"),
            PROMPTS,
            client_factory=TruncatedQwenChatClient,
        )
        self.assertTrue(result.compatibility_repaired)
        self.assertEqual(result.dashboard["dimensions"][0]["score"], 5)
        self.assertEqual(result.finish_reason, "length")
        self.assertIn("长度上限", result.compatibility_note)

    def test_non_json_output_gets_second_pass_repair(self) -> None:
        RepairingChatClient.calls = 0
        result = generate_evaluation_report(
            "Education material",
            LLMConfig(api_key="test", endpoint="chat_completions"),
            PROMPTS,
            client_factory=RepairingChatClient,
        )
        self.assertEqual(RepairingChatClient.calls, 2)
        self.assertTrue(result.compatibility_repaired)
        self.assertIn("repair", result.output_method)
        self.assertEqual(len(result.dashboard["dimensions"]), 10)

    def test_provider_rejecting_json_schema_falls_back_to_json_object(self) -> None:
        JsonObjectOnlyClient.calls = 0
        result = generate_evaluation_report(
            "Education material",
            LLMConfig(api_key="test", endpoint="chat_completions"),
            PROMPTS,
            client_factory=JsonObjectOnlyClient,
        )
        self.assertEqual(JsonObjectOnlyClient.calls, 2)
        self.assertEqual(JsonObjectOnlyClient.last_kwargs["response_format"], {"type": "json_object"})
        self.assertEqual(result.output_method, "json_object")

    def test_siliconflow_base_url_is_normalized(self) -> None:
        config = LLMConfig(
            api_key="test",
            base_url="https://api.siliconflow.cn",
            endpoint="chat_completions",
        ).validated()
        self.assertEqual(config.base_url, "https://api.siliconflow.cn/v1")

    def test_bilingual_mode_builds_three_downloadable_views(self) -> None:
        bilingual_payload = make_payload()
        bilingual_payload["summary"] = "[[ZH]]中文摘要。[[EN]]English summary."

        class BilingualClient(FakeChatClient):
            def create(self, **kwargs: object) -> SimpleNamespace:
                type(self).last_kwargs = kwargs
                return SimpleNamespace(
                    id="chat_bilingual",
                    choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(bilingual_payload)), finish_reason="stop")],
                    usage=SimpleNamespace(prompt_tokens=100, completion_tokens=80),
                )

        result = generate_evaluation_report(
            "Education material",
            LLMConfig(api_key="test", endpoint="chat_completions", output_language="bilingual"),
            PROMPTS,
            client_factory=BilingualClient,
        )
        self.assertEqual(set(result.localized_reports), {"zh", "en", "bilingual"})
        self.assertEqual(result.localized_dashboards["zh"]["summary"], "中文摘要。")
        self.assertEqual(result.localized_dashboards["en"]["summary"], "English summary.")
        self.assertIn("[[ZH]]", BilingualClient.last_kwargs["messages"][0]["content"])

    def test_chinese_mode_repairs_generated_language_without_changing_quotes_or_scores(self) -> None:
        LanguageRepairingClient.calls = 0
        result = generate_evaluation_report(
            "Education material",
            LLMConfig(api_key="test", endpoint="chat_completions", output_language="zh"),
            PROMPTS,
            client_factory=LanguageRepairingClient,
        )
        self.assertEqual(LanguageRepairingClient.calls, 2)
        self.assertTrue(result.language_repaired)
        self.assertTrue(result.language_compliant)
        self.assertTrue(result.dashboard["dimensions"][0]["reason"].startswith("中文分析与说明"))
        self.assertEqual(result.dashboard["dimensions"][0]["score"], 4)
        self.assertEqual(result.dashboard["dimensions"][0]["evidence_quotes"], ["Evidence excerpt"])
        self.assertEqual(
            result.dashboard["evidence_profile"]["strong_evidence"][0]["source_quote"],
            "We delivered the workshop.",
        )

    def test_compatible_chat_accepts_compact_field_language_repairs(self) -> None:
        class CompactRepairClient:
            calls = 0

            def __init__(self, **_: object) -> None:
                self.chat = SimpleNamespace(completions=self)

            def create(self, **kwargs: object) -> SimpleNamespace:
                type(self).calls += 1
                if type(self).calls == 1:
                    content = json.dumps(make_payload(), ensure_ascii=False)
                else:
                    user_content = kwargs["messages"][1]["content"]
                    request = json.loads(user_content)
                    content = json.dumps(
                        {
                            "repairs": {
                                path: "已根据材料完成中文分析与改进建议。"
                                for path in request["fields_to_rewrite"]
                            }
                        },
                        ensure_ascii=False,
                    )
                return SimpleNamespace(
                    id=f"compact_language_{type(self).calls}",
                    choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason="stop")],
                    usage=SimpleNamespace(prompt_tokens=100, completion_tokens=80),
                )

        CompactRepairClient.calls = 0
        result = generate_evaluation_report(
            "Education material",
            LLMConfig(api_key="test", endpoint="chat_completions", output_language="zh"),
            PROMPTS,
            client_factory=CompactRepairClient,
        )
        self.assertEqual(CompactRepairClient.calls, 2)
        self.assertTrue(result.language_compliant)
        self.assertEqual(result.dashboard["dimensions"][1]["improvement"], "已根据材料完成中文分析与改进建议。")


if __name__ == "__main__":
    unittest.main()
