from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Sequence

from physical_ai_data.package_io import ensure_dir, write_csv_rows, write_json
from physical_ai_data.schema import REQUIRED_TABLE_COLUMNS, SCHEMA_VERSION

MANIFEST_FILENAME = "physical_ai_manifest.json"
FRAME_EXTENSIONS = ["source_frame_index", "image_refs_json"]
STATE_ACTION_COLUMNS = ["frame_id", "timestamp_s", "source_frame_index", "state_json", "action_json"]


@dataclass(frozen=True)
class LeRobotFrame:
    frame_index: int
    timestamp_s: float | None
    images: Mapping[str, Path] = field(default_factory=dict)
    state: Sequence[float] = field(default_factory=list)
    action: Sequence[float] = field(default_factory=list)


@dataclass(frozen=True)
class LeRobotEpisode:
    repo_id: str
    episode_index: int
    fps: float
    frames: Sequence[LeRobotFrame]
    task_name: str = ""
    profile: str = "fallback"
    root: Path | None = None
    local_path: Path | None = None
    features: Mapping[str, object] = field(default_factory=dict)
    stats: Mapping[str, object] = field(default_factory=dict)
    episode_metadata: Mapping[str, object] = field(default_factory=dict)
    task_metadata: Mapping[str, object] = field(default_factory=dict)


def import_lerobot_episode(
    episode: LeRobotEpisode,
    output_dir: str | Path,
    *,
    max_frames: int | None = None,
    primary_camera: str | None = None,
    copy_images: bool = True,
) -> Path:
    if max_frames is not None and max_frames <= 0:
        raise ValueError("max_frames must be positive")
    if not math.isfinite(episode.fps) or episode.fps <= 0:
        raise ValueError("fps must be positive")

    package_root = Path(output_dir)
    selected_frames = list(episode.frames[:max_frames])
    if primary_camera and selected_frames and not any(primary_camera in frame.images for frame in selected_frames):
        raise ValueError(f"primary_camera not found: {primary_camera}")
    _prepare_package(package_root)

    image_refs_by_frame: list[dict[str, str]] = []
    for index, frame in enumerate(selected_frames):
        image_refs_by_frame.append(_copy_frame_images(package_root, frame, index, copy_images=copy_images))

    frame_rows = _frame_rows(episode, selected_frames, image_refs_by_frame, primary_camera)
    event_rows = _event_rows(frame_rows)
    label_rows = _label_rows(episode, frame_rows)
    metric_rows = _metric_rows(selected_frames, frame_rows)
    state_action_rows = _state_action_rows(selected_frames, frame_rows)

    source_root = package_root / "artifacts" / "source"
    write_json(source_root / "lerobot_features.json", dict(episode.features))
    write_json(source_root / "lerobot_stats.json", dict(episode.stats))
    write_json(source_root / "lerobot_episode_metadata.json", dict(episode.episode_metadata))
    write_json(source_root / "lerobot_task_metadata.json", dict(episode.task_metadata))
    write_csv_rows(source_root / "frame_state_action.csv", STATE_ACTION_COLUMNS, state_action_rows)

    write_json(package_root / MANIFEST_FILENAME, _manifest(episode, len(selected_frames)))
    write_csv_rows(package_root / "frames.csv", REQUIRED_TABLE_COLUMNS["frames"] + FRAME_EXTENSIONS, frame_rows)
    write_csv_rows(package_root / "events.csv", REQUIRED_TABLE_COLUMNS["events"], event_rows)
    write_csv_rows(package_root / "labels.csv", REQUIRED_TABLE_COLUMNS["labels"], label_rows)
    write_csv_rows(package_root / "metrics.csv", REQUIRED_TABLE_COLUMNS["metrics"], metric_rows)
    _write_readme(package_root / "README.md", episode, len(selected_frames))
    return package_root


def _prepare_package(root: Path) -> None:
    ensure_dir(root)
    for relative_path in (
        MANIFEST_FILENAME,
        "frames.csv",
        "events.csv",
        "labels.csv",
        "metrics.csv",
        "README.md",
        "artifacts/source/lerobot_features.json",
        "artifacts/source/lerobot_stats.json",
        "artifacts/source/lerobot_episode_metadata.json",
        "artifacts/source/lerobot_task_metadata.json",
        "artifacts/source/frame_state_action.csv",
    ):
        path = root / relative_path
        if path.exists():
            path.unlink()
    ensure_dir(root / "artifacts/images")
    ensure_dir(root / "artifacts/point_clouds")
    ensure_dir(root / "artifacts/trajectories")
    ensure_dir(root / "artifacts/source")
    for image in (root / "artifacts/images").glob("*/frame_*.png"):
        image.unlink()


