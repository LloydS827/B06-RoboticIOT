from __future__ import annotations

import csv
import json
from pathlib import Path

from physical_ai_data.validation import validate_package

EXPECTED_SUMMARY_KEYS = {
    "package_id",
    "scenario_type",
    "frame_count",
    "event_count",
    "label_count",
    "metric_count",
    "artifact_ref_count",
}


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_minimal_package(root: Path) -> None:
    (root / "artifacts" / "images").mkdir(parents=True)
    (root / "artifacts" / "images" / "frame_0000.png").write_bytes(b"placeholder")
    manifest = {
        "schema_version": "physical-ai-package/v0.1",
        "package_id": "pkg_test_001",
        "scenario_type": "robot_welding_station",
        "created_at": "2026-06-08T00:00:00Z",
        "task": {"task_id": "task_001", "name": "test"},
        "devices": [{"device_id": "robot_001", "type": "robot_arm"}],
        "objects": [{"object_id": "workpiece_001", "type": "workpiece"}],
        "coordinate_frames": [
            {"frame_id": "station", "parent_frame_id": "", "pose_ref": ""},
            {"frame_id": "tcp", "parent_frame_id": "station", "pose_ref": ""},
        ],
        "timelines": [{"timeline_id": "sim_time", "unit": "s"}],
        "tables": {
            "frames": "frames.csv",
            "events": "events.csv",
            "labels": "labels.csv",
            "metrics": "metrics.csv",
        },
        "artifacts": {"images": "artifacts/images"},
    }
    (root / "physical_ai_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _write_csv(
        root / "frames.csv",
        [
            "frame_id",
            "timestamp_s",
            "timeline",
            "phase",
            "coordinate_frame_id",
            "robot_state_ref",
            "tcp_pose_ref",
            "image_ref",
            "point_cloud_ref",
            "trajectory_ref",
        ],
        [
            {
                "frame_id": "frame_0000",
                "timestamp_s": 0.0,
                "timeline": "sim_time",
                "phase": "test",
                "coordinate_frame_id": "tcp",
                "robot_state_ref": "",
                "tcp_pose_ref": "",
                "image_ref": "artifacts/images/frame_0000.png",
                "point_cloud_ref": "",
                "trajectory_ref": "",
            }
        ],
    )
    _write_csv(
        root / "events.csv",
        ["event_id", "timestamp_s", "event_type", "severity", "message", "related_frame_id", "related_object_id"],
        [{"event_id": "event_0000", "timestamp_s": 0.0, "event_type": "start", "severity": "info", "message": "start", "related_frame_id": "frame_0000", "related_object_id": ""}],
    )
    _write_csv(
        root / "labels.csv",
        ["label_id", "label_type", "target_ref", "value", "confidence", "source"],
        [{"label_id": "label_0000", "label_type": "quality", "target_ref": "frame:frame_0000", "value": "ok", "confidence": 1.0, "source": "sim"}],
    )
    _write_csv(
        root / "metrics.csv",
        ["metric_id", "timestamp_s", "metric_name", "value", "unit", "source"],
        [{"metric_id": "metric_0000", "timestamp_s": 0.0, "metric_name": "score", "value": 0.1, "unit": "ratio", "source": "sim"}],
    )


def test_valid_minimal_package_passes(tmp_path: Path):
    _write_minimal_package(tmp_path)

    result = validate_package(tmp_path)

    assert result.ok
    assert result.summary["scenario_type"] == "robot_welding_station"
    assert result.summary["frame_count"] == 1
    assert result.errors == []


def test_missing_manifest_reports_error(tmp_path: Path):
    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "missing_manifest" for error in result.errors)
    assert EXPECTED_SUMMARY_KEYS <= result.summary.keys()
    assert result.summary["package_id"] == ""
    assert result.summary["frame_count"] == 0


def test_missing_required_table_column_reports_error(tmp_path: Path):
    _write_minimal_package(tmp_path)
    _write_csv(tmp_path / "frames.csv", ["frame_id"], [{"frame_id": "frame_0000"}])

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "missing_table_columns" and "timestamp_s" in error.message for error in result.errors)


