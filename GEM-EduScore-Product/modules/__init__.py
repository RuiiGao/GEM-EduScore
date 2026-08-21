"""Core modules for the GEM-EduScore prototype."""

from .benchmark import get_benchmark_comparison
from .benchmark_catalog import (
    analyze_benchmark_portfolio,
    benchmark_case_options,
    build_benchmark_reference,
    DEFAULT_BENCHMARK_IDS,
    get_benchmark_cases,
)
from .comparison import compare_projects, format_comparison_markdown
from .evaluator import evaluate_demo_case
from .extractor import extract_document_text, get_demo_evidence_profile
from .llm_client import (
    LLMConfig,
    LLMConfigurationError,
    LLMRequestError,
    LLMResult,
    generate_evaluation_report,
)
from .prompt_loader import PromptBundle, load_prompt_bundle
from .provider_catalog import PROVIDER_PRESETS, ProviderPreset, provider_for_base_url
from .report_exporter import (
    generate_comparison_docx,
    generate_comparison_pdf,
    generate_docx_report,
    generate_pdf_report,
)
from .report_schema import EvaluationPayload, format_markdown_report, prepare_dashboard
from .recommender import get_improvement_roadmap
from .wiki_extractor import extract_wiki_material, WikiExtractionError

__all__ = [
    "evaluate_demo_case",
    "analyze_benchmark_portfolio",
    "benchmark_case_options",
    "build_benchmark_reference",
    "compare_projects",
    "DEFAULT_BENCHMARK_IDS",
    "EvaluationPayload",
    "extract_document_text",
    "extract_wiki_material",
    "format_markdown_report",
    "format_comparison_markdown",
    "generate_evaluation_report",
    "generate_comparison_docx",
    "generate_comparison_pdf",
    "generate_docx_report",
    "generate_pdf_report",
    "get_benchmark_comparison",
    "get_benchmark_cases",
    "get_demo_evidence_profile",
    "get_improvement_roadmap",
    "LLMConfig",
    "LLMConfigurationError",
    "LLMRequestError",
    "LLMResult",
    "load_prompt_bundle",
    "PromptBundle",
    "PROVIDER_PRESETS",
    "ProviderPreset",
    "provider_for_base_url",
    "prepare_dashboard",
    "WikiExtractionError",
]
