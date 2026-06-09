from __future__ import annotations

import csv
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from physical_ai_data.package_io import read_csv_rows, read_json
from physical_ai_data.validation import MANIFEST_FILENAME, validate_package


def write_rrd(package_root: str | Path, output_rrd: str | Path) -> Path:
    """Write a Rerun `.rrd` recording for a validated Physical AI Package."""
    root = Path(package_root)
    output = Path(output_rrd)
    validation = validate_package(root)
    if not validation.ok:
        raise ValueError(_validation_summary(validation.errors))

    import rerun as rr

    manifest = read_json(root / MANIFEST_FILENAME)
    tables = _read_tables(root, manifest)
    scenario_type = str(manifest.get("scenario_type", "unknown"))
    package_id = str(manifest.get("package_id", "physical_ai_package"))
    base_path = f"/package/{scenario_type}"

    output.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output.with_name(f".{output.name}.tmp")

    rr.init(f"physical_ai_data_{package_id}", spawn=False)
    try:
        temp_output.unlink(missing_ok=True)
        rr.save(str(temp_output))

        _log_coordinate_frames(rr, root, manifest, base_path)
        _log_frames(rr, root, tables["frames"], base_path)
        _log_metrics(rr, tables["metrics"], base_path)
        _log_events(rr, tables["events"], base_path)
        _log_labels(rr, tables["labels"], base_path)

        rr.disconnect()
        os.replace(temp_output, output)
    except Exception:
        try:
            rr.disconnect()
        except Exception:
            pass
        temp_output.unlink(missing_ok=True)
        raise

    return output


def _validation_summary(errors: Iterable[Any]) -> str:
    return "; ".join(f"{error.code}: {error.message}" for error in errors)


def _read_tables(root: Path, manifest: Mapping[str, object]) -> dict[str, list[dict[str, str]]]:
    tables = manifest.get("tables")
    if not isinstance(tables, Mapping):
        return {"frames": [], "events": [], "labels": [], "metrics": []}
    return {
        table_name: read_csv_rows(root / str(tables[table_name]))
        for table_name in ("frames", "events", "labels", "metrics")
        if table_name in tables
    }


def _log_coordinate_frames(rr: Any, root: Path, manifest: Mapping[str, object], base_path: str) -> None:
    frames = manifest.get("coordinate_frames")
    if not isinstance(frames, list):
        return
    frame_rows = [frame for frame in frames if isinstance(frame, Mapping)]
    frame_paths = _coordinate_frame_paths(frame_rows, base_path)
    for frame in frame_rows:
        frame_id = str(frame.get("frame_id", ""))
        if not frame_id:
            continue
        pose = _read_pose(root, str(frame.get("pose_ref", "")))
        _log_static(rr, frame_paths.get(frame_id, f"{base_path}/frames/{_safe_entity_name(frame_id)}"), _transform3d(rr, pose["translation"], pose["quaternion"]))


def _coordinate_frame_paths(frames: list[Mapping[str, object]], base_path: str) -> dict[str, str]:
    by_id = {str(frame.get("frame_id", "")): frame for frame in frames if frame.get("frame_id", "")}
    resolved: dict[str, str] = {}

    def resolve(frame_id: str, visiting: set[str]) -> str:
        if frame_id in resolved:
            return resolved[frame_id]
        if frame_id in visiting:
            return f"{base_path}/frames/{_safe_entity_name(frame_id)}"
        frame = by_id.get(frame_id)
        if frame is None:
            return f"{base_path}/frames/{_safe_entity_name(frame_id)}"
        parent_id = str(frame.get("parent_frame_id", ""))
        if parent_id and parent_id in by_id:
            parent_path = resolve(parent_id, visiting | {frame_id})
            path = f"{parent_path}/{_safe_entity_name(frame_id)}"
        else:
            path = f"{base_path}/frames/{_safe_entity_name(frame_id)}"
        resolved[frame_id] = path
        return path

    for frame_id in by_id:
        resolve(frame_id, set())
    return resolved


