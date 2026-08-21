"""Load the existing GEM-EduScore prompt and its evaluation references."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PRODUCT_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = PRODUCT_DIR.parent


@dataclass(frozen=True)
class PromptBundle:
    master_prompt: str
    rubric_reference: str
    benchmark_reference: str
    version: str = "GEM-EduScore Master Prompt V1.0"


def load_prompt_bundle() -> PromptBundle:
    """Read the source-of-truth framework documents without modifying them."""
    return PromptBundle(
        master_prompt=_read_required(PROJECT_DIR / "Framework" / "11_GEM_EduScore_Master_Prompt_v1.0.md"),
        rubric_reference=_read_required(PROJECT_DIR / "Framework" / "02_rubric_v0.1.md"),
        benchmark_reference=_read_required(PROJECT_DIR / "Benchmark" / "benchmark_feature_summary.md"),
    )


def _read_required(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"缺少分析所需的项目文件：{path.name}")
    return path.read_text(encoding="utf-8").strip()
