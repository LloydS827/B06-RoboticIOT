from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import physical_ai_data
import physical_ai_data.sdk as sdk
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
    assert set(sdk.__all__) == {
        "validate",
        "summarize",
        "export_candidates_csv",
        "convert_to_rerun",
        "export_training_eval_draft",
    }


def test_public_sdk_imports_do_not_load_cli_lerobot_or_rerun():
    for module_name in list(sys.modules):
        if (
            module_name == "physical_ai_data"
            or module_name.startswith("physical_ai_data.")
            or module_name == "lerobot"
            or module_name.startswith("lerobot.")
            or module_name == "rerun"
            or module_name.startswith("rerun.")
        ):
            sys.modules.pop(module_name, None)

    imported_package = importlib.import_module("physical_ai_data")
    imported_sdk = importlib.import_module("physical_ai_data.sdk")
    importlib.reload(imported_sdk)
    importlib.reload(imported_package)

    loaded_modules = set(sys.modules)
    forbidden_modules = {
        "physical_ai_data.cli",
        "physical_ai_data.lerobot_adapter",
        "physical_ai_data.lerobot_loader",
        "physical_ai_data.lerobot_profiles",
    }
    forbidden_roots = ("lerobot", "rerun")

    assert forbidden_modules.isdisjoint(loaded_modules)
    assert not [
        module_name
        for module_name in loaded_modules
        if any(module_name == root or module_name.startswith(f"{root}.") for root in forbidden_roots)
    ]


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