def _log_frames(rr: Any, root: Path, frames: list[dict[str, str]], base_path: str) -> None:
    seen_point_cloud_refs: set[str] = set()
    seen_trajectory_refs: set[str] = set()
    for frame in frames:
        timestamp = _float_or_none(frame.get("timestamp_s", ""))
        if timestamp is not None:
            rr.set_time("sim_time", duration=timestamp)

        frame_id = _safe_entity_name(frame.get("frame_id", "frame"))
        frame_path = f"{base_path}/frames/{frame_id}"
        image_ref = frame.get("image_ref", "")
        if image_ref:
            _log(rr, f"{frame_path}/image", rr.Image(_read_image(root / image_ref)))
        additional_image_refs = _additional_image_refs(root, frame.get("image_refs_json", ""), image_ref)
        for camera_name, camera_image_path in additional_image_refs.items():
            try:
                image = _read_image(camera_image_path)
            except Exception:
                continue
            _log(
                rr,
                f"{frame_path}/images/{_safe_entity_name(camera_name)}",
                rr.Image(image),
            )

        point_cloud_ref = frame.get("point_cloud_ref", "")
        if point_cloud_ref and point_cloud_ref not in seen_point_cloud_refs:
            points = _read_xyz_csv(root / point_cloud_ref)
            if points:
                _log(rr, f"{frame_path}/point_cloud", rr.Points3D(points))
                seen_point_cloud_refs.add(point_cloud_ref)

        trajectory_ref = frame.get("trajectory_ref", "")
        if trajectory_ref and trajectory_ref not in seen_trajectory_refs:
            points = _read_xyz_csv(root / trajectory_ref)
            if points:
                _log(rr, f"{frame_path}/trajectory", rr.LineStrips3D([points]))
                seen_trajectory_refs.add(trajectory_ref)


def _additional_image_refs(root: Path, image_refs_json: str, primary_image_ref: str) -> dict[str, Path]:
    if not image_refs_json:
        return {}
    try:
        payload = json.loads(image_refs_json)
    except (TypeError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, Mapping):
        return {}
    image_refs: dict[str, Path] = {}
    for camera_name, image_ref in payload.items():
        if not isinstance(image_ref, str) or not image_ref or image_ref == primary_image_ref:
            continue
        image_path = _optional_package_file(root, image_ref)
        if image_path is None:
            continue
        image_refs[str(camera_name)] = image_path
    return image_refs


def _optional_package_file(root: Path, relative_ref: str) -> Path | None:
    relative_path = Path(relative_ref)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return None
    path = root / relative_path
    if not path.is_file():
        return None
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    return path


def _log_metrics(rr: Any, metrics: list[dict[str, str]], base_path: str) -> None:
    for metric in metrics:
        timestamp = _float_or_none(metric.get("timestamp_s", ""))
        value = _float_or_none(metric.get("value", ""))
        metric_name = metric.get("metric_name", "")
        if timestamp is None or value is None or not metric_name:
            continue
        rr.set_time("sim_time", duration=timestamp)
        _log(rr, f"{base_path}/metrics/{_safe_entity_name(metric_name)}", _scalars(rr, value))


def _log_events(rr: Any, events: list[dict[str, str]], base_path: str) -> None:
    for event in events:
        timestamp = _float_or_none(event.get("timestamp_s", ""))
        if timestamp is not None:
            rr.set_time("sim_time", duration=timestamp)
        text = _event_text(event)
        if hasattr(rr, "TextLog"):
            _log(rr, f"{base_path}/events", rr.TextLog(text, level=str(event.get("severity", "INFO")).upper()))
        else:
            _log(rr, f"{base_path}/events", rr.TextDocument(text))


def _log_labels(rr: Any, labels: list[dict[str, str]], base_path: str) -> None:
    for label in labels:
        label_id = _safe_entity_name(label.get("label_id", "label"))
        text = _label_text(label)
        if hasattr(rr, "TextLog"):
            _log(rr, f"{base_path}/labels/{label_id}", rr.TextLog(text, level="INFO"))
        else:
            _log(rr, f"{base_path}/labels/{label_id}", rr.TextDocument(text))


