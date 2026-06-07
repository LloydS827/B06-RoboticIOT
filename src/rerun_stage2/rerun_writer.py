"""Rerun recording writer for deterministic Stage 2 simulation packages."""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class _FrameRow:
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


_PHASE_INDEX = {"approach": 0, "welding": 1, "finish": 2}


def write_rrd(package_root: Path, output_rrd: Path) -> Path:
    """Write a Rerun `.rrd` recording for a generated simulation package."""
    import rerun as rr

    package_root = Path(package_root)
    output_rrd = Path(output_rrd)
    output_rrd.parent.mkdir(parents=True, exist_ok=True)
    temp_rrd = output_rrd.with_name(f".{output_rrd.name}.tmp")

    manifest = json.loads((package_root / "manifest.json").read_text(encoding="utf-8"))
    frames = _read_frames(package_root / "frames.csv")
    point_cloud = _read_points(package_root / "point_cloud.csv")

    seam_id = manifest.get("seam_id", "seam_001")
    seam_path = f"/station/workpiece/weld/{seam_id}"
    planned_path = _planned_seam_points(point_cloud)
    actual_path = [frame.tcp_position for frame in frames]

    rr.init("b06_stage2_sim_weld", spawn=False)
    try:
        temp_rrd.unlink(missing_ok=True)
        rr.save(str(temp_rrd))

        _log_coordinate_tree(rr, seam_path)
        _log_static_scene(rr, point_cloud, planned_path, actual_path, seam_path)

        for frame in frames:
            _set_frame_time(rr, frame)
            _log_dynamic_tcp_transform(rr, frame)
            _log(rr, "/station/robot/base/tcp/current", rr.Points3D([frame.tcp_position], radii=[0.012]))
            _log(rr, "/station/camera/front/image", rr.Image(_read_image(package_root / frame.image_file)))
            _log_process_scalars(rr, frame)
            _log_event_text(rr, frame)
        os.replace(temp_rrd, output_rrd)
    except Exception:
        temp_rrd.unlink(missing_ok=True)
        raise

    return output_rrd


def _read_frames(path: Path) -> list[_FrameRow]:
    with path.open(newline="", encoding="utf-8") as file:
        rows = []
        for row in csv.DictReader(file):
            rows.append(
                _FrameRow(
                    sim_time_s=float(row["sim_time_s"]),
                    robot_tick=int(row["robot_tick"]),
                    camera_frame=int(row["camera_frame"]),
                    weld_phase=row["weld_phase"],
                    tcp_position=(float(row["tcp_x"]), float(row["tcp_y"]), float(row["tcp_z"])),
                    tcp_quaternion=(
                        float(row["quat_x"]),
                        float(row["quat_y"]),
                        float(row["quat_z"]),
                        float(row["quat_w"]),
                    ),
                    weld_current=float(row["weld_current"]),
                    weld_voltage=float(row["weld_voltage"]),
                    wire_feed_speed=float(row["wire_feed_speed"]),
                    weld_speed=float(row["weld_speed"]),
                    defect_probability=float(row["defect_probability"]),
                    event=row["event"],
                    quality_label=row["quality_label"],
                    image_file=row["image_file"],
                )
            )
    return rows


def _read_points(path: Path) -> list[tuple[float, float, float]]:
    with path.open(newline="", encoding="utf-8") as file:
        return [(float(row["x"]), float(row["y"]), float(row["z"])) for row in csv.DictReader(file)]


