from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from physical_ai_data.candidates import export_candidates
from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.package_io import read_json
from physical_ai_data.rerun_adapter import write_rrd
from physical_ai_data.stage7_sim_window import generate_stage7_sim_weld_window
from physical_ai_data.training_export import export_training_eval_draft
from physical_ai_data.validation import validate_package
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter


def _json_lines(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_generate_stage7_sim_weld_window_writes_raw_and_clean_fixture(tmp_path: Path):
    fixture_root = tmp_path / "stage7_window"
    result = generate_stage7_sim_weld_window(fixture_root)

    assert result.root == fixture_root
    assert result.raw_root == fixture_root / "raw"
    assert result.clean_root == fixture_root / "clean" / "weld_workcell"

    raw_manifest = json.loads((result.raw_root / "manifest.raw.json").read_text(encoding="utf-8"))
    assert raw_manifest["stage"] == "stage7"
    assert raw_manifest["source_type"] == "simulated"
    assert raw_manifest["not_production_protocol"] is True
    assert raw_manifest["desensitization"]["status"] == "synthetic"
    assert raw_manifest["window"]["task_id"] == "sim_task_stage7_001"
    assert raw_manifest["window"]["frame_count"] == 5
    assert raw_manifest["assumptions"]["timestamp_source"] == "sim_time_seconds"
    assert raw_manifest["assumptions"]["units"]["tcp_position"] == "m"
    assert raw_manifest["assumptions"]["coordinate_frames"]["tcp"] == "relative_to_robot_base"
    assert raw_manifest["raw_zone"]["sdk_robot_state_ref"] == "sdk/robot_state.ndjson"

    robot_state_lines = _json_lines(result.raw_root / "sdk" / "robot_state.ndjson")
    assert len(robot_state_lines) == 5

    task_messages = _json_lines(result.raw_root / "tcp_json" / "hmi_task_messages.ndjson")
    assert len(task_messages) >= 2
    assert all(message["task_id"] == "sim_task_stage7_001" for message in task_messages)

    for relative_path in [
        "files/robot_program.lua",
        "files/robot_trajectory.json",
        "files/seam_trajectory.json",
        "files/images/front_0000.png",
        "process/welding_process.csv",
        "events/event_log.ndjson",
    ]:
        assert (result.raw_root / relative_path).is_file()

    for relative_path in [
        "job.json",
        "frames.csv",
        "process.csv",
        "events.csv",
        "review_labels.csv",
        "images/front_0000.png",
    ]:
        assert (result.clean_root / relative_path).is_file()


def test_generate_stage7_sim_weld_window_refuses_unknown_existing_raw_dir(tmp_path: Path):
    fixture_root = tmp_path / "stage7_window"
    sentinel = fixture_root / "raw" / "keep.txt"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("real raw data\n", encoding="utf-8")

    with pytest.raises(ValueError, match="refusing to overwrite non-stage7 fixture directory"):
        generate_stage7_sim_weld_window(fixture_root)

    assert sentinel.read_text(encoding="utf-8") == "real raw data\n"


def test_generate_stage7_sim_weld_window_refuses_unknown_files_added_to_generated_roots(tmp_path: Path):
    fixture_root = tmp_path / "stage7_window"
    result = generate_stage7_sim_weld_window(fixture_root)
    raw_sentinel = result.raw_root / "keep.txt"
    clean_sentinel = result.clean_root / "keep.txt"
    raw_sentinel.write_text("user raw data\n", encoding="utf-8")
    clean_sentinel.write_text("user clean data\n", encoding="utf-8")

    with pytest.raises(ValueError, match="refusing to overwrite non-stage7 fixture directory"):
        generate_stage7_sim_weld_window(fixture_root)

    assert raw_sentinel.read_text(encoding="utf-8") == "user raw data\n"
    assert clean_sentinel.read_text(encoding="utf-8") == "user clean data\n"


def test_generate_stage7_sim_weld_window_refuses_unknown_nested_files_added_to_generated_roots(tmp_path: Path):
    fixture_root = tmp_path / "stage7_window"
    result = generate_stage7_sim_weld_window(fixture_root)
    raw_sentinel = result.raw_root / "files" / "user_keep.txt"
    clean_sentinel = result.clean_root / "images" / "user_keep.png"
    raw_sentinel.write_text("nested raw data\n", encoding="utf-8")
    clean_sentinel.write_bytes(b"nested clean data\n")

    with pytest.raises(ValueError, match="refusing to overwrite non-stage7 fixture directory"):
        generate_stage7_sim_weld_window(fixture_root)

    assert raw_sentinel.read_text(encoding="utf-8") == "nested raw data\n"
    assert clean_sentinel.read_bytes() == b"nested clean data\n"


def test_generate_stage7_sim_weld_window_can_overwrite_own_generated_roots(tmp_path: Path):
    fixture_root = tmp_path / "stage7_window"
    generate_stage7_sim_weld_window(fixture_root, frame_count=5)

    result = generate_stage7_sim_weld_window(fixture_root, frame_count=4)

    raw_manifest = json.loads((result.raw_root / "manifest.raw.json").read_text(encoding="utf-8"))
    assert raw_manifest["window"]["frame_count"] == 4
    assert (result.raw_root / ".stage7_sim_window_generated").is_file()
    assert (result.clean_root / ".stage7_sim_window_generated").is_file()


def test_stage7_sim_weld_window_runs_weld_workcell_importer_chain(tmp_path: Path):
    result = generate_stage7_sim_weld_window(tmp_path)
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
    manifest = read_json(package_root / "physical_ai_manifest.json")
    candidates = export_candidates(package_root)
    draft = export_training_eval_draft(package_root, split="eval")
    rrd = write_rrd(package_root, tmp_path / "stage7_window.rrd")

    assert validation.ok, validation.errors
    assert import_result.frame_count == 5
    assert manifest["scenario_type"] == "robot_welding_station"
    assert manifest["source_dataset"]["format"] == "weld_workcell"
    assert candidates.is_file()
    assert (draft / "training_eval_manifest.json").is_file()
    assert rrd.suffix == ".rrd"
    assert rrd.is_file()


def test_generate_stage7_sim_window_script_smoke(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    output_root = tmp_path / "script_window"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_stage7_sim_window.py",
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
    assert "Generated Stage 7 simulated weld window" in result.stdout
    assert (output_root / "raw" / "manifest.raw.json").is_file()
    assert (output_root / "clean" / "weld_workcell" / "job.json").is_file()
