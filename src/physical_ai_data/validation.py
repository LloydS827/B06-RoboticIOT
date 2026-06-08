from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from physical_ai_data.package_io import read_csv_rows, read_json
from physical_ai_data.schema import (
    REQUIRED_MANIFEST_FIELDS,
    REQUIRED_TABLE_COLUMNS,
    SCHEMA_VERSION,
    SUPPORTED_SCENARIOS,
    ValidationMessage,
    ValidationResult,
)

MANIFEST_FILENAME = "physical_ai_manifest.json"
RECOMMENDED_ARTIFACT_DIRS = ["artifacts/images", "artifacts/point_clouds", "artifacts/trajectories"]


def validate_package(package_root: str | Path) -> ValidationResult:
    root = Path(package_root)
    errors: list[ValidationMessage] = []
    warnings: list[ValidationMessage] = []
    summary = _default_summary()

    if not root.exists():
        return ValidationResult(
            errors=[ValidationMessage("missing_package_root", f"Package root does not exist: {root}", str(root))],
            warnings=warnings,
            summary=summary,
        )

    manifest_path = root / MANIFEST_FILENAME
    if not manifest_path.exists():
        return ValidationResult(
            errors=[ValidationMessage("missing_manifest", f"Missing {MANIFEST_FILENAME}", str(manifest_path))],
            warnings=warnings,
            summary=summary,
        )

    try:
        manifest = read_json(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(
            errors=[ValidationMessage("invalid_manifest", f"Cannot parse {MANIFEST_FILENAME}: {exc}", str(manifest_path))],
            warnings=warnings,
            summary=summary,
        )

    _validate_manifest(root, manifest, errors)
    timelines = _collect_ids(manifest.get("timelines"), "timeline_id")
    coordinate_frames = _collect_ids(manifest.get("coordinate_frames"), "frame_id")
    object_ids = _collect_ids(manifest.get("objects"), "object_id")

    table_rows = _load_tables(root, manifest, errors)
    _validate_rows(root, table_rows, timelines, coordinate_frames, object_ids, errors)
    _validate_recommended_dirs(root, warnings)

    summary.update(
        {
            "package_id": manifest.get("package_id", ""),
            "scenario_type": manifest.get("scenario_type", ""),
            "frame_count": len(table_rows.get("frames", [])),
            "event_count": len(table_rows.get("events", [])),
            "label_count": len(table_rows.get("labels", [])),
            "metric_count": len(table_rows.get("metrics", [])),
            "artifact_ref_count": _count_artifact_refs(manifest, table_rows),
        }
    )
    return ValidationResult(errors=errors, warnings=warnings, summary=summary)


def _validate_manifest(root: Path, manifest: Mapping[str, object], errors: list[ValidationMessage]) -> None:
    missing_fields = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing_fields:
        errors.append(
            ValidationMessage(
                "missing_manifest_fields",
                f"Missing required manifest fields: {', '.join(missing_fields)}",
                str(root / MANIFEST_FILENAME),
            )
        )

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            ValidationMessage(
                "unsupported_schema_version",
                f"schema_version must be {SCHEMA_VERSION}",
                str(root / MANIFEST_FILENAME),
            )
        )

    scenario_type = manifest.get("scenario_type")
    if scenario_type not in SUPPORTED_SCENARIOS:
        errors.append(
            ValidationMessage(
                "unsupported_scenario_type",
                f"Unsupported scenario_type: {scenario_type}",
                str(root / MANIFEST_FILENAME),
            )
        )

    if not manifest.get("package_id", ""):
        errors.append(ValidationMessage("empty_id", "package_id must not be empty", "package_id"))
    for field, id_field in (("devices", "device_id"), ("objects", "object_id"), ("timelines", "timeline_id")):
        if field in manifest:
            _validate_manifest_list_ids(manifest.get(field), id_field, field, errors)

    timelines = manifest.get("timelines")
    timeline_ids = _collect_ids(timelines, "timeline_id")
    if "sim_time" not in timeline_ids:
        errors.append(ValidationMessage("missing_sim_time", "Manifest timelines must include sim_time", "timelines"))

    coordinate_frames = manifest.get("coordinate_frames")
    if not isinstance(coordinate_frames, list):
        errors.append(ValidationMessage("invalid_coordinate_frames", "coordinate_frames must be a list", "coordinate_frames"))
        return

    for index, frame in enumerate(coordinate_frames):
        path = f"coordinate_frames[{index}]"
        if not isinstance(frame, Mapping):
            errors.append(ValidationMessage("invalid_coordinate_frame", "Coordinate frame must be an object", path))
            continue
        missing = [field for field in ("frame_id", "parent_frame_id", "pose_ref") if field not in frame]
        if missing:
            errors.append(ValidationMessage("missing_coordinate_frame_fields", f"Missing fields: {', '.join(missing)}", path))
        frame_id = str(frame.get("frame_id", ""))
        if not frame_id:
            errors.append(ValidationMessage("empty_id", "coordinate_frames.frame_id must not be empty", path))
        pose_ref = str(frame.get("pose_ref", ""))
        _validate_file_ref(root, pose_ref, f"{path}.pose_ref", errors)


