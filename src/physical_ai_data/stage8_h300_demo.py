from __future__ import annotations

import base64
import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


TASK_ID = "synthetic_h300_task_001"
WORK_ORDER_ID = "SYN-H300-WO-001"
JOB_WINDOW_ID = "synthetic_h300_window_001"
STATION_ID = "synthetic_h300_station_001"
ROBOT_ID = "synthetic_h300_robot_001"
WELDER_ID = "synthetic_h300_welder_001"
PART_ID = "synthetic_h300_part_001"
SEAM_ID = "synthetic_h300_seam_001"
TASK_NAME = "Stage 8 H300 synthetic demo weld window"
CREATED_AT = "2026-06-22T00:00:00Z"
GENERATED_MARKER = ".stage8_h300_synthetic_demo_generated"
RAW_ALLOWED_PATHS = {
    GENERATED_MARKER,
    "manifest.raw.json",
    "sdk/robot_state.ndjson",
    "tcp_json/hmi_task_messages.ndjson",
    "files/robot_program.lua",
    "files/robot_trajectory.json",
    "files/seam_trajectory.json",
    "files/h300_job_window_story.json",
    "files/pcl_seam_candidates.json",
    "files/model_outputs.json",
    "files/manual_corrections.json",
    "files/quality_result.json",
    "files/images/front_0000.png",
    "files/point_clouds/window_0000.pcd",
    "process/welding_process.csv",
    "events/event_log.ndjson",
}
CLEAN_ALLOWED_PATHS = {
    GENERATED_MARKER,
    "job.json",
    "frames.csv",
    "process.csv",
    "events.csv",
    "review_labels.csv",
    "images/front_0000.png",
}
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


@dataclass(frozen=True)
class Stage8H300SyntheticDemoResult:
    root: Path
    raw_root: Path
    clean_root: Path


def generate_stage8_h300_synthetic_demo(
    output_root: str | Path,
    frame_count: int = 5,
) -> Stage8H300SyntheticDemoResult:
    if frame_count < 3:
        raise ValueError("stage8 frame_count must be at least 3")

    root = Path(output_root)
    raw_root = root / "raw"
    clean_root = root / "clean" / "weld_workcell"
    result = Stage8H300SyntheticDemoResult(root=root, raw_root=raw_root, clean_root=clean_root)

    _prepare_generated_roots(
        (raw_root, RAW_ALLOWED_PATHS),
        (clean_root, CLEAN_ALLOWED_PATHS),
    )
    frames = _frames(frame_count)

    _write_raw_fixture(raw_root, frames)
    _write_clean_fixture(clean_root, frames)
    return result


def _prepare_generated_roots(*roots: tuple[Path, set[str]]) -> None:
    for root, allowed_paths in roots:
        _validate_generated_root(root, allowed_paths)
    for root, _allowed_paths in roots:
        _reset_generated_root(root)


def _validate_generated_root(root: Path, allowed_files: set[str]) -> None:
    if root.exists():
        if root.is_dir() and not root.is_symlink():
            existing_paths = {entry.relative_to(root).as_posix() for entry in root.rglob("*")}
            if not existing_paths:
                return
            allowed_paths = allowed_files | _allowed_directories(allowed_files)
            if GENERATED_MARKER not in existing_paths or existing_paths - allowed_paths:
                raise ValueError(f"refusing to overwrite non-stage8 fixture directory: {root}")
        else:
            raise ValueError(f"refusing to overwrite non-stage8 fixture directory: {root}")


def _allowed_directories(allowed_files: set[str]) -> set[str]:
    directories: set[str] = set()
    for allowed_file in allowed_files:
        parent = Path(allowed_file).parent
        while parent != Path("."):
            directories.add(parent.as_posix())
            parent = parent.parent
    return directories


def _reset_generated_root(root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)


