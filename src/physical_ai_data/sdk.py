from __future__ import annotations

from pathlib import Path

from physical_ai_data.candidates import export_candidates, summarize_package
from physical_ai_data.rerun_adapter import write_rrd
from physical_ai_data.schema import ValidationResult
from physical_ai_data.stage11_readiness import (
    GapStatus,
    H300ReadinessReport,
    ReadinessCheck,
    assess_h300_sample_readiness,
)
from physical_ai_data.training_export import export_training_eval_draft as _export_training_eval_draft
from physical_ai_data.validation import validate_package

__all__ = [
    "validate",
    "summarize",
    "export_candidates_csv",
    "convert_to_rerun",
    "export_training_eval_draft",
    "GapStatus",
    "H300ReadinessReport",
    "ReadinessCheck",
    "assess_h300_sample_readiness",
]


def validate(package_root: str | Path) -> ValidationResult:
    return validate_package(package_root)


def summarize(package_root: str | Path) -> dict[str, object]:
    return summarize_package(package_root)


def export_candidates_csv(
    package_root: str | Path,
    output_csv: str | Path | None = None,
    *,
    min_score: float = 0.5,
) -> Path:
    return export_candidates(package_root, output_csv=output_csv, min_score=min_score)


def convert_to_rerun(package_root: str | Path, output_rrd: str | Path) -> Path:
    return write_rrd(package_root, output_rrd)


def export_training_eval_draft(
    package_root: str | Path,
    output_dir: str | Path | None = None,
    *,
    split: str = "unspecified",
) -> Path:
    return _export_training_eval_draft(package_root, output_dir=output_dir, split=split)
