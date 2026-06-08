from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Mapping

from physical_ai_data.package_io import ensure_dir, write_csv_rows, write_json
from physical_ai_data.schema import REQUIRED_TABLE_COLUMNS, SCHEMA_VERSION

MANIFEST_FILENAME = "physical_ai_manifest.json"
CREATED_AT = "2026-06-08T00:00:00Z"
IMAGE_SIZE = (160, 96)


def generate_welding_package(root: str | Path, frame_count: int = 60, random_seed: int = 42) -> Path:
    package_root = Path(root)
    _prepare_package_dirs(package_root)

    rng = random.Random(random_seed)
    frame_total = _positive_frame_count(frame_count)
    frames: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []
    trajectory_rows: list[dict[str, object]] = []

    for index in range(frame_total):
        frame_id = _frame_id(index)
        ratio = _ratio(index, frame_total)
        timestamp_s = round(8.0 * ratio, 4)
        phase = _welding_phase(ratio)
        x = round(-0.4 + 0.8 * ratio, 6)
        y = round(0.035 * math.sin(math.pi * ratio), 6)
        z = round(0.065 + 0.004 * math.sin(2 * math.pi * ratio), 6)
        risk_peak = math.exp(-((ratio - 0.58) / 0.14) ** 2)
        current_base = 168.0 if phase == "welding" else 82.0
        voltage_base = 21.2 if phase == "welding" else 15.0
        weld_current = round(current_base + 16.0 * risk_peak + rng.uniform(-2.0, 2.0), 3)
        weld_voltage = round(voltage_base + 1.2 * risk_peak + rng.uniform(-0.2, 0.2), 3)
        defect_probability = round(min(0.95, 0.05 + 0.72 * risk_peak + rng.uniform(0.0, 0.025)), 4)
        image_ref = f"artifacts/images/{frame_id}.png"

        frames.append(
            {
                "frame_id": frame_id,
                "timestamp_s": timestamp_s,
                "timeline": "sim_time",
                "phase": phase,
                "coordinate_frame_id": "tcp",
                "robot_state_ref": "",
                "tcp_pose_ref": "",
                "image_ref": image_ref,
                "point_cloud_ref": "artifacts/point_clouds/workpiece.csv",
                "trajectory_ref": "artifacts/trajectories/tcp_path.csv",
            }
        )
        trajectory_rows.append({"frame_id": frame_id, "timestamp_s": timestamp_s, "x": x, "y": y, "z": z, "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0})
        metric_rows.extend(
            [
                _metric_row(index, timestamp_s, "weld_current", weld_current, "A"),
                _metric_row(index, timestamp_s, "weld_voltage", weld_voltage, "V"),
                _metric_row(index, timestamp_s, "defect_probability", defect_probability, "ratio"),
            ]
        )
        _write_welding_image(package_root / image_ref, ratio, defect_probability)

    events = _welding_events(frames, metric_rows)
    labels = _welding_labels(frames, metric_rows)

    _write_manifest(package_root, _welding_manifest(frame_total, random_seed))
    _write_standard_tables(package_root, frames, events, labels, metric_rows)
    _write_point_cloud(package_root / "artifacts/point_clouds/workpiece.csv", _welding_point_cloud(frame_total))
    _write_trajectory(package_root / "artifacts/trajectories/tcp_path.csv", trajectory_rows)
    _write_readme(package_root / "README.md", "Robot welding station", "Deterministic simulated weld seam package.")
    return package_root


def generate_pick_sort_package(root: str | Path, frame_count: int = 40, random_seed: int = 42) -> Path:
    package_root = Path(root)
    _prepare_package_dirs(package_root)

    rng = random.Random(random_seed)
    frame_total = _positive_frame_count(frame_count)
    frames: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []
    trajectory_rows: list[dict[str, object]] = []

    for index in range(frame_total):
        frame_id = _frame_id(index)
        ratio = _ratio(index, frame_total)
        timestamp_s = round(6.0 * ratio, 4)
        phase = _pick_sort_phase(ratio)
        x = round(-0.26 + 0.52 * ratio, 6)
        y = round(-0.18 + 0.36 * math.sin(math.pi * ratio), 6)
        z = round(0.12 + 0.1 * math.sin(math.pi * ratio), 6)
        object_confidence = round(max(0.1, min(0.99, 0.64 + 0.28 * math.cos(math.pi * (ratio - 0.15)) + rng.uniform(-0.025, 0.025))), 4)
        grip_confidence = round(max(0.1, min(0.99, 0.42 + 0.52 * math.sin(math.pi * ratio) + rng.uniform(-0.03, 0.03))), 4)
        image_ref = f"artifacts/images/{frame_id}.png"

        frames.append(
            {
                "frame_id": frame_id,
                "timestamp_s": timestamp_s,
                "timeline": "sim_time",
                "phase": phase,
                "coordinate_frame_id": "tcp",
                "robot_state_ref": "",
                "tcp_pose_ref": "",
                "image_ref": image_ref,
                "point_cloud_ref": "artifacts/point_clouds/workpiece.csv",
                "trajectory_ref": "artifacts/trajectories/tcp_path.csv",
            }
        )
        trajectory_rows.append({"frame_id": frame_id, "timestamp_s": timestamp_s, "x": x, "y": y, "z": z, "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0})
        metric_rows.extend(
            [
                _metric_row(index, timestamp_s, "grip_confidence", grip_confidence, "ratio"),
                _metric_row(index, timestamp_s, "object_confidence", object_confidence, "ratio"),
            ]
        )
        _write_pick_sort_image(package_root / image_ref, ratio, phase, object_confidence)

    success = _pick_sort_success(metric_rows)
    events = _pick_sort_events(frames, success)
    labels = _pick_sort_labels(frames, success)

    _write_manifest(package_root, _pick_sort_manifest(frame_total, random_seed))
    _write_standard_tables(package_root, frames, events, labels, metric_rows)
    _write_point_cloud(package_root / "artifacts/point_clouds/workpiece.csv", _pick_sort_point_cloud())
    _write_trajectory(package_root / "artifacts/trajectories/tcp_path.csv", trajectory_rows)
    _write_readme(package_root / "README.md", "Arm pick/sort", "Deterministic simulated bin pick and sort package.")
    return package_root


def _prepare_package_dirs(root: Path) -> None:
    ensure_dir(root)
    for relative_path in ("artifacts/images", "artifacts/point_clouds", "artifacts/trajectories"):
        ensure_dir(root / relative_path)
    for image in (root / "artifacts/images").glob("*.png"):
        image.unlink()


def _positive_frame_count(frame_count: int) -> int:
    if frame_count < 1:
        raise ValueError("frame_count must be at least 1")
    return frame_count


def _write_manifest(root: Path, manifest: Mapping[str, object]) -> None:
    write_json(root / MANIFEST_FILENAME, manifest)


def _write_standard_tables(
    root: Path,
    frames: list[Mapping[str, object]],
    events: list[Mapping[str, object]],
    labels: list[Mapping[str, object]],
    metrics: list[Mapping[str, object]],
) -> None:
    write_csv_rows(root / "frames.csv", REQUIRED_TABLE_COLUMNS["frames"], frames)
    write_csv_rows(root / "events.csv", REQUIRED_TABLE_COLUMNS["events"], events)
    write_csv_rows(root / "labels.csv", REQUIRED_TABLE_COLUMNS["labels"], labels)
    write_csv_rows(root / "metrics.csv", REQUIRED_TABLE_COLUMNS["metrics"], metrics)


def _welding_manifest(frame_count: int, random_seed: int) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "package_id": f"sample_robot_welding_station_seed_{random_seed}_frames_{frame_count}",
        "scenario_type": "robot_welding_station",
        "created_at": CREATED_AT,
        "task": {"task_id": "weld_task_001", "name": "Simulated seam welding"},
        "devices": [
            {"device_id": "robot_arm_001", "type": "six_axis_robot"},
            {"device_id": "camera_front_001", "type": "rgb_camera"},
            {"device_id": "welder_001", "type": "welding_power_supply"},
        ],
        "objects": [
            {"object_id": "workpiece_001", "type": "steel_plate"},
            {"object_id": "seam_001", "type": "weld_seam"},
        ],
        "coordinate_frames": [
            {"frame_id": "station", "parent_frame_id": "", "pose_ref": ""},
            {"frame_id": "robot_base", "parent_frame_id": "station", "pose_ref": ""},
            {"frame_id": "tcp", "parent_frame_id": "robot_base", "pose_ref": ""},
            {"frame_id": "camera_front", "parent_frame_id": "station", "pose_ref": ""},
            {"frame_id": "workpiece", "parent_frame_id": "station", "pose_ref": ""},
        ],
        "timelines": [{"timeline_id": "sim_time", "unit": "s"}],
        "tables": _table_manifest(),
        "artifacts": _artifact_manifest(),
    }


def _pick_sort_manifest(frame_count: int, random_seed: int) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "package_id": f"sample_arm_pick_sort_seed_{random_seed}_frames_{frame_count}",
        "scenario_type": "arm_pick_sort",
        "created_at": CREATED_AT,
        "task": {"task_id": "pick_sort_task_001", "name": "Simulated bin pick and sort"},
        "devices": [
            {"device_id": "robot_arm_001", "type": "six_axis_robot"},
            {"device_id": "camera_front_001", "type": "rgb_camera"},
            {"device_id": "gripper_001", "type": "parallel_gripper"},
        ],
        "objects": [
            {"object_id": "part_001", "type": "target_part"},
            {"object_id": "bin_source_001", "type": "source_bin"},
            {"object_id": "bin_target_001", "type": "target_bin"},
        ],
        "coordinate_frames": [
            {"frame_id": "station", "parent_frame_id": "", "pose_ref": ""},
            {"frame_id": "robot_base", "parent_frame_id": "station", "pose_ref": ""},
            {"frame_id": "tcp", "parent_frame_id": "robot_base", "pose_ref": ""},
            {"frame_id": "camera_front", "parent_frame_id": "station", "pose_ref": ""},
            {"frame_id": "bin_source", "parent_frame_id": "station", "pose_ref": ""},
            {"frame_id": "bin_target", "parent_frame_id": "station", "pose_ref": ""},
        ],
        "timelines": [{"timeline_id": "sim_time", "unit": "s"}],
        "tables": _table_manifest(),
        "artifacts": _artifact_manifest(),
    }


def _table_manifest() -> dict[str, str]:
    return {
        "frames": "frames.csv",
        "events": "events.csv",
        "labels": "labels.csv",
        "metrics": "metrics.csv",
    }


def _artifact_manifest() -> dict[str, str]:
    return {
        "images": "artifacts/images",
        "point_clouds": "artifacts/point_clouds",
        "trajectories": "artifacts/trajectories",
    }


def _welding_events(frames: list[Mapping[str, object]], metric_rows: list[Mapping[str, object]]) -> list[dict[str, object]]:
    risk_frame_id, risk_timestamp = _max_metric_frame(metric_rows, "defect_probability")
    return [
        _event_row("event_0000", frames[0]["timestamp_s"], "start", "info", "Weld cycle started", frames[0]["frame_id"], "seam_001"),
        _event_row("event_0001", risk_timestamp, "porosity_risk", "warning", "Elevated defect probability", risk_frame_id, "seam_001"),
        _event_row("event_0002", frames[-1]["timestamp_s"], "end", "info", "Weld cycle completed", frames[-1]["frame_id"], "seam_001"),
    ]


def _pick_sort_events(frames: list[Mapping[str, object]], success: bool) -> list[dict[str, object]]:
    return [
        _event_row("event_0000", _phase_timestamp(frames, "observe"), "object_detected", "info", "Target part detected in source bin", _phase_frame_id(frames, "observe"), "part_001"),
        _event_row("event_0001", _phase_timestamp(frames, "grasp"), "grasp_attempt", "info", "Gripper closed on target part", _phase_frame_id(frames, "grasp"), "part_001"),
        _event_row(
            "event_0002",
            _phase_timestamp(frames, "place"),
            "place_success" if success else "place_failure",
            "info" if success else "warning",
            "Part placed in target bin" if success else "Part placement did not meet confidence threshold",
            _phase_frame_id(frames, "place"),
            "part_001",
        ),
    ]


def _welding_labels(frames: list[Mapping[str, object]], metric_rows: list[Mapping[str, object]]) -> list[dict[str, object]]:
    risk_frame_id, _ = _max_metric_frame(metric_rows, "defect_probability")
    return [
        {
            "label_id": "label_0000",
            "label_type": "quality",
            "target_ref": f"frame:{risk_frame_id}",
            "value": "review",
            "confidence": 0.92,
            "source": "deterministic_sim",
        },
        {
            "label_id": "label_0001",
            "label_type": "quality",
            "target_ref": f"frame:{frames[-1]['frame_id']}",
            "value": "completed",
            "confidence": 0.98,
            "source": "deterministic_sim",
        },
    ]


def _pick_sort_labels(frames: list[Mapping[str, object]], success: bool) -> list[dict[str, object]]:
    place_frame_id = _phase_frame_id(frames, "place")
    return [
        {
            "label_id": "label_0000",
            "label_type": "task_outcome",
            "target_ref": f"frame:{place_frame_id}",
            "value": "success" if success else "failure",
            "confidence": 0.94 if success else 0.72,
            "source": "deterministic_sim",
        }
    ]


def _metric_row(index: int, timestamp_s: float, metric_name: str, value: float, unit: str) -> dict[str, object]:
    return {
        "metric_id": f"metric_{index:04d}_{metric_name}",
        "timestamp_s": timestamp_s,
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "source": "deterministic_sim",
    }


def _event_row(
    event_id: str,
    timestamp_s: object,
    event_type: str,
    severity: str,
    message: str,
    related_frame_id: object,
    related_object_id: str,
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "timestamp_s": timestamp_s,
        "event_type": event_type,
        "severity": severity,
        "message": message,
        "related_frame_id": related_frame_id,
        "related_object_id": related_object_id,
    }


def _welding_phase(ratio: float) -> str:
    if ratio < 0.2:
        return "approach"
    if ratio > 0.8:
        return "finish"
    return "welding"


def _pick_sort_phase(ratio: float) -> str:
    if ratio < 0.15:
        return "observe"
    if ratio < 0.32:
        return "approach"
    if ratio < 0.48:
        return "grasp"
    if ratio < 0.72:
        return "transfer"
    if ratio < 0.9:
        return "place"
    return "finish"


def _ratio(index: int, frame_count: int) -> float:
    return index / max(frame_count - 1, 1)


def _frame_id(index: int) -> str:
    return f"frame_{index:04d}"


def _max_metric_frame(metric_rows: list[Mapping[str, object]], metric_name: str) -> tuple[str, object]:
    candidates = [row for row in metric_rows if row["metric_name"] == metric_name]
    best_index, best_row = max(enumerate(candidates), key=lambda item: float(item[1]["value"]))
    return _frame_id(best_index), best_row["timestamp_s"]


def _phase_frame_id(frames: list[Mapping[str, object]], phase: str) -> object:
    for frame in frames:
        if frame["phase"] == phase:
            return frame["frame_id"]
    return frames[-1]["frame_id"]


def _phase_timestamp(frames: list[Mapping[str, object]], phase: str) -> object:
    for frame in frames:
        if frame["phase"] == phase:
            return frame["timestamp_s"]
    return frames[-1]["timestamp_s"]


def _pick_sort_success(metric_rows: list[Mapping[str, object]]) -> bool:
    grip_values = [float(row["value"]) for row in metric_rows if row["metric_name"] == "grip_confidence"]
    object_values = [float(row["value"]) for row in metric_rows if row["metric_name"] == "object_confidence"]
    return max(grip_values, default=0.0) >= 0.68 and max(object_values, default=0.0) >= 0.72


def _welding_point_cloud(frame_count: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for x_index in range(12):
        x = round(-0.45 + x_index * 0.09, 6)
        for y_index in range(5):
            y = round(-0.08 + y_index * 0.04, 6)
            rows.append({"point_id": f"plate_{x_index:02d}_{y_index:02d}", "x": x, "y": y, "z": 0.0, "semantic": "workpiece"})
    for index in range(max(40, frame_count * 4)):
        ratio = _ratio(index, max(40, frame_count * 4))
        rows.append(
            {
                "point_id": f"seam_{index:04d}",
                "x": round(-0.4 + 0.8 * ratio, 6),
                "y": round(0.035 * math.sin(math.pi * ratio), 6),
                "z": round(0.012 + 0.003 * math.sin(2 * math.pi * ratio), 6),
                "semantic": "weld_seam",
            }
        )
    return rows


def _pick_sort_point_cloud() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, (center_x, center_y, semantic) in enumerate(((-0.28, -0.18, "source_bin"), (0.28, 0.18, "target_bin"), (-0.22, -0.12, "target_part"))):
        for point_index in range(16):
            angle = 2 * math.pi * point_index / 16
            radius = 0.055 if semantic == "target_part" else 0.12
            rows.append(
                {
                    "point_id": f"{semantic}_{point_index:02d}",
                    "x": round(center_x + radius * math.cos(angle), 6),
                    "y": round(center_y + radius * math.sin(angle), 6),
                    "z": round(0.02 * index, 6),
                    "semantic": semantic,
                }
            )
    return rows


def _write_point_cloud(path: Path, rows: list[Mapping[str, object]]) -> None:
    write_csv_rows(path, ["point_id", "x", "y", "z", "semantic"], rows)


def _write_trajectory(path: Path, rows: list[Mapping[str, object]]) -> None:
    write_csv_rows(path, ["frame_id", "timestamp_s", "x", "y", "z", "qx", "qy", "qz", "qw"], rows)


def _write_readme(path: Path, title: str, description: str) -> None:
    path.write_text(f"# {title}\n\n{description}\n", encoding="utf-8")


def _write_welding_image(path: Path, ratio: float, defect_probability: float) -> None:
    image, draw = _new_image((22, 27, 32))
    width, height = IMAGE_SIZE
    seam_points = []
    for step in range(48):
        point_ratio = step / 47
        seam_points.append((int(16 + point_ratio * (width - 32)), int(height * 0.55 - 12 * math.sin(math.pi * point_ratio))))
    draw.rectangle((10, 26, width - 10, height - 14), outline=(93, 103, 113), width=2)
    draw.line(seam_points, fill=(72, 179, 231), width=2)
    marker_x = int(16 + ratio * (width - 32))
    marker_y = int(height * 0.55 - 12 * math.sin(math.pi * ratio))
    marker_color = (239, 68, 68) if defect_probability >= 0.5 else (246, 196, 83)
    draw.ellipse((marker_x - 4, marker_y - 4, marker_x + 4, marker_y + 4), fill=marker_color)
    image.save(path)


def _write_pick_sort_image(path: Path, ratio: float, phase: str, object_confidence: float) -> None:
    image, draw = _new_image((24, 29, 34))
    width, height = IMAGE_SIZE
    source = (34, 58)
    target = (126, 38)
    draw.rectangle((12, 42, 56, 82), outline=(83, 161, 207), width=2)
    draw.rectangle((104, 22, 148, 62), outline=(125, 188, 90), width=2)
    x = int(source[0] + (target[0] - source[0]) * ratio)
    y = int(source[1] + (target[1] - source[1]) * ratio - 18 * math.sin(math.pi * ratio))
    part_color = (125, 188, 90) if phase in {"transfer", "place", "finish"} else (246, 196, 83)
    draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=part_color)
    if object_confidence >= 0.8:
        draw.arc((x - 11, y - 11, x + 11, y + 11), 20, 330, fill=(255, 255, 255), width=1)
    image.save(path)


def _new_image(background: tuple[int, int, int]):
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("Pillow is required to generate sample package images.") from exc

    image = Image.new("RGB", IMAGE_SIZE, background)
    return image, ImageDraw.Draw(image)