def _copy_frame_images(
    package_root: Path,
    frame: LeRobotFrame,
    output_index: int,
    *,
    copy_images: bool,
) -> dict[str, str]:
    del copy_images
    image_refs: dict[str, str] = {}
    for camera, source in sorted(frame.images.items()):
        image_ref = f"artifacts/images/{camera}/frame_{output_index:04d}.png"
        destination = package_root / image_ref
        ensure_dir(destination.parent)
        shutil.copyfile(source, destination)
        image_refs[str(camera)] = image_ref
    return image_refs


def _frame_rows(
    episode: LeRobotEpisode,
    frames: Sequence[LeRobotFrame],
    image_refs_by_frame: Sequence[dict[str, str]],
    primary_camera: str | None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for output_index, frame in enumerate(frames):
        image_refs = image_refs_by_frame[output_index]
        image_ref = _primary_image_ref(image_refs, primary_camera)
        rows.append(
            {
                "frame_id": _frame_id(output_index),
                "timestamp_s": _timestamp_s(frame, episode.fps),
                "timeline": "sim_time",
                "phase": "episode",
                "coordinate_frame_id": "robot_base",
                "robot_state_ref": "artifacts/source/frame_state_action.csv",
                "tcp_pose_ref": "",
                "image_ref": image_ref,
                "point_cloud_ref": "",
                "trajectory_ref": "",
                "source_frame_index": frame.frame_index,
                "image_refs_json": json.dumps(image_refs, sort_keys=True),
            }
        )
    return rows


def _event_rows(frame_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    if not frame_rows:
        return []
    return [
        _event_row("event_0000", frame_rows[0]["timestamp_s"], "episode_start", "info", "LeRobot episode import started", frame_rows[0]["frame_id"]),
        _event_row("event_0001", frame_rows[-1]["timestamp_s"], "episode_end", "info", "LeRobot episode import ended", frame_rows[-1]["frame_id"]),
    ]


def _label_rows(episode: LeRobotEpisode, frame_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    if not frame_rows:
        return []
    return [
        {
            "label_id": "label_0000",
            "label_type": "task_context",
            "target_ref": f"frame:{frame_rows[0]['frame_id']}",
            "value": episode.task_name or episode.profile,
            "confidence": 1.0,
            "source": "lerobot_import",
        }
    ]


def _metric_rows(frames: Sequence[LeRobotFrame], frame_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    previous_action: list[float] | None = None
    for index, (frame, frame_row) in enumerate(zip(frames, frame_rows, strict=True)):
        timestamp_s = frame_row["timestamp_s"]
        action_values = _finite_values(frame.action)
        state_values = _finite_values(frame.state)
        action_delta = _delta_norm(previous_action, action_values)
        rows.extend(
            [
                _metric_row(index, timestamp_s, "action_norm", _norm(action_values), "l2_norm"),
                _metric_row(index, timestamp_s, "state_norm", _norm(state_values), "l2_norm"),
                _metric_row(index, timestamp_s, "action_delta", action_delta, "l2_norm"),
                _metric_row(index, timestamp_s, "image_available", 1.0 if frame.images else 0.0, "boolean"),
            ]
        )
        previous_action = action_values
    return rows


def _state_action_rows(frames: Sequence[LeRobotFrame], frame_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for frame, frame_row in zip(frames, frame_rows, strict=True):
        rows.append(
            {
                "frame_id": frame_row["frame_id"],
                "timestamp_s": frame_row["timestamp_s"],
                "source_frame_index": frame.frame_index,
                "state_json": json.dumps(_finite_values(frame.state)),
                "action_json": json.dumps(_finite_values(frame.action)),
            }
        )
    return rows


def _manifest(episode: LeRobotEpisode, frame_count: int) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "package_id": _package_id(episode),
        "scenario_type": "open_robot_manipulation",
        "created_at": _utc_now(),
        "task": {"task_id": f"episode_{episode.episode_index}", "name": episode.task_name or "LeRobot episode"},
        "devices": _devices(episode),
        "objects": [{"object_id": "task_object", "type": "object"}],
        "coordinate_frames": [
            {"frame_id": "station", "parent_frame_id": "", "pose_ref": ""},
            {"frame_id": "robot_base", "parent_frame_id": "station", "pose_ref": ""},
        ],
        "timelines": [{"timeline_id": "sim_time", "unit": "s"}, {"timeline_id": "episode_time", "unit": "s"}],
        "tables": {
            "frames": "frames.csv",
            "events": "events.csv",
            "labels": "labels.csv",
            "metrics": "metrics.csv",
        },
        "artifacts": {
            "images": "artifacts/images",
            "point_clouds": "artifacts/point_clouds",
            "trajectories": "artifacts/trajectories",
            "source": "artifacts/source",
        },
        "source_dataset": _source_dataset(episode, frame_count),
    }


def _source_dataset(episode: LeRobotEpisode, frame_count: int) -> dict[str, object]:
    source_dataset: dict[str, object] = {
        "format": "lerobot",
        "repo_id": episode.repo_id,
        "episode_index": episode.episode_index,
        "profile": episode.profile,
        "feature_schema_ref": "artifacts/source/lerobot_features.json",
        "stats_ref": "artifacts/source/lerobot_stats.json",
        "episode_metadata_ref": "artifacts/source/lerobot_episode_metadata.json",
        "task_metadata_ref": "artifacts/source/lerobot_task_metadata.json",
        "fps": episode.fps,
        "frame_count": frame_count,
        "converted_at": _utc_now(),
    }
    if episode.root is not None:
        source_dataset["root"] = str(episode.root)
    else:
        source_dataset["local_path"] = str(episode.local_path or ".")
    return source_dataset


def _devices(episode: LeRobotEpisode) -> list[dict[str, str]]:
    cameras = sorted({camera for frame in episode.frames for camera in frame.images})
    devices = [{"device_id": "robot_arm", "type": "robot"}]
    devices.extend({"device_id": f"camera_{camera}", "type": "rgb_camera"} for camera in cameras)
    return devices


def _primary_image_ref(image_refs: Mapping[str, str], primary_camera: str | None) -> str:
    if primary_camera and primary_camera in image_refs:
        return image_refs[primary_camera]
    if not image_refs:
        return ""
    first_camera = sorted(image_refs)[0]
    return image_refs[first_camera]


def _timestamp_s(frame: LeRobotFrame, fps: float) -> float:
    if frame.timestamp_s is not None and math.isfinite(frame.timestamp_s):
        return round(float(frame.timestamp_s), 6)
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError("fps must be positive when frame timestamps are missing")
    return round(frame.frame_index / fps, 6)


def _finite_values(values: Sequence[float]) -> list[float]:
    finite_values: list[float] = []
    for value in values:
        number = float(value)
        if math.isfinite(number):
            finite_values.append(number)
    return finite_values


def _norm(values: Sequence[float]) -> float:
    return round(math.sqrt(sum(value * value for value in values)), 6)


def _delta_norm(previous: Sequence[float] | None, current: Sequence[float]) -> float:
    if previous is None:
        return 0.0
    return _norm([current_value - previous_value for previous_value, current_value in zip(previous, current, strict=False)])


def _metric_row(index: int, timestamp_s: object, metric_name: str, value: float, unit: str) -> dict[str, object]:
    return {
        "metric_id": f"metric_{index:04d}_{metric_name}",
        "timestamp_s": timestamp_s,
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "source": "lerobot_import",
    }


def _event_row(event_id: str, timestamp_s: object, event_type: str, severity: str, message: str, frame_id: object) -> dict[str, object]:
    return {
        "event_id": event_id,
        "timestamp_s": timestamp_s,
        "event_type": event_type,
        "severity": severity,
        "message": message,
        "related_frame_id": frame_id,
        "related_object_id": "",
    }


def _frame_id(index: int) -> str:
    return f"frame_{index:04d}"


def _package_id(episode: LeRobotEpisode) -> str:
    repo_id = "".join(character if character.isalnum() else "_" for character in episode.repo_id).strip("_")
    return f"lerobot_{repo_id}_episode_{episode.episode_index}_{episode.profile}"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_readme(path: Path, episode: LeRobotEpisode, frame_count: int) -> None:
    ensure_dir(path.parent)
    path.write_text(
        "\n".join(
            [
                "# Physical AI Package",
                "",
                f"- Source format: LeRobot",
                f"- Repository: {episode.repo_id}",
                f"- Episode: {episode.episode_index}",
                f"- Profile: {episode.profile}",
                f"- Frames: {frame_count}",
                "",
            ]
        ),
        encoding="utf-8",
    )