def test_missing_declared_extra_table_reports_error(tmp_path: Path):
    _write_minimal_package(tmp_path)
    manifest_path = tmp_path / "physical_ai_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["tables"]["candidates"] = "missing_candidates.csv"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "missing_table" and "missing_candidates.csv" in error.message for error in result.errors)


def test_absolute_declared_table_ref_is_invalid_even_when_file_exists(tmp_path: Path):
    _write_minimal_package(tmp_path)
    outside_frames = tmp_path.parent / f"{tmp_path.name}_frames.csv"
    outside_frames.write_text((tmp_path / "frames.csv").read_text(encoding="utf-8"), encoding="utf-8")
    manifest_path = tmp_path / "physical_ai_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["tables"]["frames"] = str(outside_frames)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "invalid_table_ref" and "absolute" in error.message for error in result.errors)


def test_parent_directory_declared_table_ref_escape_is_invalid_even_when_file_exists(tmp_path: Path):
    _write_minimal_package(tmp_path)
    outside_candidates = tmp_path.parent / f"{tmp_path.name}_candidates.csv"
    _write_csv(outside_candidates, ["candidate_id"], [{"candidate_id": "candidate_0000"}])
    manifest_path = tmp_path / "physical_ai_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["tables"]["candidates"] = f"../{outside_candidates.name}"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "invalid_table_ref" and "package root" in error.message for error in result.errors)


def test_non_empty_ref_must_exist(tmp_path: Path):
    _write_minimal_package(tmp_path)
    rows = list(csv.DictReader((tmp_path / "frames.csv").open(newline="", encoding="utf-8")))
    rows[0]["image_ref"] = "artifacts/images/missing.png"
    _write_csv(tmp_path / "frames.csv", list(rows[0].keys()), rows)

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "missing_artifact_ref" for error in result.errors)


def test_absolute_ref_is_invalid_even_when_file_exists(tmp_path: Path):
    _write_minimal_package(tmp_path)
    outside_file = tmp_path / "absolute.png"
    outside_file.write_bytes(b"placeholder")
    rows = list(csv.DictReader((tmp_path / "frames.csv").open(newline="", encoding="utf-8")))
    rows[0]["image_ref"] = str(outside_file)
    _write_csv(tmp_path / "frames.csv", list(rows[0].keys()), rows)

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "invalid_artifact_ref" and "absolute" in error.message for error in result.errors)


def test_parent_directory_ref_escape_is_invalid_even_when_file_exists(tmp_path: Path):
    _write_minimal_package(tmp_path)
    outside_file = tmp_path.parent / f"{tmp_path.name}_outside.png"
    outside_file.write_bytes(b"placeholder")
    rows = list(csv.DictReader((tmp_path / "frames.csv").open(newline="", encoding="utf-8")))
    rows[0]["image_ref"] = f"../{outside_file.name}"
    _write_csv(tmp_path / "frames.csv", list(rows[0].keys()), rows)

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "invalid_artifact_ref" and "package root" in error.message for error in result.errors)


