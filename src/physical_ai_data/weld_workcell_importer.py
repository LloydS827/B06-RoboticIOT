from __future__ import annotations

import csv
import math
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Sequence

from physical_ai_data.importers import ImportRequest, ImportResult
from physical_ai_data.package_io import ensure_dir, read_csv_rows, read_json, write_csv_rows, write_json
from physical_ai_data.schema import REQUIRED_TABLE_COLUMNS, SCHEMA_VERSION
from physical_ai_data.validation import validate_package

MANIFEST_FILENAME = "physical_ai_manifest.json"
SOURCE_FILES = ("job.json", "frames.csv", "process.csv", "events.csv")
OPTIONAL_SOURCE_FILES = ("review_labels.csv",)
JOB_REQUIRED_FIELDS = [
    "work_order_id",
    "station_id",
    "robot_id",
    "welder_id",
    "part_id",
    "seam_id",
    "task_name",
    "created_at",
]
FRAME_REQUIRED_COLUMNS = [
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
]
PROCESS_REQUIRED_COLUMNS = [
    "timestamp_s",
    "weld_current_a",
    "weld_voltage_v",
    "wire_feed_mpm",
    "gas_flow_lpm",
    "travel_speed_mm_s",
    "defect_probability",
]
EVENT_REQUIRED_COLUMNS = ["timestamp_s", "event_type", "severity", "message", "object_id"]
LABEL_REQUIRED_COLUMNS = ["timestamp_s", "label_type", "value", "confidence"]
TRAJECTORY_COLUMNS = ["frame_id", "timestamp_s", "x", "y", "z", "qx", "qy", "qz", "qw"]
PROCESS_METRICS = [
    ("weld_current_a", "weld_current", "A"),
    ("weld_voltage_v", "weld_voltage", "V"),
    ("wire_feed_mpm", "wire_feed", "m/min"),
    ("gas_flow_lpm", "gas_flow", "L/min"),
    ("travel_speed_mm_s", "travel_speed", "mm/s"),
    ("defect_probability", "defect_probability", "ratio"),
]


class WeldWorkcellPackageImporter:
    source_format = "weld_workcell"

    def import_package(self, request: ImportRequest) -> ImportResult:
        if request.source_format != self.source_format:
            raise ValueError(f"Weld workcell importer cannot handle {request.source_format}")

        source_root = _required_path(request.source, "root")
        copy_images = _optional_bool(request.options, "copy_images", default=True)
        package_root = _write_package(source_root, request.output_dir, copy_images=copy_images)
        validation = validate_package(package_root)
        if not validation.ok:
            raise ValueError(f"Imported package failed validation: {_format_validation_errors(validation.errors)}")
        return ImportResult(
            package_root=package_root,
            source_format=self.source_format,
            source_id=str(source_root),
            frame_count=int(validation.summary.get("frame_count", 0)),
            warnings=[f"{warning.code}: {warning.message}" for warning in validation.warnings],
        )


