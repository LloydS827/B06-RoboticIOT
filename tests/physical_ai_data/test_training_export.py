from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest

from physical_ai_data.samples import generate_welding_package
from physical_ai_data.schema import CANDIDATE_COLUMNS
from physical_ai_data.training_export import export_training_eval_draft


EXPECTED_ALLOWED_SPLITS = [
    "unspecified",
    "train",
    "eval",
    "validation",
    "test",
    "holdout",
]
EXPECTED_SAMPLE_COLUMNS = [
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


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_export_training_eval_draft_creates_default_manifest_and_samples(
    tmp_path: Path,
):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=3)

    output = export_training_eval_draft(package)

    assert output == package / "derived" / "training_eval"
    manifest = json.loads(
        (output / "training_eval_manifest.json").read_text(encoding="utf-8")
    )
    rows = _rows(output / "samples.csv")

    assert manifest["export_format"] == "physical-ai-training-eval-draft/v0.2"
    assert manifest["contract_status"] == "draft"
    assert manifest["formal_format"] is False
    assert manifest["allowed_splits"] == EXPECTED_ALLOWED_SPLITS
    assert (
        manifest["samples_schema_version"]
        == "physical-ai-training-eval-samples/v0.2"
    )
    assert manifest["source_package_id"] == "sample_robot_welding_station_seed_3_frames_12"
    assert manifest["source_package_root"] == str(package)
    assert manifest["schema_version"] == "physical-ai-package/v0.1"
    assert manifest["scenario_type"] == "robot_welding_station"
    assert manifest["split"] == "unspecified"
    assert manifest["samples_csv"] == "samples.csv"
    assert manifest["sample_count"] == len(rows)
    assert manifest["candidate_count"] == len(rows)
    assert "not a formal training framework format" in manifest["notes"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", manifest["created_at"])

    assert rows
    assert list(rows[0].keys()) == EXPECTED_SAMPLE_COLUMNS
    assert rows[0]["sample_id"] == "sample_0000"
    assert rows[0]["split"] == "unspecified"
    assert rows[0]["package_id"] == "sample_robot_welding_station_seed_3_frames_12"
    assert rows[0]["candidate_id"]
    assert rows[0]["candidate_source_type"]
    assert rows[0]["candidate_source_id"]
    assert rows[0]["score"]
    assert rows[0]["label_status"] == "unlabeled"
    assert rows[0]["label_ref"] == ""
    assert rows[0]["primary_artifact_ref"]
    assert rows[0]["package_root"] == str(package)


def test_export_training_eval_draft_generates_default_candidates_when_missing(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=4)
    candidates_csv = package / "derived" / "candidates.csv"
    assert not candidates_csv.exists()

    export_training_eval_draft(package)

    assert candidates_csv.exists()


def test_export_training_eval_draft_reuses_existing_valid_candidates(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=8)
    _write_rows(
        package / "derived" / "candidates.csv",
        CANDIDATE_COLUMNS,
        [
            {
                "candidate_id": "candidate_manual",
                "source_type": "event",
                "source_id": "event_manual",
                "frame_id": "frame_0000",
                "object_id": "",
                "timestamp_s": "0.0",
                "reasons": "precomputed",
                "score": "0.42",
            }
        ],
    )

    output = export_training_eval_draft(package)

    rows = _rows(output / "samples.csv")
    assert len(rows) == 1
    assert rows[0]["candidate_id"] == "candidate_manual"
    assert rows[0]["candidate_source_type"] == "event"
    assert rows[0]["candidate_source_id"] == "event_manual"
    assert rows[0]["object_id"] == ""
    assert rows[0]["reasons"] == "precomputed"
    assert rows[0]["score"] == "0.42"
    assert rows[0]["label_status"] == "unlabeled"
    assert rows[0]["label_ref"] == ""
    assert rows[0]["primary_artifact_ref"] == "artifacts/images/frame_0000.png"


def test_export_training_eval_draft_rejects_existing_candidates_missing_required_columns(
    tmp_path: Path,
):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=9)
    columns = [column for column in CANDIDATE_COLUMNS if column not in {"score", "source_type"}]
    _write_rows(
        package / "derived" / "candidates.csv",
        columns,
        [
            {
                "candidate_id": "candidate_old",
                "source_id": "event_old",
                "frame_id": "frame_0000",
                "object_id": "",
                "timestamp_s": "0.0",
                "reasons": "old format",
            }
        ],
    )

    with pytest.raises(ValueError) as exc_info:
        export_training_eval_draft(package)
    assert "score" in str(exc_info.value)
    assert "source_type" in str(exc_info.value)