def _load_tables(
    root: Path,
    manifest: Mapping[str, object],
    errors: list[ValidationMessage],
) -> dict[str, list[dict[str, str]]]:
    table_rows: dict[str, list[dict[str, str]]] = {name: [] for name in REQUIRED_TABLE_COLUMNS}
    table_paths: dict[str, Path] = {}
    tables = manifest.get("tables")
    if not isinstance(tables, Mapping):
        errors.append(ValidationMessage("invalid_tables", "Manifest tables must be an object", "tables"))
        return table_rows

    for table_name, table_ref in tables.items():
        if not isinstance(table_ref, str) or not table_ref:
            errors.append(
                ValidationMessage(
                    "missing_table",
                    f"Manifest tables.{table_name} must be a non-empty path",
                    f"tables.{table_name}",
                )
            )
            continue
        table_path = _resolve_package_relative_ref(root, table_ref, f"tables.{table_name}", errors, "invalid_table_ref")
        if table_path is None:
            continue
        table_paths[str(table_name)] = table_path
        if not table_path.exists():
            errors.append(ValidationMessage("missing_table", f"Missing table file: {table_ref}", table_ref))

    for table_name, required_columns in REQUIRED_TABLE_COLUMNS.items():
        table_ref = tables.get(table_name)
        if not isinstance(table_ref, str) or not table_ref:
            if table_name not in tables:
                errors.append(ValidationMessage("missing_table", f"Manifest tables.{table_name} is required", f"tables.{table_name}"))
            continue
        table_path = table_paths.get(table_name)
        if table_path is None or not table_path.exists():
            continue
        rows = read_csv_rows(table_path)
        _validate_csv_rows(table_ref, rows, errors)
        table_rows[table_name] = rows
        columns = set(rows[0].keys()) if rows else _read_csv_header(table_path)
        missing_columns = [column for column in required_columns if column not in columns]
        if missing_columns:
            errors.append(
                ValidationMessage(
                    "missing_table_columns",
                    f"{table_ref} is missing required columns: {', '.join(missing_columns)}",
                    table_ref,
                )
            )
    return table_rows


def _validate_rows(
    root: Path,
    table_rows: Mapping[str, list[dict[str, str]]],
    timelines: set[str],
    coordinate_frames: set[str],
    object_ids: set[str],
    errors: list[ValidationMessage],
) -> None:
    for row_index, frame in enumerate(table_rows.get("frames", []), start=1):
        path = f"frames.csv:{row_index}"
        _validate_non_empty_id(frame, "frame_id", path, errors)
        _validate_numeric(frame, "timestamp_s", "frames.csv", row_index, errors)
        if frame.get("timeline", "") not in timelines:
            errors.append(ValidationMessage("unknown_timeline", f"frames.csv row {row_index} references unknown timeline", path))
        if frame.get("coordinate_frame_id", "") not in coordinate_frames:
            errors.append(
                ValidationMessage("unknown_coordinate_frame", f"frames.csv row {row_index} references unknown coordinate_frame_id", path)
            )
        for field, value in frame.items():
            if isinstance(field, str) and field.endswith("_ref"):
                _validate_file_ref(root, value, f"{path}.{field}", errors)

    frame_ids = {row.get("frame_id", "") for row in table_rows.get("frames", [])}
    for row_index, event in enumerate(table_rows.get("events", []), start=1):
        path = f"events.csv:{row_index}"
        _validate_non_empty_id(event, "event_id", path, errors)
        _validate_numeric(event, "timestamp_s", "events.csv", row_index, errors)
        related_frame_id = event.get("related_frame_id", "")
        if related_frame_id and related_frame_id not in frame_ids:
            errors.append(ValidationMessage("unknown_frame_id", f"events.csv row {row_index} references unknown related_frame_id", path))
        related_object_id = event.get("related_object_id", "")
        if related_object_id and related_object_id not in object_ids:
            errors.append(ValidationMessage("unknown_object_id", f"events.csv row {row_index} references unknown related_object_id", path))

    for row_index, label in enumerate(table_rows.get("labels", []), start=1):
        path = f"labels.csv:{row_index}"
        _validate_non_empty_id(label, "label_id", path, errors)
        target_ref = label.get("target_ref", "")
        if target_ref.startswith("frame:"):
            if target_ref.removeprefix("frame:") not in frame_ids:
                errors.append(ValidationMessage("unknown_frame_id", f"labels.csv row {row_index} references unknown {target_ref}", path))
        elif target_ref.startswith("object:"):
            if target_ref.removeprefix("object:") not in object_ids:
                errors.append(ValidationMessage("unknown_object_id", f"labels.csv row {row_index} references unknown {target_ref}", path))
        else:
            errors.append(ValidationMessage("invalid_target_ref", f"labels.csv row {row_index} target_ref must start with frame: or object:", path))

    for row_index, metric in enumerate(table_rows.get("metrics", []), start=1):
        path = f"metrics.csv:{row_index}"
        _validate_non_empty_id(metric, "metric_id", path, errors)
        _validate_numeric(metric, "timestamp_s", "metrics.csv", row_index, errors)