def _write_package(source_root: Path, output_dir: Path, *, copy_images: bool) -> Path:
    _validate_source_files(source_root)

    job = read_json(source_root / "job.json")
    _validate_job(job)
    source_frames = read_csv_rows(source_root / "frames.csv")
    source_process = read_csv_rows(source_root / "process.csv")
    source_events = read_csv_rows(source_root / "events.csv")
    has_review_labels = (source_root / "review_labels.csv").exists()
    source_labels = read_csv_rows(source_root / "review_labels.csv") if has_review_labels else []

    _validate_columns(source_frames, source_root / "frames.csv", FRAME_REQUIRED_COLUMNS)
    _validate_columns(source_process, source_root / "process.csv", PROCESS_REQUIRED_COLUMNS)
    _validate_columns(source_events, source_root / "events.csv", EVENT_REQUIRED_COLUMNS)
    if has_review_labels:
        _validate_columns(source_labels, source_root / "review_labels.csv", LABEL_REQUIRED_COLUMNS)
    _validate_rows(source_frames, source_root / "frames.csv")
    _validate_rows(source_process, source_root / "process.csv")
    _validate_rows(source_events, source_root / "events.csv")
    _validate_rows(source_labels, source_root / "review_labels.csv")
    if not source_frames:
        raise ValueError("frames.csv must contain at least one data row")

    frame_rows: list[dict[str, object]] = []
    trajectory_rows: list[dict[str, object]] = []
    image_copies: list[tuple[str, str]] = []
    for index, frame in enumerate(source_frames):
        frame_id = f"frame_{index:04d}"
        timestamp_s = frame["timestamp_s"].strip()
        _finite_float(timestamp_s, "frames.csv timestamp_s")
        image_ref = _copy_image(
            source_root,
            None,
            frame.get("image_path", ""),
            frame_id=frame_id,
            copy_images=copy_images,
        )
        if image_ref:
            image_copies.append((frame_id, frame.get("image_path", "")))
        frame_rows.append(
            {
                "frame_id": frame_id,
                "timestamp_s": timestamp_s,
                "timeline": "sim_time",
                "phase": frame.get("phase", "").strip(),
                "coordinate_frame_id": "tcp",
                "robot_state_ref": "",
                "tcp_pose_ref": "",
                "image_ref": image_ref,
                "point_cloud_ref": "",
                "trajectory_ref": "artifacts/trajectories/tcp_path.csv",
            }
        )
        tcp_values = {
            "x": frame["tcp_x"].strip(),
            "y": frame["tcp_y"].strip(),
            "z": frame["tcp_z"].strip(),
            "qx": frame["tcp_qx"].strip(),
            "qy": frame["tcp_qy"].strip(),
            "qz": frame["tcp_qz"].strip(),
            "qw": frame["tcp_qw"].strip(),
        }
        for field, value in tcp_values.items():
            _finite_float(value, field)
        trajectory_rows.append({"frame_id": frame_id, "timestamp_s": timestamp_s, **tcp_values})

    metric_rows = _metric_rows(source_process)
    event_rows = _event_rows(source_events, frame_rows, job)
    label_rows = _label_rows(source_labels, frame_rows)
    converted_at = _utc_now()

    package_root = Path(output_dir)
    _prepare_package(package_root)
    _copy_source_files(source_root, package_root)
    for frame_id, image_path in image_copies:
        _copy_image(source_root, package_root, image_path, frame_id=frame_id, copy_images=True)

    write_json(
        package_root / MANIFEST_FILENAME,
        _manifest(
            job,
            source_root,
            frame_count=len(frame_rows),
            process_count=len(source_process),
            event_count=len(source_events),
            label_count=len(label_rows),
            converted_at=converted_at,
            copy_images=copy_images,
            has_review_labels=has_review_labels,
        ),
    )
    write_csv_rows(package_root / "frames.csv", REQUIRED_TABLE_COLUMNS["frames"], frame_rows)
    write_csv_rows(package_root / "events.csv", REQUIRED_TABLE_COLUMNS["events"], event_rows)
    write_csv_rows(package_root / "labels.csv", REQUIRED_TABLE_COLUMNS["labels"], label_rows)
    write_csv_rows(package_root / "metrics.csv", REQUIRED_TABLE_COLUMNS["metrics"], metric_rows)
    write_csv_rows(package_root / "artifacts/trajectories/tcp_path.csv", TRAJECTORY_COLUMNS, trajectory_rows)
    _write_readme(package_root / "README.md", source_root, len(frame_rows))
    return package_root


