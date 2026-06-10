from __future__ import annotations

import math
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Sequence

from physical_ai_data.importers import ImportRequest, ImportResult
from physical_ai_data.package_io import ensure_dir, read_csv_rows, write_csv_rows, write_json
from physical_ai_data.schema import REQUIRED_TABLE_COLUMNS, SCHEMA_VERSION
from physical_ai_data.validation import validate_package

MANIFEST_FILENAME = "physical_ai_manifest.json"
SOURCE_FRAMES_REF = "artifacts/source/csv_recording_frames.csv"
CSV_RECORDING_REQUIRED_COLUMNS = ["timestamp_s", "phase", "image_path", "metric_name", "metric_value"]
CSV_RECORDING_OPTIONAL_COLUMNS = [
    "event_type",
    "event_severity",
    "event_message",
    "label_type",
    "label_value",
    "label_confidence",
]


class CsvRecordingPackageImporter:
    source_format = "csv_recording"

    def import_package(self, request: ImportRequest) -> ImportResult:
        if request.source_format != self.source_format:
            raise ValueError(f"CSV recording importer cannot handle {request.source_format}")

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
    frames_csv = source_root / "frames.csv"
    if not frames_csv.exists():
        raise ValueError("source.root must contain frames.csv")

    input_rows = read_csv_rows(frames_csv)
    _validate_columns(input_rows, frames_csv)

    package_root = Path(output_dir)
    _prepare_package(package_root)
    shutil.copyfile(frames_csv, package_root / SOURCE_FRAMES_REF)

    frame_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []

    for index, input_row in enumerate(input_rows):
        frame_id = f"frame_{index:04d}"
        timestamp_s = input_row.get("timestamp_s", "").strip()
        _finite_float(timestamp_s, "timestamp_s")

        image_ref = _copy_image(
            source_root,
            package_root,
            input_row.get("image_path", ""),
            frame_id=frame_id,
            copy_images=copy_images,
        )
        frame_rows.append(
            {
                "frame_id": frame_id,
                "timestamp_s": timestamp_s,
                "timeline": "sim_time",
                "phase": input_row.get("phase", "").strip(),
                "coordinate_frame_id": "robot_base",
                "robot_state_ref": "",
                "tcp_pose_ref": "",
                "image_ref": image_ref,
                "point_cloud_ref": "",
                "trajectory_ref": "",
            }
        )

        metric_name = input_row.get("metric_name", "").strip()
        metric_value = input_row.get("metric_value", "").strip()
        if metric_name and metric_value:
            _finite_float(metric_value, "metric_value")
            metric_rows.append(
                {
                    "metric_id": f"metric_{len(metric_rows):04d}",
                    "timestamp_s": timestamp_s,
                    "metric_name": metric_name,
                    "value": metric_value,
                    "unit": "",
                    "source": "csv_recording_import",
                }
            )

        event_type = input_row.get("event_type", "").strip()
        if event_type:
            event_rows.append(
                {
                    "event_id": f"event_{len(event_rows):04d}",
                    "timestamp_s": timestamp_s,
                    "event_type": event_type,
                    "severity": input_row.get("event_severity", "").strip() or "info",
                    "message": input_row.get("event_message", "").strip(),
                    "related_frame_id": frame_id,
                    "related_object_id": "",
                }
            )

        label_type = input_row.get("label_type", "").strip()
        label_value = input_row.get("label_value", "").strip()
        if label_type:
            confidence = input_row.get("label_confidence", "").strip() or "1.0"
            _finite_float(confidence, "label_confidence")
            label_rows.append(
                {
                    "label_id": f"label_{len(label_rows):04d}",
                    "label_type": label_type,
                    "target_ref": f"frame:{frame_id}",
                    "value": label_value,
                    "confidence": confidence,
                    "source": "csv_recording_import",
                }
            )

    converted_at = _utc_now()
    write_json(package_root / MANIFEST_FILENAME, _manifest(source_root, len(input_rows), converted_at))
    write_csv_rows(package_root / "frames.csv", REQUIRED_TABLE_COLUMNS["frames"], frame_rows)
    write_csv_rows(package_root / "events.csv", REQUIRED_TABLE_COLUMNS["events"], event_rows)
    write_csv_rows(package_root / "labels.csv", REQUIRED_TABLE_COLUMNS["labels"], label_rows)
    write_csv_rows(package_root / "metrics.csv", REQUIRED_TABLE_COLUMNS["metrics"], metric_rows)
    _write_readme(package_root / "README.md", source_root, len(input_rows))
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
        SOURCE_FRAMES_REF,
    ):
        path = root / relative_path
        if path.exists():
            path.unlink()
    for relative_path in ("artifacts/images", "artifacts/point_clouds", "artifacts/trajectories", "artifacts/source"):
        ensure_dir(root / relative_path)
    for image in (root / "artifacts/images").glob("*"):
        if image.is_file():
            image.unlink()


def _copy_image(source_root: Path, package_root: Path, image_path: str, *, frame_id: str, copy_images: bool) -> str:
    image_path = image_path.strip()
    if not image_path:
        return ""

    relative_image = _source_relative_path(image_path)
    if not copy_images:
        return ""

    source_image = source_root / relative_image
    if not source_image.exists():
        raise ValueError(f"source image does not exist: {image_path}")

    image_ref = f"artifacts/images/{frame_id}{relative_image.suffix}"
    shutil.copyfile(source_image, package_root / image_ref)
    return image_ref


def _source_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("image_path must be relative to source.root")
    return path


def _validate_columns(rows: list[dict[str, str]], frames_csv: Path) -> None:
    if rows:
        columns = set(rows[0].keys())
    else:
        columns = _read_csv_header(frames_csv)
    missing = [column for column in CSV_RECORDING_REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"frames.csv missing required columns: {', '.join(missing)}")


def _read_csv_header(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as file:
        header = file.readline().strip()
    return set(header.split(",")) if header else set()


def _manifest(source_root: Path, frame_count: int, converted_at: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "package_id": "csv_recording_fixture",
        "scenario_type": "arm_pick_sort",
        "created_at": converted_at,
        "task": {"task_id": "csv_recording_fixture", "name": "CSV recording fixture import"},
        "devices": [
            {"device_id": "robot_arm", "type": "robot"},
            {"device_id": "camera_fixture", "type": "rgb_camera"},
        ],
        "objects": [{"object_id": "recording_object", "type": "fixture_object"}],
        "coordinate_frames": [
            {"frame_id": "station", "parent_frame_id": "", "pose_ref": ""},
            {"frame_id": "robot_base", "parent_frame_id": "station", "pose_ref": ""},
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
        "source_dataset": {
            "format": "csv_recording",
            "root": str(source_root),
            "frames_csv_ref": SOURCE_FRAMES_REF,
            "frame_count": frame_count,
            "converted_at": converted_at,
        },
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
                "- Source format: CSV recording",
                f"- Source root: {source_root}",
                f"- Frames: {frame_count}",
                "",
            ]
        ),
        encoding="utf-8",
    )