def _read_image(path: Path) -> Any:
    import numpy as np
    from PIL import Image

    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def _planned_seam_points(points: Iterable[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    seam_points = [point for point in points if point[2] >= 0.01]
    return seam_points


def _log_coordinate_tree(rr: Any, seam_path: str) -> None:
    static_transforms = {
        "/station": [0.0, 0.0, 0.0],
        "/station/workpiece": [0.0, 0.0, 0.0],
        "/station/robot/base": [0.0, -0.42, 0.0],
        "/station/camera/front": [0.0, -0.72, 0.36],
        seam_path: [0.0, 0.0, 0.012],
    }
    for path, translation in static_transforms.items():
        _log_static(rr, path, _transform3d(rr, translation, (0.0, 0.0, 0.0, 1.0)))


def _log_dynamic_tcp_transform(rr: Any, frame: _FrameRow) -> None:
    _log(
        rr,
        "/station/robot/base/tcp",
        _transform3d(rr, frame.tcp_position, frame.tcp_quaternion),
    )


def _set_frame_time(rr: Any, frame: _FrameRow) -> None:
    phase_index = _PHASE_INDEX.get(frame.weld_phase, -1)
    rr.set_time("sim_time", duration=frame.sim_time_s)
    rr.set_time("robot_tick", sequence=frame.robot_tick)
    rr.set_time("camera_frame", sequence=frame.camera_frame)
    rr.set_time("weld_phase", sequence=phase_index)


def _log_static_scene(
    rr: Any,
    point_cloud: list[tuple[float, float, float]],
    planned_path: list[tuple[float, float, float]],
    actual_path: list[tuple[float, float, float]],
    seam_path: str,
) -> None:
    _log_static(rr, "/station/workpiece/point_cloud", rr.Points3D(point_cloud, radii=[0.004]))
    if planned_path:
        _log_static(rr, f"{seam_path}/planned_path", rr.LineStrips3D([planned_path], radii=[0.006]))
    if actual_path:
        _log_static(rr, f"{seam_path}/actual_tcp_path", rr.LineStrips3D([actual_path], radii=[0.005]))


def _log_process_scalars(rr: Any, frame: _FrameRow) -> None:
    _log(rr, "/process/weld_current", _scalars(rr, frame.weld_current))
    _log(rr, "/process/weld_voltage", _scalars(rr, frame.weld_voltage))
    _log(rr, "/process/wire_feed_speed", _scalars(rr, frame.wire_feed_speed))
    _log(rr, "/process/weld_speed", _scalars(rr, frame.weld_speed))
    _log(rr, "/quality/defect_probability", _scalars(rr, frame.defect_probability))


def _log_event_text(rr: Any, frame: _FrameRow) -> None:
    event = frame.event or "nominal"
    text = f"frame={frame.camera_frame} phase={frame.weld_phase} event={event} quality={frame.quality_label}"
    if hasattr(rr, "TextLog"):
        _log(rr, "/events", rr.TextLog(text, level="INFO"))
        return

    # Older Rerun SDKs expose TextDocument but not TextLog; this preserves event text content.
    _log(rr, "/events", rr.TextDocument(text))


def _transform3d(
    rr: Any,
    translation: Iterable[float],
    quaternion_xyzw: tuple[float, float, float, float],
) -> Any:
    translation_values = list(translation)
    attempts = [
        {"translation": translation_values, "quaternion": list(quaternion_xyzw), "from_parent": True},
        {"translation": translation_values, "quaternion": list(quaternion_xyzw)},
        {"translation": translation_values, "rotation": _quaternion(rr, quaternion_xyzw), "from_parent": True},
        {"translation": translation_values, "rotation": _quaternion(rr, quaternion_xyzw)},
    ]
    last_error: TypeError | None = None
    for kwargs in attempts:
        try:
            return rr.Transform3D(**kwargs)
        except TypeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return rr.Transform3D(translation=translation_values)


def _quaternion(rr: Any, quaternion_xyzw: tuple[float, float, float, float]) -> Any:
    if hasattr(rr, "Quaternion"):
        try:
            return rr.Quaternion(xyzw=list(quaternion_xyzw))
        except TypeError:
            return rr.Quaternion(list(quaternion_xyzw))
    return list(quaternion_xyzw)


def _scalars(rr: Any, value: float) -> Any:
    if hasattr(rr, "Scalars"):
        return rr.Scalars([value])
    return rr.TimeSeriesScalar(value)


def _log(rr: Any, entity_path: str, archetype: Any) -> None:
    rr.log(entity_path, archetype)


def _log_static(rr: Any, entity_path: str, archetype: Any) -> None:
    try:
        rr.log(entity_path, archetype, static=True)
    except TypeError:
        rr.log(entity_path, archetype, timeless=True)
