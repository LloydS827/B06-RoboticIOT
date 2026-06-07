"""Deterministic simulated welding data for local Stage 2 evaluation."""

from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RecordingConfig:
    frame_count: int = 120
    duration_s: float = 12.0
    random_seed: int = 42
    image_width: int = 320
    image_height: int = 180
    workpiece_id: str = "wp_demo_001"
    seam_id: str = "seam_001"
    batch_id: str = "batch_stage2_demo"


@dataclass(frozen=True)
class FrameSample:
    sim_time_s: float
    robot_tick: int
    camera_frame: int
    weld_phase: str
    tcp_position: tuple[float, float, float]
    tcp_quaternion: tuple[float, float, float, float]
    weld_current: float
    weld_voltage: float
    wire_feed_speed: float
    weld_speed: float
    defect_probability: float
    event: str
    quality_label: str
    image_file: str


@dataclass(frozen=True)
class SimulationPackage:
    root: Path
    manifest_path: Path
    frames_csv: Path
    events_csv: Path
    quality_json: Path
    point_cloud_csv: Path


def generate_frames(config: RecordingConfig) -> list[FrameSample]:
    """Generate deterministic robot, camera, weld, and quality samples."""
    if config.frame_count < 1:
        return []

    rng = random.Random(config.random_seed)
    frames: list[FrameSample] = []
    last_index = max(config.frame_count - 1, 1)

    for index in range(config.frame_count):
        ratio = index / last_index
        phase = _phase_for_ratio(ratio)
        risk_peak = math.exp(-((ratio - 0.58) / 0.14) ** 2)
        defect_probability = round(min(0.95, 0.05 + 0.72 * risk_peak + rng.uniform(0.0, 0.025)), 4)

        if index == 0:
            event = "arc_start"
        elif index == config.frame_count - 1:
            event = "arc_end"
        elif defect_probability >= 0.5:
            event = "porosity_risk"
        else:
            event = ""

        x = -0.4 + 0.8 * ratio
        y = 0.035 * math.sin(math.pi * ratio)
        z = 0.065 + 0.004 * math.sin(2 * math.pi * ratio)
        weld_speed = 0.8 / config.duration_s if config.duration_s else 0.0
        current_base = 168.0 if phase == "welding" else 82.0
        voltage_base = 21.2 if phase == "welding" else 15.0

        frames.append(
            FrameSample(
                sim_time_s=round(config.duration_s * ratio, 4),
                robot_tick=int(round(config.duration_s * ratio * 1000)),
                camera_frame=index,
                weld_phase=phase,
                tcp_position=_rounded_tuple((x, y, z)),
                tcp_quaternion=(0.0, 0.0, 0.0, 1.0),
                weld_current=round(current_base + 16.0 * risk_peak + rng.uniform(-2.0, 2.0), 3),
                weld_voltage=round(voltage_base + 1.2 * risk_peak + rng.uniform(-0.2, 0.2), 3),
                wire_feed_speed=round(4.6 + 0.5 * risk_peak + rng.uniform(-0.08, 0.08), 3),
                weld_speed=round(weld_speed, 5),
                defect_probability=defect_probability,
                event=event,
                quality_label="review" if defect_probability >= 0.5 else "nominal",
                image_file=f"images/frame_{index:04d}.png",
            )
        )

    return frames


def generate_point_cloud(config: RecordingConfig) -> list[tuple[float, float, float]]:
    """Generate a small deterministic workpiece and weld seam point cloud."""
    points: list[tuple[float, float, float]] = []

    for x_index in range(12):
        x = -0.45 + x_index * 0.09
        for y_index in range(5):
            y = -0.08 + y_index * 0.04
            points.append(_rounded_tuple((x, y, 0.0)))

    seam_steps = max(40, config.frame_count * 5)
    for index in range(seam_steps):
        ratio = index / max(seam_steps - 1, 1)
        x = -0.4 + 0.8 * ratio
        y = 0.035 * math.sin(math.pi * ratio)
        z = 0.012 + 0.003 * math.sin(2 * math.pi * ratio)
        points.append(_rounded_tuple((x, y, z)))

    return points


def write_simulation_package(root: str | Path, config: RecordingConfig) -> SimulationPackage:
    root_path = Path(root)
    images_dir = root_path / "images"
    root_path.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(exist_ok=True)
    _remove_stale_frame_images(images_dir)

    frames = generate_frames(config)
    points = generate_point_cloud(config)

    manifest_path = root_path / "manifest.json"
    frames_csv = root_path / "frames.csv"
    events_csv = root_path / "events.csv"
    quality_json = root_path / "quality.json"
    point_cloud_csv = root_path / "point_cloud.csv"

    _write_manifest(manifest_path, config)
    _write_frames_csv(frames_csv, frames)
    _write_events_csv(events_csv, frames)
    _write_quality_json(quality_json, config, frames)
    _write_point_cloud_csv(point_cloud_csv, points)

    for frame in frames:
        _write_frame_image(root_path / frame.image_file, config, frame)

    return SimulationPackage(
        root=root_path,
        manifest_path=manifest_path,
        frames_csv=frames_csv,
        events_csv=events_csv,
        quality_json=quality_json,
        point_cloud_csv=point_cloud_csv,
    )