def test_manifest_pose_ref_must_exist_when_non_empty(tmp_path: Path):
    _write_minimal_package(tmp_path)
    manifest = json.loads((tmp_path / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    manifest["coordinate_frames"][1]["pose_ref"] = "artifacts/poses/missing_tcp_pose.csv"
    (tmp_path / "physical_ai_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "missing_artifact_ref" and "pose_ref" in error.message for error in result.errors)


def test_malformed_csv_row_reports_error_instead_of_crashing(tmp_path: Path):
    _write_minimal_package(tmp_path)
    rows = list(csv.DictReader((tmp_path / "frames.csv").open(newline="", encoding="utf-8")))
    fieldnames = list(rows[0].keys())
    with (tmp_path / "frames.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(fieldnames)
        writer.writerow([rows[0][field] for field in fieldnames] + ["extra-cell"])

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "malformed_csv_row" and "frames.csv" in error.message for error in result.errors)


def test_table_read_failure_reports_error_instead_of_crashing(tmp_path: Path):
    _write_minimal_package(tmp_path)
    (tmp_path / "frames.csv").unlink()
    (tmp_path / "frames.csv").mkdir()

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "unreadable_table" and "frames.csv" in error.message for error in result.errors)


def test_underfilled_label_row_reports_error_instead_of_crashing(tmp_path: Path):
    _write_minimal_package(tmp_path)
    with (tmp_path / "labels.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["label_id", "label_type", "target_ref", "value", "confidence", "source"])
        writer.writerow(["label_0001", "quality"])

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "malformed_csv_row" and "labels.csv" in error.message for error in result.errors)


def test_manifest_devices_objects_and_timelines_must_be_lists(tmp_path: Path):
    _write_minimal_package(tmp_path)
    manifest_path = tmp_path / "physical_ai_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["devices"] = {"device_id": "robot_001", "type": "robot_arm"}
    manifest["objects"] = {"object_id": "workpiece_001", "type": "workpiece"}
    manifest["timelines"] = {"timeline_id": "sim_time", "unit": "s"}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "invalid_manifest_list" and error.path == "devices" for error in result.errors)
    assert any(error.code == "invalid_manifest_list" and error.path == "objects" for error in result.errors)
    assert any(error.code == "invalid_manifest_list" and error.path == "timelines" for error in result.errors)


def test_events_and_metrics_timestamp_must_be_numeric(tmp_path: Path):
    _write_minimal_package(tmp_path)
    _write_csv(
        tmp_path / "events.csv",
        ["event_id", "timestamp_s", "event_type", "severity", "message", "related_frame_id", "related_object_id"],
        [{"event_id": "event_0000", "timestamp_s": "not-a-number", "event_type": "start", "severity": "info", "message": "start", "related_frame_id": "frame_0000", "related_object_id": ""}],
    )
    _write_csv(
        tmp_path / "metrics.csv",
        ["metric_id", "timestamp_s", "metric_name", "value", "unit", "source"],
        [{"metric_id": "metric_0000", "timestamp_s": "also-bad", "metric_name": "score", "value": 0.1, "unit": "ratio", "source": "sim"}],
    )

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "invalid_timestamp" and "events.csv" in error.message for error in result.errors)
    assert any(error.code == "invalid_timestamp" and "metrics.csv" in error.message for error in result.errors)


def test_label_target_refs_must_exist(tmp_path: Path):
    _write_minimal_package(tmp_path)
    _write_csv(
        tmp_path / "labels.csv",
        ["label_id", "label_type", "target_ref", "value", "confidence", "source"],
        [
            {"label_id": "label_0001", "label_type": "quality", "target_ref": "frame:missing", "value": "bad", "confidence": 1.0, "source": "sim"},
            {"label_id": "label_0002", "label_type": "quality", "target_ref": "object:missing", "value": "bad", "confidence": 1.0, "source": "sim"},
        ],
    )

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "unknown_frame_id" and "frame:missing" in error.message for error in result.errors)
    assert any(error.code == "unknown_object_id" and "object:missing" in error.message for error in result.errors)


def test_missing_recommended_artifact_directory_reports_warning(tmp_path: Path):
    _write_minimal_package(tmp_path)
    (tmp_path / "artifacts" / "point_clouds").rmdir() if (tmp_path / "artifacts" / "point_clouds").exists() else None

    result = validate_package(tmp_path)

    assert result.ok
    assert any(warning.code == "missing_recommended_artifact_dir" for warning in result.warnings)


def test_timelines_must_include_sim_time(tmp_path: Path):
    _write_minimal_package(tmp_path)
    manifest = json.loads((tmp_path / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    manifest["timelines"] = [{"timeline_id": "robot_tick", "unit": "tick"}]
    (tmp_path / "physical_ai_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "missing_sim_time" for error in result.errors)
