from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.schema import ValidationMessage, ValidationResult
from physical_ai_data.sdk import (
    convert_to_rerun,
    export_candidates_csv,
    export_training_eval_draft,
    summarize,
    validate,
)
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter

__all__ = ["PipelineResult", "run_weld_workcell_pipeline"]


@dataclass(frozen=True)
class PipelineResult:
    package_root: Path
    validation: ValidationResult
    summary: dict[str, object]
    candidates_csv: Path | None
    training_draft_dir: Path | None
    rrd_path: Path | None


def run_weld_workcell_pipeline(
    clean_root: str | Path,
    output_dir: str | Path,
    *,
    copy_images: bool = True,
    export_candidates: bool = True,
    candidate_min_score: float = 0.5,
    training_split: str | None = "unspecified",
    output_rrd: str | Path | None = None,
) -> PipelineResult:
    try:
        import_result = run_import(
            WeldWorkcellPackageImporter(),
            ImportRequest(
                source_format="weld_workcell",
                source={"root": Path(clean_root)},
                output_dir=Path(output_dir),
                options={"copy_images": copy_images},
            ),
        )
    except Exception as exc:
        raise ValueError(f"weld_workcell pipeline failed during import: {exc}") from exc

    package_root = import_result.package_root
    validation = validate(package_root)
    if not validation.ok:
        error_details = _format_validation_errors(validation.errors)
        raise ValueError(f"weld_workcell pipeline produced invalid package: {error_details}")

    summary = summarize(package_root)
    candidates_csv = (
        export_candidates_csv(package_root, min_score=candidate_min_score)
        if export_candidates
        else None
    )
    # Training draft export may create derived/candidates.csv internally for sample rows;
    # only report candidates_csv when this pipeline step explicitly requested it.
    training_draft_dir = (
        export_training_eval_draft(package_root, split=training_split)
        if training_split is not None
        else None
    )
    rrd_path = convert_to_rerun(package_root, output_rrd) if output_rrd is not None else None

    return PipelineResult(
        package_root=package_root,
        validation=validation,
        summary=summary,
        candidates_csv=candidates_csv,
        training_draft_dir=training_draft_dir,
        rrd_path=rrd_path,
    )


def _format_validation_errors(errors: list[ValidationMessage]) -> str:
    if not errors:
        return "unknown validation error"
    return "; ".join(f"{error.code}: {error.message}" for error in errors)