def test_export_training_eval_draft_uses_custom_output_dir(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=5)
    output_dir = tmp_path / "exports" / "training_eval"

    output = export_training_eval_draft(package, output_dir=output_dir)

    assert output == output_dir
    assert (output_dir / "samples.csv").exists()
    assert (output_dir / "training_eval_manifest.json").exists()


@pytest.mark.parametrize("split", EXPECTED_ALLOWED_SPLITS)
def test_export_training_eval_draft_accepts_allowed_splits(tmp_path: Path, split: str):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=10)

    output = export_training_eval_draft(package, split=split)

    manifest = json.loads(
        (output / "training_eval_manifest.json").read_text(encoding="utf-8")
    )
    rows = _rows(output / "samples.csv")
    assert manifest["split"] == split
    assert {row["split"] for row in rows} == {split}


@pytest.mark.parametrize("split", ["", "Train", "dev", "train/eval"])
def test_export_training_eval_draft_rejects_invalid_split(tmp_path: Path, split: str):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=11)

    with pytest.raises(ValueError, match="split must be one of"):
        export_training_eval_draft(package, split=split)


def test_export_training_eval_draft_leaves_primary_artifact_empty_for_missing_candidate_frame(
    tmp_path: Path,
):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=6)
    _write_rows(
        package / "derived" / "candidates.csv",
        CANDIDATE_COLUMNS,
        [
            {
                "candidate_id": "candidate_missing_frame",
                "source_type": "event",
                "source_id": "event_missing_frame",
                "frame_id": "missing_frame",
                "object_id": "",
                "timestamp_s": "0.0",
                "reasons": "precomputed",
                "score": "0.42",
            }
        ],
    )

    output = export_training_eval_draft(package)

    rows = _rows(output / "samples.csv")
    assert rows[0]["primary_artifact_ref"] == ""


def test_export_training_eval_draft_uses_ordered_primary_artifact_fallback(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=13)
    frame_rows = _rows(package / "frames.csv")
    frame_rows[0]["image_ref"] = ""
    frame_rows[1]["image_ref"] = ""
    frame_rows[1]["point_cloud_ref"] = ""
    _write_rows(package / "frames.csv", list(frame_rows[0].keys()), frame_rows)
    _write_rows(
        package / "derived" / "candidates.csv",
        CANDIDATE_COLUMNS,
        [
            {
                "candidate_id": "candidate_point_cloud",
                "source_type": "event",
                "source_id": "event_point_cloud",
                "frame_id": frame_rows[0]["frame_id"],
                "object_id": "",
                "timestamp_s": frame_rows[0]["timestamp_s"],
                "reasons": "precomputed",
                "score": "0.42",
            },
            {
                "candidate_id": "candidate_trajectory",
                "source_type": "event",
                "source_id": "event_trajectory",
                "frame_id": frame_rows[1]["frame_id"],
                "object_id": "",
                "timestamp_s": frame_rows[1]["timestamp_s"],
                "reasons": "precomputed",
                "score": "0.43",
            },
        ],
    )

    output = export_training_eval_draft(package)

    rows = _rows(output / "samples.csv")
    assert rows[0]["primary_artifact_ref"] == "artifacts/point_clouds/workpiece.csv"
    assert rows[1]["primary_artifact_ref"] == "artifacts/trajectories/tcp_path.csv"


def test_export_training_eval_draft_rejects_invalid_package_with_validator_code(tmp_path: Path):
    with pytest.raises(ValueError, match="missing_manifest"):
        export_training_eval_draft(tmp_path)
