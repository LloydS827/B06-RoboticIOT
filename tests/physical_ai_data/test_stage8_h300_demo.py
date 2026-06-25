from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from physical_ai_data.candidates import export_candidates
from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.rerun_adapter import write_rrd
from physical_ai_data.stage7_sim_window import generate_stage7_sim_weld_window
from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo
from physical_ai_data.training_export import export_training_eval_draft
from physical_ai_data.validation import validate_package
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter


def test_generate_stage8_h300_demo_writes_raw_artifacts_and_clean_fixture(tmp_path: Path):
    fixture_root = tmp_path / "stage8_demo"
    result = generate_stage8_h300_synthetic_demo(fixture_root)

    assert result.root == fixture_root
    assert result.raw_root == fixture_root / "raw"
    assert result.clean_root == fixture_root / "clean" / "weld_workcell"

    raw_files = [
        "manifest.raw.json",
        "files/h300_job_window_story.json",
        "files/pcl_seam_candidates.json",
        "files/model_outputs.json",
        "files/manual_corrections.json",
        "files/quality_result.json",
        "files/point_clouds/window_0000.pcd",
    ]
    for relative_path in raw_files:
        assert (result.raw_root / relative_path).is_file()

    manifest = json.loads((result.raw_root / "manifest.raw.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "stage8"
    assert manifest["data_origin"] == "synthetic"
    assert manifest["real_replacement_required"] is True
    assert "point_cloud" in manifest["source_artifact_only_fields"]
    assert "frames.csv" in manifest["importer_supported_fields"]
    assert (result.raw_root / ".stage8_h300_synthetic_demo_generated").is_file()
    assert (result.clean_root / ".stage8_h300_synthetic_demo_generated").is_file()

    expected_clean_files = {
        ".stage8_h300_synthetic_demo_generated",
        "job.json",
        "frames.csv",
        "process.csv",
        "events.csv",
        "review_labels.csv",
        "images/front_0000.png",
    }
    actual_clean_files = {
        entry.relative_to(result.clean_root).as_posix()
        for entry in result.clean_root.rglob("*")
        if entry.is_file()
    }
    assert actual_clean_files == expected_clean_files
    for relative_path in expected_clean_files:
        assert (result.clean_root / relative_path).is_file()
    frames = list(csv.DictReader((result.clean_root / "frames.csv").open(newline="", encoding="utf-8")))
    assert frames
    assert frames[0]["image_path"] == "images/front_0000.png"
    assert all(row["image_path"] == "" for row in frames[1:])


def test_generate_stage8_h300_demo_refuses_unknown_existing_raw_dir(tmp_path: Path):
    fixture_root = tmp_path / "stage8_demo"
    sentinel = fixture_root / "raw" / "keep.txt"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("real raw data\n", encoding="utf-8")

    with pytest.raises(ValueError, match="refusing to overwrite non-stage8 fixture directory"):
        generate_stage8_h300_synthetic_demo(fixture_root)

    assert sentinel.read_text(encoding="utf-8") == "real raw data\n"


def test_generate_stage8_h300_demo_refuses_unknown_files_added_to_generated_roots(tmp_path: Path):
    fixture_root = tmp_path / "stage8_demo"
    result = generate_stage8_h300_synthetic_demo(fixture_root)
    raw_sentinel = result.raw_root / "files" / "user_keep.txt"
    clean_sentinel = result.clean_root / "images" / "user_keep.png"
    raw_sentinel.write_text("user raw data\n", encoding="utf-8")
    clean_sentinel.write_bytes(b"user clean data\n")

    with pytest.raises(ValueError, match="refusing to overwrite non-stage8 fixture directory"):
        generate_stage8_h300_synthetic_demo(fixture_root)

    assert raw_sentinel.read_text(encoding="utf-8") == "user raw data\n"
    assert clean_sentinel.read_bytes() == b"user clean data\n"


def test_generate_stage8_h300_demo_can_overwrite_own_generated_roots(tmp_path: Path):
    fixture_root = tmp_path / "stage8_demo"
    generate_stage8_h300_synthetic_demo(fixture_root, frame_count=5)

    result = generate_stage8_h300_synthetic_demo(fixture_root, frame_count=4)

    manifest = json.loads((result.raw_root / "manifest.raw.json").read_text(encoding="utf-8"))
    assert manifest["window"]["frame_count"] == 4


def test_stage8_does_not_change_stage7_marker(tmp_path: Path):
    stage7_result = generate_stage7_sim_weld_window(tmp_path / "stage7_window")
    stage8_result = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")

    assert (stage7_result.raw_root / ".stage7_sim_window_generated").is_file()
    assert not (stage7_result.raw_root / ".stage8_h300_synthetic_demo_generated").exists()
    assert (stage8_result.raw_root / ".stage8_h300_synthetic_demo_generated").is_file()


def test_stage8_refuses_to_overwrite_stage7_fixture_root(tmp_path: Path):
    stage7_result = generate_stage7_sim_weld_window(tmp_path / "shared_window")

    with pytest.raises(ValueError, match="refusing to overwrite non-stage8 fixture directory"):
        generate_stage8_h300_synthetic_demo(stage7_result.root)

    assert (stage7_result.raw_root / ".stage7_sim_window_generated").is_file()
    assert not (stage7_result.raw_root / ".stage8_h300_synthetic_demo_generated").exists()


def test_generate_stage8_h300_synthetic_demo_script_smoke(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    output_root = tmp_path / "script_demo"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_stage8_h300_synthetic_demo.py",
            "--output-root",
            str(output_root),
            "--frames",
            "5",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "Generated Stage 8 H300 synthetic demo" in result.stdout
    assert (output_root / "raw" / "files" / "h300_job_window_story.json").is_file()


def test_stage8_h300_demo_runs_weld_workcell_importer_chain(tmp_path: Path):
    result = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    package_root = tmp_path / "package"

    import_result = run_import(
        WeldWorkcellPackageImporter(),
        ImportRequest(
            source_format="weld_workcell",
            source={"root": result.clean_root},
            output_dir=package_root,
            options={"copy_images": True},
        ),
    )

    validation = validate_package(package_root)
    candidates = export_candidates(package_root)
    draft = export_training_eval_draft(package_root, split="eval")
    rrd = write_rrd(package_root, tmp_path / "stage8_demo.rrd")

    assert validation.ok, validation.errors
    assert import_result.frame_count == 5
    assert candidates.is_file()
    assert (draft / "training_eval_manifest.json").is_file()
    assert rrd.is_file()
