from __future__ import annotations

import json
from pathlib import Path

import physical_ai_data
from physical_ai_data import (
    convert_to_rerun,
    export_candidates_csv,
    export_training_eval_draft,
    summarize,
    validate,
)
from physical_ai_data.samples import generate_pick_sort_package
from physical_ai_data.schema import ValidationResult


def test_top_level_exports_sdk_functions():
    assert callable(validate)
    assert callable(summarize)
    assert callable(export_candidates_csv)
    assert callable(convert_to_rerun)
    assert callable(export_training_eval_draft)
    assert physical_ai_data.__version__ == "0.1.0"
    assert set(physical_ai_data.__all__) == {
        "__version__",
        "validate",
        "summarize",
        "export_candidates_csv",
        "convert_to_rerun",
        "export_training_eval_draft",
    }


def test_sdk_wraps_stable_package_operations_for_pick_sort(tmp_path: Path):
    package = generate_pick_sort_package(tmp_path / "pick", frame_count=8, random_seed=12)

    validation = validate(package)
    summary = summarize(package)
    candidates_csv = export_candidates_csv(package)
    training_eval_dir = export_training_eval_draft(package, split="eval")
    rrd = convert_to_rerun(package, tmp_path / "pick.rrd")

    assert isinstance(validation, ValidationResult)
    assert validation.ok
    assert summary["frame_count"] == 8
    assert candidates_csv == package / "derived" / "candidates.csv"
    assert candidates_csv.exists()

    manifest_path = training_eval_dir / "training_eval_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["split"] == "eval"
    assert manifest_path.exists()

    assert rrd == tmp_path / "pick.rrd"
    assert rrd.exists()


def test_sdk_does_not_import_cli_or_lerobot_boundaries():
    sdk_source = (Path(__file__).parents[2] / "src" / "physical_ai_data" / "sdk.py").read_text(encoding="utf-8")

    assert "argparse" not in sdk_source
    assert "physical_ai_data.cli" not in sdk_source
    assert "lerobot" not in sdk_source.lower()