def _metric_rows(source_process: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for process in source_process:
        timestamp_s = process["timestamp_s"].strip()
        _finite_float(timestamp_s, "process.csv timestamp_s")
        for source_column, metric_name, unit in PROCESS_METRICS:
            value = process[source_column].strip()
            _finite_float(value, source_column)
            rows.append(
                {
                    "metric_id": f"metric_{len(rows):04d}",
                    "timestamp_s": timestamp_s,
                    "metric_name": metric_name,
                    "value": value,
                    "unit": unit,
                    "source": "weld_workcell_process",
                }
            )
    return rows


def _event_rows(source_events: list[dict[str, str]], frames: list[dict[str, object]], job: Mapping[str, object]) -> list[dict[str, object]]:
    known_objects = {str(job["part_id"]), str(job["seam_id"])}
    rows: list[dict[str, object]] = []
    for event in source_events:
        timestamp_s = event["timestamp_s"].strip()
        timestamp = _finite_float(timestamp_s, "events.csv timestamp_s")
        object_id = event.get("object_id", "").strip()
        if object_id and object_id not in known_objects:
            raise ValueError(f"events.csv object_id must be one of {sorted(known_objects)}: {object_id}")
        rows.append(
            {
                "event_id": f"event_{len(rows):04d}",
                "timestamp_s": timestamp_s,
                "event_type": event.get("event_type", "").strip(),
                "severity": event.get("severity", "").strip() or "info",
                "message": event.get("message", "").strip(),
                "related_frame_id": _nearest_frame_id(frames, timestamp),
                "related_object_id": object_id,
            }
        )
    return rows


def _label_rows(source_labels: list[dict[str, str]], frames: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for label in source_labels:
        label_type = label.get("label_type", "").strip()
        if not label_type:
            continue
        timestamp_s = label["timestamp_s"].strip()
        timestamp = _finite_float(timestamp_s, "review_labels.csv timestamp_s")
        confidence = label.get("confidence", "").strip()
        _finite_float(confidence, "review_labels.csv confidence")
        rows.append(
            {
                "label_id": f"label_{len(rows):04d}",
                "label_type": label_type,
                "target_ref": f"frame:{_nearest_frame_id(frames, timestamp)}",
                "value": label.get("value", "").strip(),
                "confidence": confidence,
                "source": "weld_workcell_review",
            }
        )
    return rows


def _prepare_package(root: Path) -> None:
    ensure_dir(root)
    for relative_path in (
        MANIFEST_FILENAME,
        "frames.csv",
        "events.csv",
        "labels.csv",
        "metrics.csv",
        "README.md",
        "artifacts/trajectories/tcp_path.csv",
    ):
        path = root / relative_path
        if path.exists():
            path.unlink()

    for relative_path in ("artifacts/images", "artifacts/point_clouds", "artifacts/trajectories", "artifacts/source"):
        path = root / relative_path
        if path.exists():
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
        ensure_dir(path)


def _copy_source_files(source_root: Path, package_root: Path) -> None:
    for filename in (*SOURCE_FILES, *OPTIONAL_SOURCE_FILES):
        source_file = source_root / filename
        if source_file.exists():
            shutil.copyfile(source_file, package_root / "artifacts/source" / filename)


def _copy_image(source_root: Path, package_root: Path | None, image_path: str, *, frame_id: str, copy_images: bool) -> str:
    image_path = image_path.strip()
    if not image_path:
        return ""

    relative_image = _source_relative_path(image_path)
    resolved_source_root = source_root.resolve()
    source_image = (resolved_source_root / relative_image).resolve()
    if not source_image.is_relative_to(resolved_source_root):
        raise ValueError("image_path must be relative to source.root")
    if not source_image.is_file():
        raise ValueError(f"source image does not exist: {image_path}")
    if not copy_images:
        return ""

    image_ref = f"artifacts/images/{frame_id}{relative_image.suffix}"
    if package_root is not None:
        shutil.copyfile(source_image, package_root / image_ref)
    return image_ref


def _source_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("image_path must be relative to source.root")
    return path


def _manifest(
    job: Mapping[str, object],
    source_root: Path,
    *,
    frame_count: int,
    process_count: int,
    event_count: int,
    label_count: int,
    converted_at: str,
    copy_images: bool,
    has_review_labels: bool,
) -> dict[str, object]:
    work_order_id = str(job["work_order_id"])
    station_id = str(job["station_id"])
    source_dataset: dict[str, object] = {
        "format": "weld_workcell",
        "root": str(source_root),
        "job_json_ref": "artifacts/source/job.json",
        "frames_csv_ref": "artifacts/source/frames.csv",
        "process_csv_ref": "artifacts/source/process.csv",
        "events_csv_ref": "artifacts/source/events.csv",
        "frame_count": frame_count,
        "process_row_count": process_count,
        "event_count": event_count,
        "label_count": label_count,
        "image_copy_policy": "copied_to_artifacts_images_frame_id"
        if copy_images
        else "image_refs_empty_when_copy_images_false",
        "converted_at": converted_at,
    }
    if has_review_labels:
        source_dataset["review_labels_csv_ref"] = "artifacts/source/review_labels.csv"
    return {
        "schema_version": SCHEMA_VERSION,
        "package_id": f"weld_workcell_{work_order_id}_{station_id}",
        "scenario_type": "robot_welding_station",
        "created_at": str(job["created_at"]),
        "task": {"task_id": work_order_id, "name": str(job["task_name"])},
        "devices": [
            {"device_id": str(job["robot_id"]), "type": "six_axis_robot"},
            {"device_id": str(job["welder_id"]), "type": "welding_power_supply"},
            {"device_id": "camera_front", "type": "rgb_camera"},
        ],
        "objects": [
            {"object_id": str(job["part_id"]), "type": "workpiece"},
            {"object_id": str(job["seam_id"]), "type": "weld_seam"},
        ],
        "coordinate_frames": [
            {"frame_id": "station", "parent_frame_id": "", "pose_ref": ""},
            {"frame_id": "robot_base", "parent_frame_id": "station", "pose_ref": ""},
            {"frame_id": "tcp", "parent_frame_id": "robot_base", "pose_ref": ""},
            {"frame_id": "camera_front", "parent_frame_id": "station", "pose_ref": ""},
            {"frame_id": "workpiece", "parent_frame_id": "station", "pose_ref": ""},
        ],
        "timelines": [{"timeline_id": "sim_time", "unit": "s"}],
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
        "source_dataset": source_dataset,
    }


def _required_path(values: Mapping[str, object], key: str) -> Path:
    value = values.get(key)
    if not isinstance(value, (str, Path)) or not value:
        raise ValueError(f"source.{key} must be a path string or Path")
    path = Path(value)
    if not path.exists():
        raise ValueError(f"source.{key} must exist")
    if not path.is_dir():
        raise ValueError(f"source.{key} must be a directory")
    return path


def _optional_bool(values: Mapping[str, object], key: str, *, default: bool) -> bool:
    value = values.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"options.{key} must be a boolean")
    return value


def _validate_source_files(source_root: Path) -> None:
    for filename in SOURCE_FILES:
        _require_source_file(source_root, filename)


def _require_source_file(source_root: Path, filename: str) -> Path:
    path = source_root / filename
    if not path.is_file():
        raise ValueError(f"source.root must contain {filename}")
    return path


def _validate_job(job: Mapping[str, object]) -> None:
    missing = [field for field in JOB_REQUIRED_FIELDS if not job.get(field)]
    if missing:
        raise ValueError(f"job.json missing required fields: {', '.join(missing)}")


def _validate_columns(rows: list[dict[str, str]], path: Path, required_columns: Sequence[str]) -> None:
    columns = set(rows[0].keys()) if rows else _read_csv_header(path)
    missing = [column for column in required_columns if column not in columns]
    if missing:
        raise ValueError(f"{path.name} missing required columns: {', '.join(missing)}")


def _validate_rows(rows: list[dict[str, str]], path: Path) -> None:
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"{path.name} has malformed rows")


def _read_csv_header(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as file:
        try:
            return set(next(csv.reader(file)))
        except StopIteration:
            return set()


def _nearest_frame_id(frames: list[dict[str, object]], timestamp_s: float) -> str:
    nearest_id = ""
    nearest_key: tuple[float, int] | None = None
    for index, frame in enumerate(frames):
        frame_timestamp = float(str(frame.get("timestamp_s", "")))
        key = (abs(frame_timestamp - timestamp_s), index)
        if nearest_key is None or key < nearest_key:
            nearest_id = str(frame.get("frame_id", ""))
            nearest_key = key
    return nearest_id


def _finite_float(value: str, field: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def _format_validation_errors(errors: Sequence[object]) -> str:
    return "; ".join(
        f"{getattr(error, 'code', 'validation_error')}: {getattr(error, 'message', str(error))}"
        for error in errors
    )


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_readme(path: Path, source_root: Path, frame_count: int) -> None:
    ensure_dir(path.parent)
    path.write_text(
        "\n".join(
            [
                "# Physical AI Package",
                "",
                "- Source format: Weld workcell",
                f"- Source root: {source_root}",
                f"- Frames: {frame_count}",
                "",
            ]
        ),
        encoding="utf-8",
    )