def _validate_recommended_dirs(root: Path, warnings: list[ValidationMessage]) -> None:
    for relative_path in RECOMMENDED_ARTIFACT_DIRS:
        if not (root / relative_path).is_dir():
            warnings.append(
                ValidationMessage(
                    "missing_recommended_artifact_dir",
                    f"Recommended artifact directory is missing: {relative_path}",
                    relative_path,
                )
            )


def _validate_non_empty_id(row: Mapping[str, str], field: str, path: str, errors: list[ValidationMessage]) -> None:
    if not row.get(field, ""):
        errors.append(ValidationMessage("empty_id", f"{field} must not be empty", path))


def _validate_manifest_list_ids(value: object, id_field: str, path: str, errors: list[ValidationMessage]) -> None:
    if not isinstance(value, list):
        errors.append(ValidationMessage("invalid_manifest_list", f"{path} must be a list", path))
        return
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            errors.append(ValidationMessage("invalid_manifest_entry", f"{path}[{index}] must be an object", f"{path}[{index}]"))
            continue
        if not item.get(id_field, ""):
            errors.append(ValidationMessage("empty_id", f"{path}[{index}].{id_field} must not be empty", f"{path}[{index}]"))


def _validate_numeric(
    row: Mapping[str, str],
    field: str,
    table_name: str,
    row_index: int,
    errors: list[ValidationMessage],
) -> None:
    try:
        float(row.get(field, ""))
    except (TypeError, ValueError):
        errors.append(ValidationMessage("invalid_timestamp", f"{table_name} row {row_index} has invalid {field}", f"{table_name}:{row_index}"))


def _validate_file_ref(root: Path, ref: object, path: str, errors: list[ValidationMessage]) -> None:
    if not isinstance(ref, str) or not ref:
        return
    candidate = _resolve_package_relative_ref(root, ref, path, errors, "invalid_artifact_ref")
    if candidate is None:
        return

    if not candidate.exists():
        errors.append(ValidationMessage("missing_artifact_ref", f"Missing artifact referenced by {path}: {ref}", path))


def _resolve_package_relative_ref(
    root: Path,
    ref: str,
    path: str,
    errors: list[ValidationMessage],
    error_code: str,
) -> Path | None:
    ref_path = Path(ref)
    if ref_path.is_absolute():
        errors.append(ValidationMessage(error_code, f"{path} must be package-relative, got absolute path: {ref}", path))
        return None

    if ".." in ref_path.parts:
        errors.append(
            ValidationMessage(
                error_code,
                f"{path} must stay within package root and not use path traversal: {ref}",
                path,
            )
        )
        return None

    root_resolved = root.resolve()
    candidate = (root / ref_path).resolve(strict=False)
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        errors.append(
            ValidationMessage(
                error_code,
                f"{path} must stay within package root and not use path traversal: {ref}",
                path,
            )
        )
        return None
    return candidate


def _collect_ids(value: object, id_field: str) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item.get(id_field, "")) for item in value if isinstance(item, Mapping) and item.get(id_field, "")}


def _default_summary() -> dict[str, object]:
    return {
        "package_id": "",
        "scenario_type": "",
        "frame_count": 0,
        "event_count": 0,
        "label_count": 0,
        "metric_count": 0,
        "artifact_ref_count": 0,
    }


def _validate_csv_rows(table_ref: str, rows: list[dict[str, str]], errors: list[ValidationMessage]) -> None:
    for row_index, row in enumerate(rows, start=1):
        if None in row:
            errors.append(
                ValidationMessage(
                    "malformed_csv_row",
                    f"{table_ref} row {row_index} has more values than header columns",
                    f"{table_ref}:{row_index}",
                )
            )


def _count_artifact_refs(manifest: Mapping[str, object], table_rows: Mapping[str, list[dict[str, str]]]) -> int:
    count = 0
    for frame in _as_list(manifest.get("coordinate_frames")):
        if isinstance(frame, Mapping) and frame.get("pose_ref", ""):
            count += 1
    for rows in table_rows.values():
        for row in rows:
            count += sum(1 for field, value in row.items() if isinstance(field, str) and field.endswith("_ref") and value)
    return count


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _read_csv_header(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as file:
        header = file.readline().strip()
    return set(header.split(",")) if header else set()