def _write_raw_fixture(raw_root: Path, frames: list[dict[str, str]]) -> None:
    raw_refs = {
        "manifest_ref": "manifest.raw.json",
        "sdk_robot_state_ref": "sdk/robot_state.ndjson",
        "tcp_task_messages_ref": "tcp_json/hmi_task_messages.ndjson",
        "robot_program_ref": "files/robot_program.lua",
        "robot_trajectory_ref": "files/robot_trajectory.json",
        "seam_trajectory_ref": "files/seam_trajectory.json",
        "h300_job_window_story_ref": "files/h300_job_window_story.json",
        "pcl_seam_candidates_ref": "files/pcl_seam_candidates.json",
        "model_outputs_ref": "files/model_outputs.json",
        "manual_corrections_ref": "files/manual_corrections.json",
        "quality_result_ref": "files/quality_result.json",
        "front_image_ref": "files/images/front_0000.png",
        "point_cloud_ref": "files/point_clouds/window_0000.pcd",
        "welding_process_ref": "process/welding_process.csv",
        "event_log_ref": "events/event_log.ndjson",
    }
    _write_json(
        raw_root / "manifest.raw.json",
        {
            "stage": "stage8",
            "data_origin": "synthetic",
            "source_type": "h300_synthetic_demo",
            "not_production_protocol": True,
            "real_replacement_required": True,
            "task_id": TASK_ID,
            "work_order_id": WORK_ORDER_ID,
            "job_window_id": JOB_WINDOW_ID,
            "synthetic_demo_only": True,
            "window": {
                "task_id": TASK_ID,
                "job_window_id": JOB_WINDOW_ID,
                "frame_count": len(frames),
                "duration_s": 4.0,
                "work_order_id": WORK_ORDER_ID,
            },
            "synthetic_fields": [
                "work_order_id",
                "job_window_id",
                "robot_state",
                "pcl_seam_candidates",
                "model_outputs",
                "manual_corrections",
                "quality_result",
            ],
            "real_sample_required_fields": [
                "real_job_window_id",
                "real_task_id",
                "robot_controller_timestamps",
                "camera_calibration",
                "point_cloud_capture",
                "reviewer_identity",
                "quality_inspection_result",
            ],
            "importer_supported_fields": [
                "job.json",
                "frames.csv",
                "process.csv",
                "events.csv",
                "review_labels.csv",
                "images/front_0000.png",
            ],
            "source_artifact_only_fields": [
                "point_cloud",
                "pcl_seam_candidates",
                "model_outputs",
                "manual_corrections",
                "quality_result",
                "h300_job_window_story",
            ],
            "raw_zone": raw_refs,
        },
    )
    _write_ndjson(raw_root / "sdk" / "robot_state.ndjson", [_robot_state_row(index, frame) for index, frame in enumerate(frames)])
    _write_ndjson(
        raw_root / "tcp_json" / "hmi_task_messages.ndjson",
        [
            {
                "timestamp_s": frames[0]["timestamp_s"],
                "task_id": TASK_ID,
                "job_window_id": JOB_WINDOW_ID,
                "message_type": "task_started",
                "synthetic_demo_only": True,
            },
            {
                "timestamp_s": frames[-1]["timestamp_s"],
                "task_id": TASK_ID,
                "job_window_id": JOB_WINDOW_ID,
                "message_type": "task_completed",
                "synthetic_demo_only": True,
            },
        ],
    )
    _write_text(
        raw_root / "files" / "robot_program.lua",
        "\n".join(
            [
                "-- Synthetic Stage 8 H300 demo weld window program",
                f"task_id = {TASK_ID!r}",
                f"job_window_id = {JOB_WINDOW_ID!r}",
                "movej('approach')",
                "arc_on()",
                "movel('h300_demo_weld_path')",
                "arc_off()",
                "movej('cooldown')",
                "",
            ]
        ),
    )
    _write_json(raw_root / "files" / "robot_trajectory.json", {"task_id": TASK_ID, "job_window_id": JOB_WINDOW_ID, "frames": frames})
    _write_json(
        raw_root / "files" / "seam_trajectory.json",
        {
            "task_id": TASK_ID,
            "seam_id": SEAM_ID,
            "coordinate_frame": "synthetic_h300_robot_base",
            "points": [
                {"x": frame["tcp_x"], "y": frame["tcp_y"], "z": frame["tcp_z"]}
                for frame in frames
                if frame["phase"] == "weld"
            ],
        },
    )
    _write_json(raw_root / "files" / "h300_job_window_story.json", _job_window_story(frames))
    _write_json(raw_root / "files" / "pcl_seam_candidates.json", _pcl_candidates())
    _write_json(raw_root / "files" / "model_outputs.json", _model_outputs())
    _write_json(raw_root / "files" / "manual_corrections.json", _manual_corrections())
    _write_json(raw_root / "files" / "quality_result.json", _quality_result())
    _write_bytes(raw_root / "files" / "images" / "front_0000.png", TINY_PNG)
    _write_text(raw_root / "files" / "point_clouds" / "window_0000.pcd", _point_cloud())
    _write_csv(
        raw_root / "process" / "welding_process.csv",
        ["timestamp_s", "task_id", "weld_current_a", "weld_voltage_v", "travel_speed_mm_s"],
        [_process_row(frame, include_task_id=True) for frame in frames],
    )
    _write_ndjson(
        raw_root / "events" / "event_log.ndjson",
        [
            {
                "timestamp_s": "1.0000",
                "task_id": TASK_ID,
                "event_type": "arc_start",
                "severity": "info",
                "message": "Synthetic H300 arc established",
                "object_id": SEAM_ID,
            },
            {
                "timestamp_s": "3.0000",
                "task_id": TASK_ID,
                "event_type": "manual_review_required",
                "severity": "warning",
                "message": "Synthetic seam endpoint correction available for A02 evidence review",
                "object_id": SEAM_ID,
            },
        ],
    )
    _write_text(raw_root / GENERATED_MARKER, "stage8 H300 synthetic demo fixture\n")


