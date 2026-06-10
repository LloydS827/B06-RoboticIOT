from __future__ import annotations

import base64
import csv
import json
from pathlib import Path

import pytest

from physical_ai_data.candidates import export_candidates, summarize_package
from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.package_io import read_json
from physical_ai_data.rerun_adapter import write_rrd
from physical_ai_data.training_export import export_training_eval_draft
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


def _fieldnames(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or [])


def _rewrite_csv_without_column(path: Path, missing: str) -> None:
    fieldnames = [field for field in _fieldnames(path) if field != missing]
    rows = [{field: row[field] for field in fieldnames} for row in _rows(path)]
    _write_csv(path, fieldnames, rows)


def _rewrite_csv_value(path: Path, row_index: int, column: str, value: str) -> None:
    fieldnames = _fieldnames(path)
    rows = _rows(path)
    rows[row_index][column] = value
    _write_csv(path, fieldnames, rows)


def _import_weld_source(source: Path, package: Path, *, copy_images: bool = True):
    request = ImportRequest(
        source_format="weld_workcell",
        source={"root": source},
        output_dir=package,
        options={"copy_images": copy_images},
    )
    return run_import(WeldWorkcellPackageImporter(), request)


def _write_weld_source(root: Path, *, include_review_labels: bool = True) -> Path:
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
    if include_review_labels:
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


def test_weld_workcell_importer_maps_tables_and_source_dataset(tmp_path: Path):
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
    manifest = read_json(package / "physical_ai_manifest.json")
    assert manifest["scenario_type"] == "robot_welding_station"
    assert manifest["package_id"] == "weld_workcell_WO-1001_station_A"
    assert manifest["task"]["name"] == "Root pass weld"
    assert manifest["source_dataset"]["format"] == "weld_workcell"
    assert manifest["source_dataset"]["image_copy_policy"] == "copied_to_artifacts_images_frame_id"
    assert manifest["source_dataset"]["frame_count"] == 3
    assert manifest["source_dataset"]["process_row_count"] == 1
    assert manifest["source_dataset"]["event_count"] == 1
    assert manifest["source_dataset"]["label_count"] == 1
    assert manifest["source_dataset"]["job_json_ref"] == "artifacts/source/job.json"
    assert manifest["source_dataset"]["frames_csv_ref"] == "artifacts/source/frames.csv"
    assert manifest["source_dataset"]["process_csv_ref"] == "artifacts/source/process.csv"
    assert manifest["source_dataset"]["events_csv_ref"] == "artifacts/source/events.csv"
    assert manifest["source_dataset"]["review_labels_csv_ref"] == "artifacts/source/review_labels.csv"
    assert [item["object_id"] for item in manifest["objects"]] == ["part_alpha", "seam_root"]
    assert [item["frame_id"] for item in manifest["coordinate_frames"]] == [
        "station",
        "robot_base",
        "tcp",
        "camera_front",
        "workpiece",
    ]
    frame_rows = _rows(package / "frames.csv")
    assert [row["frame_id"] for row in frame_rows] == ["frame_0000", "frame_0001", "frame_0002"]
    assert [row["timeline"] for row in frame_rows] == ["sim_time", "sim_time", "sim_time"]
    assert [row["coordinate_frame_id"] for row in frame_rows] == ["tcp", "tcp", "tcp"]
    assert frame_rows[0]["image_ref"] == "artifacts/images/frame_0000.png"
    assert frame_rows[0]["trajectory_ref"] == "artifacts/trajectories/tcp_path.csv"
    assert (package / "artifacts/images/frame_0000.png").is_file()
    assert (package / "artifacts/images/frame_0000.png").read_bytes() == (source / "images/front_0000.png").read_bytes()
    trajectory_rows = _rows(package / "artifacts/trajectories/tcp_path.csv")
    assert list(trajectory_rows[0]) == ["frame_id", "timestamp_s", "x", "y", "z", "qx", "qy", "qz", "qw"]
    assert trajectory_rows[0] == {
        "frame_id": "frame_0000",
        "timestamp_s": "0.0",
        "x": "0.10",
        "y": "0.20",
        "z": "0.30",
        "qx": "0.0",
        "qy": "0.0",
        "qz": "0.0",
        "qw": "1.0",
    }
    assert trajectory_rows[1]["x"] == "0.15"
    metric_rows = _rows(package / "metrics.csv")
    assert [(row["metric_name"], row["unit"]) for row in metric_rows] == [
        ("weld_current", "A"),
        ("weld_voltage", "V"),
        ("wire_feed", "m/min"),
        ("gas_flow", "L/min"),
        ("travel_speed", "mm/s"),
        ("defect_probability", "ratio"),
    ]
    event_rows = _rows(package / "events.csv")
    assert event_rows[0]["timestamp_s"] == "0.31"
    assert event_rows[0]["related_frame_id"] == "frame_0002"
    assert event_rows[0]["related_object_id"] == "seam_root"
    label_rows = _rows(package / "labels.csv")
    assert label_rows[0]["target_ref"] == "frame:frame_0001"
    assert label_rows[0]["source"] == "weld_workcell_review"
    assert (package / "artifacts/source/job.json").is_file()
    assert (package / "artifacts/source/frames.csv").is_file()
    assert (package / "artifacts/source/process.csv").is_file()
    assert (package / "artifacts/source/events.csv").is_file()
    assert (package / "artifacts/source/review_labels.csv").is_file()


