from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping

from physical_ai_data.candidates import export_candidates
from physical_ai_data.package_io import read_csv_rows, read_json, write_csv_rows, write_json
from physical_ai_data.schema import CANDIDATE_COLUMNS, ValidationMessage
from physical_ai_data.validation import MANIFEST_FILENAME, validate_package

TRAINING_EVAL_EXPORT_FORMAT = "physical-ai-training-eval-draft/v0.2"
TRAINING_EVAL_SAMPLES_SCHEMA_VERSION = "physical-ai-training-eval-samples/v0.2"
TRAINING_EVAL_ALLOWED_SPLITS = [
    "unspecified",
    "train",
    "eval",
    "validation",
    "test",
    "holdout",
]
TRAINING_EVAL_SAMPLE_COLUMNS = [
    "sample_id",
    "split",
    "package_id",
    "frame_id",
    "timestamp_s",
    "candidate_id",
    "candidate_source_type",
    "candidate_source_id",
    "object_id",
    "score",
    "reasons",
    "label_status",
    "label_ref",
    "primary_artifact_ref",
    "package_root",
]


def export_training_eval_draft(
    package_root: str | Path,
    output_dir: str | Path | None = None,
    *,
    split: str = "unspecified",
) -> Path:
    _validate_split(split)

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
    manifest_tables = package_manifest.get("tables", {})
    frames = (
        read_csv_rows(root / str(manifest_tables["frames"]))
        if isinstance(manifest_tables, Mapping)
        else []
    )
    frames_by_id = {row.get("frame_id", ""): row for row in frames}
    package_id = str(package_manifest.get("package_id", ""))
    output = Path(output_dir) if output_dir is not None else root / "derived" / "training_eval"
    samples = [
        _sample_row(index, split, candidate, root, package_id, frames_by_id)
        for index, candidate in enumerate(candidates)
    ]

    write_csv_rows(output / "samples.csv", TRAINING_EVAL_SAMPLE_COLUMNS, samples)
    write_json(
        output / "training_eval_manifest.json",
        _manifest(package_manifest, root, split, len(samples)),
    )
    return output


def _sample_row(
    index: int,
    split: str,
    candidate: Mapping[str, str],
    root: Path,
    package_id: str,
    frames_by_id: Mapping[str, Mapping[str, str]],
) -> dict[str, str]:
    frame = frames_by_id.get(candidate.get("frame_id", ""), {})
    return {
        "sample_id": f"sample_{index:04d}",
        "split": split,
        "package_id": package_id,
        "frame_id": candidate.get("frame_id", ""),
        "timestamp_s": candidate.get("timestamp_s", ""),
        "candidate_id": candidate.get("candidate_id", ""),
        "candidate_source_type": candidate.get("source_type", ""),
        "candidate_source_id": candidate.get("source_id", ""),
        "object_id": candidate.get("object_id", ""),
        "score": candidate.get("score", ""),
        "reasons": candidate.get("reasons", ""),
        "label_status": "unlabeled",
        "label_ref": "",
        "primary_artifact_ref": _primary_artifact_ref(frame),
        "package_root": str(root),
    }


def _manifest(
    package_manifest: Mapping[str, object],
    root: Path,
    split: str,
    candidate_count: int,
) -> dict[str, object]:
    return {
        "export_format": TRAINING_EVAL_EXPORT_FORMAT,
        "contract_status": "draft",
        "formal_format": False,
        "allowed_splits": TRAINING_EVAL_ALLOWED_SPLITS,
        "samples_schema_version": TRAINING_EVAL_SAMPLES_SCHEMA_VERSION,
        "source_package_id": package_manifest.get("package_id", ""),
        "source_package_root": str(root),
        "schema_version": package_manifest.get("schema_version", ""),
        "scenario_type": package_manifest.get("scenario_type", ""),
        "split": split,
        "samples_csv": "samples.csv",
        "sample_count": candidate_count,
        "candidate_count": candidate_count,
        "notes": "This draft export is not a formal training framework format.",
        "created_at": datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
    }


def _validate_split(split: str) -> None:
    if split not in TRAINING_EVAL_ALLOWED_SPLITS:
        raise ValueError(
            f"split must be one of: {', '.join(TRAINING_EVAL_ALLOWED_SPLITS)}"
        )


def _primary_artifact_ref(frame: Mapping[str, str]) -> str:
    for field in ("image_ref", "point_cloud_ref", "trajectory_ref"):
        value = frame.get(field, "")
        if value:
            return value
    return ""


def _validate_candidate_columns(candidates_csv: Path) -> None:
    with candidates_csv.open(newline="", encoding="utf-8") as file:
        columns = csv.DictReader(file).fieldnames or []
    missing = [column for column in CANDIDATE_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"Candidate CSV missing required columns: {', '.join(missing)}")


def _format_validation_errors(errors: list[ValidationMessage]) -> str:
    return "; ".join(f"{error.code}: {error.message}" for error in errors)