def _write_clean_fixture(clean_root: Path, frames: list[dict[str, str]]) -> None:
    _write_json(
        clean_root / "job.json",
        {
            "work_order_id": WORK_ORDER_ID,
            "station_id": STATION_ID,
            "robot_id": ROBOT_ID,
            "welder_id": WELDER_ID,
            "part_id": PART_ID,
            "seam_id": SEAM_ID,
            "task_name": TASK_NAME,
            "created_at": CREATED_AT,
        },
    )
    _write_csv(
        clean_root / "frames.csv",
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
        frames,
    )
    _write_csv(
        clean_root / "process.csv",
        [
            "timestamp_s",
            "weld_current_a",
            "weld_voltage_v",
            "wire_feed_mpm",
            "gas_flow_lpm",
            "travel_speed_mm_s",
            "defect_probability",
        ],
        [_process_row(frame) for frame in frames],
    )
    _write_csv(
        clean_root / "events.csv",
        ["timestamp_s", "event_type", "severity", "message", "object_id"],
        [
            {
                "timestamp_s": "1.0000",
                "event_type": "arc_start",
                "severity": "info",
                "message": "Synthetic H300 arc established",
                "object_id": SEAM_ID,
            },
            {
                "timestamp_s": "3.0000",
                "event_type": "manual_review_required",
                "severity": "warning",
                "message": "Synthetic seam endpoint correction available for A02 evidence review",
                "object_id": SEAM_ID,
            },
        ],
    )
    _write_csv(
        clean_root / "review_labels.csv",
        ["timestamp_s", "label_type", "value", "confidence", "review_status", "reviewer"],
        [
            {
                "timestamp_s": "2.0000",
                "label_type": "h300_bead_quality",
                "value": "acceptable_with_endpoint_correction",
                "confidence": "0.9000",
                "review_status": "reviewed",
                "reviewer": "synthetic_stage8",
            }
        ],
    )
    _write_bytes(clean_root / "images" / "front_0000.png", TINY_PNG)
    _write_text(clean_root / GENERATED_MARKER, "stage8 H300 synthetic demo fixture\n")