def test_weld_workcell_importer_leaves_image_refs_empty_when_copy_images_false(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    request = ImportRequest(
        source_format="weld_workcell",
        source={"root": source},
        output_dir=tmp_path / "package",
        options={"copy_images": False},
    )

    run_import(WeldWorkcellPackageImporter(), request)

    package = tmp_path / "package"
    frame_rows = _rows(package / "frames.csv")
    manifest = read_json(package / "physical_ai_manifest.json")
    validation = validate_package(package)
    assert validation.ok, validation.errors
    assert [row["image_ref"] for row in frame_rows] == ["", "", ""]
    assert manifest["source_dataset"]["image_copy_policy"] == "image_refs_empty_when_copy_images_false"
    assert list((package / "artifacts/images").iterdir()) == []


def test_weld_workcell_importer_omits_absent_review_labels_ref(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source", include_review_labels=False)
    request = ImportRequest(
        source_format="weld_workcell",
        source={"root": source},
        output_dir=tmp_path / "package",
        options={"copy_images": True},
    )

    run_import(WeldWorkcellPackageImporter(), request)

    package = tmp_path / "package"
    validation = validate_package(package)
    assert validation.ok, validation.errors
    manifest = read_json(package / "physical_ai_manifest.json")
    assert _rows(package / "labels.csv") == []
    assert manifest["source_dataset"]["label_count"] == 0
    assert "review_labels_csv_ref" not in manifest["source_dataset"]
    assert not (package / "artifacts/source/review_labels.csv").exists()


def test_weld_workcell_importer_outputs_pipeline_compatible_package(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    request = ImportRequest(
        source_format="weld_workcell",
        source={"root": source},
        output_dir=tmp_path / "package",
        options={"copy_images": True},
    )

    run_import(WeldWorkcellPackageImporter(), request)

    package = tmp_path / "package"
    summary = summarize_package(package)
    candidates = export_candidates(package)
    draft = export_training_eval_draft(package, split="eval")
    rrd = write_rrd(package, tmp_path / "weld_workcell.rrd")
    training_eval_manifest = read_json(draft / "training_eval_manifest.json")
    assert summary["package_id"] == "weld_workcell_WO-1001_station_A"
    assert candidates.is_file()
    assert training_eval_manifest["export_format"] == "physical-ai-training-eval-draft/v0.2"
    assert rrd.exists()
    assert rrd.stat().st_size > 0


def test_weld_workcell_importer_rejects_source_format_mismatch(tmp_path: Path):
    request = ImportRequest(
        source_format="other",
        source={},
        output_dir=tmp_path / "package",
        options={},
    )

    with pytest.raises(ValueError, match="cannot handle other"):
        run_import(WeldWorkcellPackageImporter(), request)


def test_weld_workcell_importer_requires_process_csv(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    (source / "process.csv").unlink()

    with pytest.raises(ValueError, match="source.root must contain process.csv"):
        _import_weld_source(source, tmp_path / "package")


def test_weld_workcell_importer_rejects_in_place_output_dir(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")

    with pytest.raises(ValueError, match="output_dir must not be the same as source.root"):
        _import_weld_source(source, source)

    assert (source / "frames.csv").is_file()
    assert not (source / "artifacts").exists()


def test_weld_workcell_importer_requires_robot_id(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    job = json.loads((source / "job.json").read_text(encoding="utf-8"))
    job.pop("robot_id")
    (source / "job.json").write_text(json.dumps(job) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="job.json missing required fields: robot_id"):
        _import_weld_source(source, tmp_path / "package")


def test_weld_workcell_importer_requires_frames_tcp_x_column(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _rewrite_csv_without_column(source / "frames.csv", "tcp_x")

    with pytest.raises(ValueError, match="frames.csv missing required columns: tcp_x"):
        _import_weld_source(source, tmp_path / "package")


def test_weld_workcell_importer_requires_process_weld_current_column(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _rewrite_csv_without_column(source / "process.csv", "weld_current_a")

    with pytest.raises(ValueError, match="process.csv missing required columns: weld_current_a"):
        _import_weld_source(source, tmp_path / "package")


def test_weld_workcell_importer_requires_review_label_confidence_column(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _rewrite_csv_without_column(source / "review_labels.csv", "confidence")

    with pytest.raises(ValueError, match="review_labels.csv missing required columns: confidence"):
        _import_weld_source(source, tmp_path / "package")


def test_weld_workcell_importer_rejects_malformed_events_rows(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    (source / "events.csv").write_text(
        "timestamp_s,event_type,severity,message,object_id\n"
        "0.31,arc_start,info,Arc stabilized,seam_root,extra\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="events.csv has malformed rows"):
        _import_weld_source(source, tmp_path / "package")


def test_weld_workcell_importer_rejects_nonfinite_process_numeric(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _rewrite_csv_value(source / "process.csv", 0, "weld_current_a", "nan")

    with pytest.raises(ValueError, match="weld_current_a must be a finite number"):
        _import_weld_source(source, tmp_path / "package")


def test_weld_workcell_importer_rejects_nonfinite_review_label_confidence(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _rewrite_csv_value(source / "review_labels.csv", 0, "confidence", "inf")

    with pytest.raises(ValueError, match="confidence must be a finite number"):
        _import_weld_source(source, tmp_path / "package")


def test_weld_workcell_importer_validates_skipped_review_label_rows(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _rewrite_csv_value(source / "review_labels.csv", 0, "label_type", "")
    _rewrite_csv_value(source / "review_labels.csv", 0, "confidence", "inf")

    with pytest.raises(ValueError, match="confidence must be a finite number"):
        _import_weld_source(source, tmp_path / "package")


@pytest.mark.parametrize(
    ("image_path", "message"),
    [
        ("/tmp/front_0000.png", "image_path must be relative to source.root"),
        ("../front_0000.png", "image_path must be relative to source.root"),
        ("images/missing.png", "source image does not exist"),
    ],
)
@pytest.mark.parametrize("copy_images", [True, False])
def test_weld_workcell_importer_rejects_invalid_image_paths(
    tmp_path: Path,
    image_path: str,
    message: str,
    copy_images: bool,
):
    source = _write_weld_source(tmp_path / "source")
    _rewrite_csv_value(source / "frames.csv", 0, "image_path", image_path)

    with pytest.raises(ValueError, match=message):
        _import_weld_source(source, tmp_path / "package", copy_images=copy_images)


def test_weld_workcell_importer_rejects_symlink_escape_image(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    outside = tmp_path / "outside.png"
    outside.write_bytes((source / "images/front_0000.png").read_bytes())
    (source / "images/escape.png").symlink_to(outside)
    _rewrite_csv_value(source / "frames.csv", 0, "image_path", "images/escape.png")

    with pytest.raises(ValueError, match="image_path must be relative to source.root"):
        _import_weld_source(source, tmp_path / "package")


def test_weld_workcell_importer_requires_frame_data_rows(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _write_csv(source / "frames.csv", _fieldnames(source / "frames.csv"), [])

    with pytest.raises(ValueError, match="frames.csv must contain at least one data row"):
        _import_weld_source(source, tmp_path / "package")


def test_weld_workcell_importer_rejects_unknown_event_object_id(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _rewrite_csv_value(source / "events.csv", 0, "object_id", "unknown_fixture")

    with pytest.raises(ValueError, match="events.csv object_id must be one of"):
        _import_weld_source(source, tmp_path / "package")


def test_weld_workcell_importer_uses_nearest_frame_edges_and_earlier_tie(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _write_csv(
        source / "events.csv",
        ["timestamp_s", "event_type", "severity", "message", "object_id"],
        [
            {
                "timestamp_s": "-0.1",
                "event_type": "before_first",
                "severity": "info",
                "message": "",
                "object_id": "seam_root",
            },
            {
                "timestamp_s": "0.1",
                "event_type": "exact_tie",
                "severity": "info",
                "message": "",
                "object_id": "seam_root",
            },
            {
                "timestamp_s": "0.9",
                "event_type": "after_last",
                "severity": "info",
                "message": "",
                "object_id": "seam_root",
            },
        ],
    )

    _import_weld_source(source, tmp_path / "package")

    event_rows = _rows(tmp_path / "package/events.csv")
    assert [row["related_frame_id"] for row in event_rows] == ["frame_0000", "frame_0000", "frame_0002"]
