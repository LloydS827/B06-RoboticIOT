from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping

from physical_ai_data.candidates import export_candidates
from physical_ai_data.package_io import read_csv_rows, read_json, write_csv_rows, write_json
from physical_ai_data.schema import CANDIDATE_COLUMNS, ValidationMessage
from physical_ai_data.validation import MANIFEST_FILENAME, validate_package

TRAINING_EVAL_EXPORT_FORMAT = "physical-ai-training-eval-draft/v0.1"
TRAINING_EVAL_SAMPLE_COLUMNS = [
    "sample_id",
    "split",
    "frame_id",
    "timestamp_s",
    "candidate_id",
    "source_type",
    "score",
    "label_status",
    "package_root",
]


def export_training_eval_draft(
    package_root: str | Path,
    output_dir: str | Path | None = None,
    *,
    split: str = "unspecified",
) -> Path:
    root = Path(package_root)
    validation = validate_package(root)
    if not validation.ok:
        raise ValueError(_format_validation_errors(validation.errors))

    package_manifest = read_json(root / MANIFEST_FILENAME)
    candidates_csv = root / "derived" / "candidates.csv"
    if not candidates_csv.exists():
        candidates_csv = export_candidates(root)

    _validate_candidate_columns(candidates_csv)
    candidates = read_csv_rows(candidates_csv)
    output = Path(output_dir) if output_dir is not None else root / "derived" / "training_eval"
    samples = [_sample_row(index, split, candidate, root) for index, candidate in enumerate(candidates)]

    write_csv_rows(output / "samples.csv", TRAINING_EVAL_SAMPLE_COLUMNS, samples)
    write_json(output / "training_eval_manifest.json", _manifest(package_manifest, root, split, len(samples)))
    return output


def _sample_row(index: int, split: str, candidate: Mapping[str, str], root: Path) -> dict[str, str]:
    return {
        "sample_id": f"sample_{index:04d}",
        "split": split,
        "frame_id": candidate.get("frame_id", ""),
        "timestamp_s": candidate.get("timestamp_s", ""),
        "candidate_id": candidate.get("candidate_id", ""),
        "source_type": candidate.get("source_type", ""),
        "score": candidate.get("score", ""),
        "label_status": "unlabeled",
        "package_root": str(root),
    }


def _manifest(package_manifest: Mapping[str, object], root: Path, split: str, candidate_count: int) -> dict[str, object]:
    return {
        "export_format": TRAINING_EVAL_EXPORT_FORMAT,
        "source_package_id": package_manifest.get("package_id", ""),
        "source_package_root": str(root),
        "schema_version": package_manifest.get("schema_version", ""),
        "scenario_type": package_manifest.get("scenario_type", ""),
        "split": split,
        "samples_csv": "samples.csv",
        "candidate_count": candidate_count,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def _validate_candidate_columns(candidates_csv: Path) -> None:
    with candidates_csv.open(newline="", encoding="utf-8") as file:
        columns = csv.DictReader(file).fieldnames or []
    missing = [column for column in CANDIDATE_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"Candidate CSV missing required columns: {', '.join(missing)}")


def _format_validation_errors(errors: list[ValidationMessage]) -> str:
    return "; ".join(f"{error.code}: {error.message}" for error in errors)
