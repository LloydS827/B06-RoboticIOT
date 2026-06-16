from __future__ import annotations

import base64
import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


TASK_ID = "sim_task_stage7_001"
WORK_ORDER_ID = "SIM-WO-STAGE7-001"
STATION_ID = "sim_station_stage7"
ROBOT_ID = "sim_robot_001"
WELDER_ID = "sim_welder_001"
PART_ID = "sim_part_001"
SEAM_ID = "sim_seam_001"
TASK_NAME = "Stage 7 simulated weld window"
CREATED_AT = "2026-06-16T00:00:00Z"
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


@dataclass(frozen=True)
class Stage7SimWindowResult:
    root: Path
    raw_root: Path
    clean_root: Path


def generate_stage7_sim_weld_window(output_root: str | Path, frame_count: int = 5) -> Stage7SimWindowResult:
    if frame_count < 3:
        raise ValueError("stage7 frame_count must be at least 3")

    root = Path(output_root) / "stage7_window"
    raw_root = root / "raw"
    clean_root = root / "clean" / "weld_workcell"
    result = Stage7SimWindowResult(root=root, raw_root=raw_root, clean_root=clean_root)

    _prepare_generated_root(raw_root)
    _prepare_generated_root(clean_root)
    frames = _frames(frame_count)

    _write_raw_fixture(raw_root, frames)
    _write_clean_fixture(clean_root, frames)
    return result


def _prepare_generated_root(root: Path) -> None:
    if root.exists():
        if root.is_dir() and not root.is_symlink():
            shutil.rmtree(root)
        else:
            root.unlink()
    root.mkdir(parents=True, exist_ok=True)


def _write_raw_fixture(raw_root: Path, frames: list[dict[str, str]]) -> None:
    raw_refs = {
        "manifest_ref": "manifest.raw.json",
        "sdk_robot_state_ref": "sdk/robot_state.ndjson",
        "tcp_task_messages_ref": "tcp_json/hmi_task_messages.ndjson",
        "robot_program_ref": "files/robot_program.lua",
        "robot_trajectory_ref": "files/robot_trajectory.json",
        "seam_trajectory_ref": "files/seam_trajectory.json",
        "front_image_ref": "files/images/front_0000.png",
        "welding_process_ref": "process/welding_process.csv",
        "event_log_ref": "events/event_log.ndjson",
    }
    _write_json(
        raw_root / "manifest.raw.json",
        {
            "stage": "stage7",
            "source_type": "simulated",
            "not_production_protocol": True,
            "task_id": TASK_ID,
            "desensitization": {"status": "synthetic"},
            "window": {
                "task_id": TASK_ID,
                "frame_count": len(frames),
                "duration_s": 4.0,
                "work_order_id": WORK_ORDER_ID,
            },
            "assumptions": {
                "timestamp_source": "sim_time_seconds",
                "units": {
                    "tcp_position": "m",
                    "tcp_orientation": "quaternion_xyzw",
                    "weld_current": "A",
                    "weld_voltage": "V",
                    "travel_speed": "mm/s",
                },
                "coordinate_frames": {
                    "robot_base": "simulated_station_frame",
                    "tcp": "relative_to_robot_base",
                    "camera_front": "simulated_fixed_camera",
                },
            },
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
                "message_type": "task_started",
                "task_name": TASK_NAME,
            },
            {
                "timestamp_s": frames[-1]["timestamp_s"],
                "task_id": TASK_ID,
                "message_type": "task_completed",
                "task_name": TASK_NAME,
            },
        ],
    )
    _write_text(
        raw_root / "files" / "robot_program.lua",
        "\n".join(
            [
                "-- Synthetic Stage 7 weld window program",
                f"task_id = {TASK_ID!r}",
                "movej('approach')",
                "arc_on()",
                "movel('weld_path')",
                "arc_off()",
                "movej('cooldown')",
                "",
            ]
        ),
    )
    _write_json(raw_root / "files" / "robot_trajectory.json", {"task_id": TASK_ID, "frames": frames})
    _write_json(
        raw_root / "files" / "seam_trajectory.json",
        {
            "task_id": TASK_ID,
            "seam_id": SEAM_ID,
            "points": [
                {"x": frame["tcp_x"], "y": frame["tcp_y"], "z": frame["tcp_z"]}
                for frame in frames
                if frame["phase"] == "weld"
            ],
        },
    )
    _write_bytes(raw_root / "files" / "images" / "front_0000.png", TINY_PNG)
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
                "message": "Synthetic arc established",
                "object_id": SEAM_ID,
            },
            {
                "timestamp_s": "3.0000",
                "task_id": TASK_ID,
                "event_type": "cooldown_risk_review",
                "severity": "warning",
                "message": "Synthetic cooldown risk marker for candidate export",
                "object_id": SEAM_ID,
            },
        ],
    )


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
                "message": "Synthetic arc established",
                "object_id": SEAM_ID,
            },
            {
                "timestamp_s": "3.0000",
                "event_type": "cooldown_risk_review",
                "severity": "warning",
                "message": "Synthetic cooldown risk marker for candidate export",
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
                "label_type": "bead_quality",
                "value": "acceptable",
                "confidence": "0.91",
                "review_status": "reviewed",
                "reviewer": "synthetic_stage7",
            }
        ],
    )
    _write_bytes(clean_root / "images" / "front_0000.png", TINY_PNG)


def _frames(frame_count: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index in range(frame_count):
        timestamp = 4.0 * index / (frame_count - 1)
        phase = _phase(timestamp)
        rows.append(
            {
                "timestamp_s": _format_number(timestamp),
                "phase": phase,
                "tcp_x": _format_number(0.42 + index * 0.015),
                "tcp_y": _format_number(0.08 + index * 0.01),
                "tcp_z": _format_number(0.31 if phase != "weld" else 0.29),
                "tcp_qx": "0.0000",
                "tcp_qy": "0.0000",
                "tcp_qz": _format_number(0.02 * index),
                "tcp_qw": _format_number(1.0 - 0.002 * index),
                "image_path": "images/front_0000.png" if index == 0 else "",
            }
        )
    return rows


def _phase(timestamp_s: float) -> str:
    if timestamp_s < 1.0:
        return "approach"
    if timestamp_s < 3.0:
        return "weld"
    return "cooldown"


def _robot_state_row(index: int, frame: Mapping[str, str]) -> dict[str, object]:
    return {
        "timestamp_s": frame["timestamp_s"],
        "task_id": TASK_ID,
        "robot_id": ROBOT_ID,
        "frame_index": index,
        "phase": frame["phase"],
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
        "weld_current_a": "128.0000" if is_weld else "0.0000",
        "weld_voltage_v": "23.4000" if is_weld else "0.0000",
        "wire_feed_mpm": "7.2000" if is_weld else "0.0000",
        "gas_flow_lpm": "15.0000",
        "travel_speed_mm_s": "5.5000" if is_weld else "0.0000",
        "defect_probability": "0.6200" if frame["phase"] == "cooldown" else "0.0800",
    }
    if include_task_id:
        return {"timestamp_s": row["timestamp_s"], "task_id": TASK_ID, **{key: row[key] for key in ("weld_current_a", "weld_voltage_v", "travel_speed_mm_s")}}
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