def _phase_for_ratio(ratio: float) -> str:
    if ratio < 0.2:
        return "approach"
    if ratio > 0.8:
        return "finish"
    return "welding"


def _rounded_tuple(values: Iterable[float]) -> tuple[float, float, float]:
    return tuple(round(value, 6) for value in values)  # type: ignore[return-value]


def _write_manifest(path: Path, config: RecordingConfig) -> None:
    entity_paths = [
        "/world",
        "/station",
        "/station/workpiece",
        "/station/robot/base",
        "/station/robot/base/tcp",
        "/station/camera/front",
        f"/station/workpiece/weld/{config.seam_id}",
    ]
    manifest = {
        "batch_id": config.batch_id,
        "workpiece_id": config.workpiece_id,
        "seam_id": config.seam_id,
        "coordinate_system": {
            "convention": "right-handed, Z-up, meters, quaternions xyzw",
            "world": "/world",
        },
        "entity_paths": entity_paths,
        "timelines": ["sim_time_s", "robot_tick", "camera_frame"],
    }
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _write_frames_csv(path: Path, frames: list[FrameSample]) -> None:
    fieldnames = [
        "sim_time_s",
        "robot_tick",
        "camera_frame",
        "weld_phase",
        "tcp_x",
        "tcp_y",
        "tcp_z",
        "quat_x",
        "quat_y",
        "quat_z",
        "quat_w",
        "weld_current",
        "weld_voltage",
        "wire_feed_speed",
        "weld_speed",
        "defect_probability",
        "event",
        "quality_label",
        "image_file",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for frame in frames:
            writer.writerow(
                {
                    "sim_time_s": frame.sim_time_s,
                    "robot_tick": frame.robot_tick,
                    "camera_frame": frame.camera_frame,
                    "weld_phase": frame.weld_phase,
                    "tcp_x": frame.tcp_position[0],
                    "tcp_y": frame.tcp_position[1],
                    "tcp_z": frame.tcp_position[2],
                    "quat_x": frame.tcp_quaternion[0],
                    "quat_y": frame.tcp_quaternion[1],
                    "quat_z": frame.tcp_quaternion[2],
                    "quat_w": frame.tcp_quaternion[3],
                    "weld_current": frame.weld_current,
                    "weld_voltage": frame.weld_voltage,
                    "wire_feed_speed": frame.wire_feed_speed,
                    "weld_speed": frame.weld_speed,
                    "defect_probability": frame.defect_probability,
                    "event": frame.event,
                    "quality_label": frame.quality_label,
                    "image_file": frame.image_file,
                }
            )


def _write_events_csv(path: Path, frames: list[FrameSample]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["sim_time_s", "robot_tick", "camera_frame", "event"])
        writer.writeheader()
        for frame in frames:
            if frame.event:
                writer.writerow(
                    {
                        "sim_time_s": frame.sim_time_s,
                        "robot_tick": frame.robot_tick,
                        "camera_frame": frame.camera_frame,
                        "event": frame.event,
                    }
                )


def _write_quality_json(path: Path, config: RecordingConfig, frames: list[FrameSample]) -> None:
    max_risk = max((frame.defect_probability for frame in frames), default=0.0)
    risk_frames = [frame.camera_frame for frame in frames if frame.event == "porosity_risk"]
    quality = {
        "batch_id": config.batch_id,
        "workpiece_id": config.workpiece_id,
        "seam_id": config.seam_id,
        "frame_count": len(frames),
        "max_defect_probability": max_risk,
        "risk_frames": risk_frames,
        "summary_label": "review" if risk_frames else "nominal",
    }
    path.write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")


def _write_point_cloud_csv(path: Path, points: list[tuple[float, float, float]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["x", "y", "z"])
        writer.writerows(points)


def _remove_stale_frame_images(images_dir: Path) -> None:
    for image_path in images_dir.glob("frame_*.png"):
        image_path.unlink()


def _write_frame_image(path: Path, config: RecordingConfig, frame: FrameSample) -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("Pillow is required to generate semantic weld-line simulation images.") from exc

    image = Image.new("RGB", (config.image_width, config.image_height), (26, 31, 36))
    draw = ImageDraw.Draw(image)
    seam_points = []
    for step in range(80):
        ratio = step / 79
        x = int(24 + ratio * (config.image_width - 48))
        y = int(config.image_height * 0.54 - 18 * math.sin(math.pi * ratio))
        seam_points.append((x, y))

    draw.rectangle((16, 32, config.image_width - 16, config.image_height - 28), outline=(86, 96, 106), width=2)
    draw.line(seam_points, fill=(72, 179, 231), width=3)

    frame_ratio = frame.camera_frame / max(config.frame_count - 1, 1)
    marker_x = int(24 + frame_ratio * (config.image_width - 48))
    marker_y = int(config.image_height * 0.54 - 18 * math.sin(math.pi * frame_ratio))
    marker_color = (239, 68, 68) if frame.event == "porosity_risk" else (246, 196, 83)
    draw.ellipse((marker_x - 6, marker_y - 6, marker_x + 6, marker_y + 6), fill=marker_color)

    if frame.event == "porosity_risk":
        draw.line((marker_x - 10, marker_y - 14, marker_x + 10, marker_y - 14), fill=(239, 68, 68), width=3)

    image.save(path)
