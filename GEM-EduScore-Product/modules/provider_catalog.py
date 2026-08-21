"""Curated API presets for hosted and local OpenAI-compatible model services."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPreset:
    id: str
    label: str
    base_url: str
    default_model: str
    description: str
    supports_responses: bool = False
    api_key_optional: bool = False


PROVIDER_PRESETS = (
    ProviderPreset(
        id="openai",
        label="OpenAI",
        base_url="https://api.openai.com/v1",
        default_model="gpt-5-mini",
        description="原生 Responses API 与 Chat Completions",
        supports_responses=True,
    ),
    ProviderPreset(
        id="siliconflow",
        label="SiliconFlow",
        base_url="https://api.siliconflow.cn/v1",
        default_model="Qwen/Qwen3-8B",
        description="适合国内访问，可调用 Qwen、DeepSeek 等模型",
    ),
    ProviderPreset(
        id="deepseek",
        label="DeepSeek",
        base_url="https://api.deepseek.com",
        default_model="deepseek-v4-flash",
        description="DeepSeek 官方 OpenAI-compatible 接口",
    ),
    ProviderPreset(
        id="dashscope",
        label="阿里云百炼 / DashScope",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-plus",
        description="通义千问 OpenAI-compatible 接口（北京地域）",
    ),
    ProviderPreset(
        id="openrouter",
        label="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        default_model="qwen/qwen3-30b-a3b-instruct-2507",
        description="一个 API 访问多个模型提供商",
    ),
    ProviderPreset(
        id="groq",
        label="Groq",
        base_url="https://api.groq.com/openai/v1",
        default_model="qwen/qwen3.6-27b",
        description="高速 OpenAI-compatible 推理服务",
    ),
    ProviderPreset(
        id="ollama",
        label="Ollama（本地）",
        base_url="http://localhost:11434/v1",
        default_model="qwen3:8b",
        description="在本机运行模型；API Key 可留空",
        api_key_optional=True,
    ),
    ProviderPreset(
        id="custom",
        label="自定义 OpenAI-compatible",
        base_url="https://your-provider.example/v1",
        default_model="model-name",
        description="适配任何提供 /chat/completions 的兼容服务",
    ),
)

PROVIDERS_BY_LABEL = {preset.label: preset for preset in PROVIDER_PRESETS}
PROVIDERS_BY_ID = {preset.id: preset for preset in PROVIDER_PRESETS}


def provider_for_base_url(base_url: str) -> ProviderPreset:
    """Best-effort match for environment-based configurations."""
    normalized = base_url.strip().rstrip("/").lower()
    aliases = {
        "https://api.siliconflow.cn": "siliconflow",
        "http://localhost:11434": "ollama",
    }
    if normalized in aliases:
        return PROVIDERS_BY_ID[aliases[normalized]]
    for preset in PROVIDER_PRESETS:
        if preset.id == "custom":
            continue
        if normalized == preset.base_url.rstrip("/").lower():
            return preset
    return PROVIDERS_BY_ID["custom"]
