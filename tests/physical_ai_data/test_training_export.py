from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest

from physical_ai_data.samples import generate_welding_package
from physical_ai_data.training_export import (
    TRAINING_EVAL_EXPORT_FORMAT,
    TRAINING_EVAL_SAMPLE_COLUMNS,
    export_training_eval_draft,
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def test_export_training_eval_draft_creates_default_manifest_and_samples(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=3)

    output = export_training_eval_draft(package)

    assert output == package / "derived" / "training_eval"
    manifest = json.loads((output / "training_eval_manifest.json").read_text(encoding="utf-8"))
    rows = _rows(output / "samples.csv")

    assert manifest["export_format"] == TRAINING_EVAL_EXPORT_FORMAT
    assert manifest["source_package_id"] == "sample_robot_welding_station_seed_3_frames_12"
    assert manifest["source_package_root"] == str(package)
    assert manifest["schema_version"] == "physical-ai-package/v0.1"
    assert manifest["scenario_type"] == "robot_welding_station"
    assert manifest["split"] == "unspecified"
    assert manifest["samples_csv"] == "samples.csv"
    assert manifest["candidate_count"] == len(rows)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", manifest["created_at"])

    assert rows
    assert list(rows[0].keys()) == TRAINING_EVAL_SAMPLE_COLUMNS
    assert rows[0]["sample_id"] == "sample_0000"
    assert rows[0]["split"] == "unspecified"
    assert rows[0]["candidate_id"]
    assert rows[0]["source_type"]
    assert rows[0]["score"]
    assert rows[0]["label_status"] == "unlabeled"
    assert rows[0]["package_root"] == str(package)


def test_export_training_eval_draft_generates_default_candidates_when_missing(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=4)
    candidates_csv = package / "derived" / "candidates.csv"
    assert not candidates_csv.exists()

    export_training_eval_draft(package)

    assert candidates_csv.exists()


def test_export_training_eval_draft_uses_custom_output_dir(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=5)
    output_dir = tmp_path / "exports" / "training_eval"

    output = export_training_eval_draft(package, output_dir=output_dir)

    assert output == output_dir
    assert (output_dir / "samples.csv").exists()
    assert (output_dir / "training_eval_manifest.json").exists()


def test_export_training_eval_draft_preserves_split_verbatim(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=6)

    output = export_training_eval_draft(package, split="holdout")

    manifest = json.loads((output / "training_eval_manifest.json").read_text(encoding="utf-8"))
    rows = _rows(output / "samples.csv")
    assert manifest["split"] == "holdout"
    assert {row["split"] for row in rows} == {"holdout"}


def test_export_training_eval_draft_rejects_invalid_package_with_validator_code(tmp_path: Path):
    with pytest.raises(ValueError, match="missing_manifest"):
        export_training_eval_draft(tmp_path)