def _read_image(path: Path) -> Any:
    import numpy as np
    from PIL import Image

    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def _read_xyz_csv(path: Path) -> list[tuple[float, float, float]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or not {"x", "y", "z"} <= set(reader.fieldnames):
            return []
        points = []
        for row in reader:
            x = _float_or_none(row.get("x", ""))
            y = _float_or_none(row.get("y", ""))
            z = _float_or_none(row.get("z", ""))
            if x is not None and y is not None and z is not None:
                points.append((x, y, z))
        return points


def _read_pose(root: Path, pose_ref: str) -> dict[str, tuple[float, ...]]:
    identity = {"translation": (0.0, 0.0, 0.0), "quaternion": (0.0, 0.0, 0.0, 1.0)}
    if not pose_ref:
        return identity

    pose_path = root / pose_ref
    if pose_path.suffix.lower() == ".json":
        payload = json.loads(pose_path.read_text(encoding="utf-8"))
        if isinstance(payload, Mapping):
            return _pose_from_mapping(payload, identity)
    if pose_path.suffix.lower() == ".csv":
        rows = read_csv_rows(pose_path)
        if rows:
            return _pose_from_mapping(rows[0], identity)
    return identity


def _pose_from_mapping(payload: Mapping[str, object], default: dict[str, tuple[float, ...]]) -> dict[str, tuple[float, ...]]:
    x = _float_or_none(payload.get("x", ""))
    y = _float_or_none(payload.get("y", ""))
    z = _float_or_none(payload.get("z", ""))
    qx = _float_or_none(payload.get("qx", ""))
    qy = _float_or_none(payload.get("qy", ""))
    qz = _float_or_none(payload.get("qz", ""))
    qw = _float_or_none(payload.get("qw", ""))
    if None in (x, y, z):
        return default
    if None in (qx, qy, qz, qw):
        return {"translation": (x, y, z), "quaternion": default["quaternion"]}
    return {"translation": (x, y, z), "quaternion": (qx, qy, qz, qw)}


def _transform3d(rr: Any, translation: Iterable[float], quaternion_xyzw: tuple[float, ...]) -> Any:
    translation_values = list(translation)
    quaternion_values = list(quaternion_xyzw)
    attempts = []
    if hasattr(rr, "TransformRelation"):
        attempts.extend(
            [
                {
                    "translation": translation_values,
                    "quaternion": quaternion_values,
                    "relation": rr.TransformRelation.ChildFromParent,
                },
                {
                    "translation": translation_values,
                    "rotation": _quaternion(rr, tuple(quaternion_xyzw)),
                    "relation": rr.TransformRelation.ChildFromParent,
                },
            ]
        )
    attempts.extend(
        [
            {"translation": translation_values, "quaternion": quaternion_values},
            {"translation": translation_values, "rotation": _quaternion(rr, tuple(quaternion_xyzw))},
        ]
    )
    attempts.extend(
        [
            {"translation": translation_values, "quaternion": quaternion_values, "from_parent": True},
            {"translation": translation_values, "rotation": _quaternion(rr, tuple(quaternion_xyzw)), "from_parent": True},
        ]
    )
    last_error: TypeError | None = None
    for kwargs in attempts:
        try:
            return rr.Transform3D(**kwargs)
        except TypeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return rr.Transform3D(translation=translation_values)


def _quaternion(rr: Any, quaternion_xyzw: tuple[float, ...]) -> Any:
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


def _float_or_none(value: object) -> float | None:
    try:
        parsed = float(str(value))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _event_text(event: Mapping[str, str]) -> str:
    return (
        f"{event.get('event_id', '')} {event.get('event_type', '')}: {event.get('message', '')} "
        f"frame={event.get('related_frame_id', '')} object={event.get('related_object_id', '')}"
    ).strip()


def _label_text(label: Mapping[str, str]) -> str:
    return (
        f"{label.get('label_id', '')} {label.get('label_type', '')}: {label.get('value', '')} "
        f"target={label.get('target_ref', '')} confidence={label.get('confidence', '')} source={label.get('source', '')}"
    ).strip()


def _safe_entity_name(value: object) -> str:
    text = str(value or "unnamed").strip().replace("/", "_")
    return text or "unnamed"


def _log(rr: Any, entity_path: str, archetype: Any) -> None:
    rr.log(entity_path, archetype)


def _log_static(rr: Any, entity_path: str, archetype: Any) -> None:
    try:
        rr.log(entity_path, archetype, static=True)
    except TypeError:
        rr.log(entity_path, archetype, timeless=True)