def _frames(frame_count: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index in range(frame_count):
        timestamp = 4.0 * index / (frame_count - 1)
        phase = _phase(timestamp)
        rows.append(
            {
                "timestamp_s": _format_number(timestamp),
                "phase": phase,
                "tcp_x": _format_number(0.52 + index * 0.012),
                "tcp_y": _format_number(0.14 + index * 0.009),
                "tcp_z": _format_number(0.28 if phase == "weld" else 0.305),
                "tcp_qx": "0.0000",
                "tcp_qy": "0.0000",
                "tcp_qz": _format_number(0.015 * index),
                "tcp_qw": _format_number(1.0 - 0.0015 * index),
                "image_path": "images/front_0000.png",
            }
        )
    return rows


def _phase(timestamp_s: float) -> str:
    if timestamp_s < 1.0:
        return "approach"
    if timestamp_s < 3.0:
        return "weld"
    return "cooldown"


def _job_window_story(frames: list[dict[str, str]]) -> dict[str, object]:
    return {
        "stage": "stage8",
        "synthetic_demo_only": True,
        "data_origin": "synthetic",
        "real_replacement_required": True,
        "task_id": TASK_ID,
        "work_order_id": WORK_ORDER_ID,
        "job_window_id": JOB_WINDOW_ID,
        "equipment": {
            "station_id": STATION_ID,
            "robot_id": ROBOT_ID,
            "welder_id": WELDER_ID,
        },
        "workpiece": {"part_id": PART_ID, "seam_id": SEAM_ID},
        "timeline": [
            {"phase": "approach", "summary": "Synthetic robot approach to H300 demo seam"},
            {"phase": "weld", "summary": "Synthetic welding path with process metrics"},
            {"phase": "cooldown", "summary": "Synthetic cooldown and manual quality review"},
        ],
        "source_refs": {
            "clean_frames": "clean/weld_workcell/frames.csv",
            "point_cloud": "raw/files/point_clouds/window_0000.pcd",
            "pcl_candidates": "raw/files/pcl_seam_candidates.json",
            "quality_result": "raw/files/quality_result.json",
        },
        "frame_count": len(frames),
    }


def _pcl_candidates() -> dict[str, object]:
    return {
        "synthetic_demo_only": True,
        "coordinate_frame": "synthetic_h300_robot_base",
        "point_cloud_ref": "point_clouds/window_0000.pcd",
        "candidates": [
            {
                "candidate_id": "pcl_candidate_001",
                "seam_id": SEAM_ID,
                "confidence": 0.86,
                "feature_summary": {"edge_points": 4, "gap_width_mm": 1.2},
                "start_xyz_m": [0.532, 0.149, 0.28],
                "end_xyz_m": [0.568, 0.176, 0.28],
            }
        ],
    }


def _model_outputs() -> dict[str, object]:
    return {
        "synthetic_demo_only": True,
        "models": [
            {
                "model_name": "synthetic_seam_localizer",
                "version": "demo-0.1",
                "output_type": "seam_localization",
                "confidence": 0.88,
                "candidate_ref": "pcl_candidate_001",
            },
            {
                "model_name": "synthetic_quality_predictor",
                "version": "demo-0.1",
                "output_type": "quality_prediction",
                "defect_probability": 0.18,
            },
        ],
    }


def _manual_corrections() -> dict[str, object]:
    return {
        "synthetic_demo_only": True,
        "reviewer": "synthetic_stage8",
        "review_status": "reviewed",
        "a02_evidence_candidate": True,
        "corrections": [
            {
                "correction_id": "manual_correction_001",
                "reason": "Synthetic endpoint alignment correction",
                "path_point_index": 2,
                "delta_xyz_m": [0.002, -0.001, 0.0],
            }
        ],
    }


def _quality_result() -> dict[str, object]:
    return {
        "synthetic_demo_only": True,
        "inspection_source": "synthetic_visual_review",
        "overall_result": "acceptable",
        "defect_summary": [
            {
                "defect_type": "endpoint_offset_risk",
                "severity": "low",
                "review_status": "accepted_after_manual_correction",
            }
        ],
    }


def _point_cloud() -> str:
    return "\n".join(
        [
            "# .PCD v0.7 - Point Cloud Data file format",
            "VERSION 0.7",
            "FIELDS x y z intensity",
            "SIZE 4 4 4 4",
            "TYPE F F F F",
            "COUNT 1 1 1 1",
            "WIDTH 4",
            "HEIGHT 1",
            "VIEWPOINT 0 0 0 1 0 0 0",
            "POINTS 4",
            "DATA ascii",
            "0.5320 0.1490 0.2800 0.72",
            "0.5440 0.1580 0.2800 0.81",
            "0.5560 0.1670 0.2800 0.79",
            "0.5680 0.1760 0.2800 0.70",
            "",
        ]
    )


def _robot_state_row(index: int, frame: Mapping[str, str]) -> dict[str, object]:
    return {
        "timestamp_s": frame["timestamp_s"],
        "task_id": TASK_ID,
        "job_window_id": JOB_WINDOW_ID,
        "robot_id": ROBOT_ID,
        "frame_index": index,
        "phase": frame["phase"],
        "synthetic_demo_only": True,
        "tcp_pose": {
            "position_m": {
                "x": frame["tcp_x"],
                "y": frame["tcp_y"],
                "z": frame["tcp_z"],
            },
            "orientation_xyzw": {
                "x": frame["tcp_qx"],
                "y": frame["tcp_qy"],
                "z": frame["tcp_qz"],
                "w": frame["tcp_qw"],
            },
        },
    }


def _process_row(frame: Mapping[str, str], *, include_task_id: bool = False) -> dict[str, str]:
    is_weld = frame["phase"] == "weld"
    row = {
        "timestamp_s": frame["timestamp_s"],
        "weld_current_a": "132.0000" if is_weld else "0.0000",
        "weld_voltage_v": "24.1000" if is_weld else "0.0000",
        "wire_feed_mpm": "7.6000" if is_weld else "0.0000",
        "gas_flow_lpm": "15.5000",
        "travel_speed_mm_s": "5.8000" if is_weld else "0.0000",
        "defect_probability": "0.1800" if is_weld else "0.0500",
    }
    if include_task_id:
        return {
            "timestamp_s": row["timestamp_s"],
            "task_id": TASK_ID,
            "weld_current_a": row["weld_current_a"],
            "weld_voltage_v": row["weld_voltage_v"],
            "travel_speed_mm_s": row["travel_speed_mm_s"],
        }
    return row


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_ndjson(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    path.write_text(payload, encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _format_number(value: float) -> str:
    return f"{value:.4f}"
