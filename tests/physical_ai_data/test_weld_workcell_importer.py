from __future__ import annotations

import base64
import csv
import json
from pathlib import Path

from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.validation import validate_package
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _write_weld_source(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "images").mkdir()
    tiny_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
    )
    (root / "images" / "front_0000.png").write_bytes(tiny_png)
    (root / "job.json").write_text(
        json.dumps(
            {
                "work_order_id": "WO-1001",
                "station_id": "station_A",
                "robot_id": "robot_17",
                "welder_id": "welder_03",
                "part_id": "part_alpha",
                "seam_id": "seam_root",
                "task_name": "Root pass weld",
                "created_at": "2026-06-10T09:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _write_csv(
        root / "frames.csv",
        [
            "timestamp_s",
            "phase",
            "tcp_x",
            "tcp_y",
            "tcp_z",
            "tcp_qx",
            "tcp_qy",
            "tcp_qz",
            "tcp_qw",
            "image_path",
        ],
        [
            {
                "timestamp_s": "0.0",
                "phase": "approach",
                "tcp_x": "0.10",
                "tcp_y": "0.20",
                "tcp_z": "0.30",
                "tcp_qx": "0.0",
                "tcp_qy": "0.0",
                "tcp_qz": "0.0",
                "tcp_qw": "1.0",
                "image_path": "images/front_0000.png",
            },
            {
                "timestamp_s": "0.2",
                "phase": "weld",
                "tcp_x": "0.15",
                "tcp_y": "0.22",
                "tcp_z": "0.31",
                "tcp_qx": "0.0",
                "tcp_qy": "0.0",
                "tcp_qz": "0.1",
                "tcp_qw": "0.99",
                "image_path": "",
            },
            {
                "timestamp_s": "0.4",
                "phase": "cooldown",
                "tcp_x": "0.18",
                "tcp_y": "0.23",
                "tcp_z": "0.32",
                "tcp_qx": "0.0",
                "tcp_qy": "0.0",
                "tcp_qz": "0.2",
                "tcp_qw": "0.98",
                "image_path": "",
            },
        ],
    )
    _write_csv(
        root / "process.csv",
        [
            "timestamp_s",
            "weld_current_a",
            "weld_voltage_v",
            "wire_feed_mpm",
            "gas_flow_lpm",
            "travel_speed_mm_s",
            "defect_probability",
        ],
        [
            {
                "timestamp_s": "0.1",
                "weld_current_a": "121.5",
                "weld_voltage_v": "23.2",
                "wire_feed_mpm": "7.1",
                "gas_flow_lpm": "15.0",
                "travel_speed_mm_s": "4.5",
                "defect_probability": "0.08",
            }
        ],
    )
    _write_csv(
        root / "events.csv",
        ["timestamp_s", "event_type", "severity", "message", "object_id"],
        [
            {
                "timestamp_s": "0.31",
                "event_type": "arc_start",
                "severity": "info",
                "message": "Arc stabilized",
                "object_id": "seam_root",
            }
        ],
    )
    _write_csv(
        root / "review_labels.csv",
        ["timestamp_s", "label_type", "value", "confidence", "review_status", "reviewer"],
        [
            {
                "timestamp_s": "0.19",
                "label_type": "bead_quality",
                "value": "acceptable",
                "confidence": "0.9",
                "review_status": "reviewed",
                "reviewer": "qa_01",
            }
        ],
    )
    return root


def test_weld_workcell_importer_creates_valid_robot_welding_package(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    request = ImportRequest(
        source_format="weld_workcell",
        source={"root": source},
        output_dir=tmp_path / "package",
        options={"copy_images": True},
    )

    result = run_import(WeldWorkcellPackageImporter(), request)

    package = tmp_path / "package"
    validation = validate_package(package)
    assert validation.ok, validation.errors
    assert result.source_format == "weld_workcell"
    assert result.source_id == str(source)
    assert result.frame_count == 3
    manifest = json.loads((package / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenario_type"] == "robot_welding_station"
    assert manifest["package_id"] == "weld_workcell_WO-1001_station_A"
    assert manifest["task"]["name"] == "Root pass weld"
    assert manifest["source_dataset"]["format"] == "weld_workcell"
    assert manifest["source_dataset"]["image_copy_policy"] == "copied_to_artifacts_images_frame_id"
    frame_rows = _rows(package / "frames.csv")
    assert [row["frame_id"] for row in frame_rows] == ["frame_0000", "frame_0001", "frame_0002"]
    assert frame_rows[0]["image_ref"] == "artifacts/images/frame_0000.png"
    assert (package / "artifacts/images/frame_0000.png").is_file()
    trajectory_rows = _rows(package / "artifacts/trajectories/tcp_path.csv")
    assert list(trajectory_rows[0]) == ["frame_id", "timestamp_s", "x", "y", "z", "qx", "qy", "qz", "qw"]
    assert (package / "artifacts/source/job.json").is_file()
    assert (package / "artifacts/source/frames.csv").is_file()
    assert (package / "artifacts/source/process.csv").is_file()
    assert (package / "artifacts/source/events.csv").is_file()
    assert (package / "artifacts/source/review_labels.csv").is_file()
