from __future__ import annotations

import math
from pathlib import Path
from typing import Mapping

from physical_ai_data.package_io import nearest_frame_id, read_csv_rows, read_json, write_csv_rows
from physical_ai_data.schema import CANDIDATE_COLUMNS, ValidationMessage
from physical_ai_data.validation import MANIFEST_FILENAME, validate_package

EVENT_KEYWORDS = ("warning", "error", "risk", "failure", "success")
METRIC_KEYWORDS = (
    "probability",
    "confidence",
    "risk",
    "score",
    "success",
    "action_delta",
    "timestamp_gap",
    "image_missing",
)


def summarize_package(package_root: str | Path) -> dict[str, object]:
    root = Path(package_root)
    validation = validate_package(root)
    if not validation.ok:
        raise ValueError(_format_validation_errors(validation.errors))

    manifest = read_json(root / MANIFEST_FILENAME)
    tables = _read_package_tables(root, manifest)
    return {
        **validation.summary,
        "phases": sorted({row.get("phase", "") for row in tables["frames"] if row.get("phase", "")}),
        "event_types": sorted({row.get("event_type", "") for row in tables["events"] if row.get("event_type", "")}),
        "label_types": sorted({row.get("label_type", "") for row in tables["labels"] if row.get("label_type", "")}),
        "metric_names": sorted({row.get("metric_name", "") for row in tables["metrics"] if row.get("metric_name", "")}),
    }


def export_candidates(package_root: str | Path, output_csv: str | Path | None = None, min_score: float = 0.5) -> Path:
    root = Path(package_root)
    validation = validate_package(root)
    if not validation.ok:
        raise ValueError(_format_validation_errors(validation.errors))

    manifest = read_json(root / MANIFEST_FILENAME)
    tables = _read_package_tables(root, manifest)
    frames = tables["frames"]
    frame_timestamps = {row.get("frame_id", ""): row.get("timestamp_s", "") for row in frames}
    sim_time_frames = [row for row in frames if row.get("timeline", "") == "sim_time"]

    candidates = []
    candidates.extend(_event_candidates(tables["events"], sim_time_frames))
    candidates.extend(_label_candidates(tables["labels"], frame_timestamps, min_score))
    candidates.extend(_metric_candidates(tables["metrics"], sim_time_frames, min_score))

    rows = _with_candidate_ids(_merge_frame_candidates(candidates))
    output_path = Path(output_csv) if output_csv is not None else root / "derived" / "candidates.csv"
    write_csv_rows(output_path, CANDIDATE_COLUMNS, rows)
    return output_path


def _read_package_tables(root: Path, manifest: Mapping[str, object]) -> dict[str, list[dict[str, str]]]:
    tables = manifest.get("tables")
    if not isinstance(tables, Mapping):
        raise ValueError("Manifest tables must be an object")
    return {
        table_name: read_csv_rows(root / str(tables[table_name]))
        for table_name in ("frames", "events", "labels", "metrics")
    }


def _event_candidates(events: list[dict[str, str]], frames: list[dict[str, str]]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for event in events:
        haystack = " ".join(
            [
                event.get("event_type", ""),
                event.get("severity", ""),
                event.get("message", ""),
            ]
        ).lower()
        if not any(keyword in haystack for keyword in EVENT_KEYWORDS):
            continue

        timestamp_s = event.get("timestamp_s", "")
        frame_id = event.get("related_frame_id", "")
        if not frame_id:
            frame_id = _nearest_frame_id(frames, timestamp_s)
        candidates.append(
            {
                "source_type": "event",
                "source_id": event.get("event_id", ""),
                "frame_id": frame_id,
                "object_id": event.get("related_object_id", ""),
                "timestamp_s": timestamp_s,
                "reasons": _join_reason_parts(
                    [
                        f"event:{event.get('event_type', '')}",
                        f"severity:{event.get('severity', '')}",
                        event.get("message", ""),
                    ]
                ),
                "score": _event_score(event),
            }
        )
    return candidates


def _label_candidates(
    labels: list[dict[str, str]],
    frame_timestamps: Mapping[str, str],
    min_score: float,
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for label in labels:
        confidence = _parse_float(label.get("confidence", ""))
        if confidence is None or confidence < min_score:
            continue

        frame_id = ""
        object_id = ""
        target_ref = label.get("target_ref", "")
        if target_ref.startswith("frame:"):
            frame_id = target_ref.removeprefix("frame:")
        elif target_ref.startswith("object:"):
            object_id = target_ref.removeprefix("object:")
        else:
            continue

        candidates.append(
            {
                "source_type": "label",
                "source_id": label.get("label_id", ""),
                "frame_id": frame_id,
                "object_id": object_id,
                "timestamp_s": frame_timestamps.get(frame_id, ""),
                "reasons": _join_reason_parts(
                    [
                        f"label:{label.get('label_type', '')}",
                        f"value:{label.get('value', '')}",
                        f"confidence:{_format_number(confidence)}",
                    ]
                ),
                "score": confidence,
            }
        )
    return candidates


def _metric_candidates(
    metrics: list[dict[str, str]],
    frames: list[dict[str, str]],
    min_score: float,
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for metric in metrics:
        metric_name = metric.get("metric_name", "")
        value = _parse_float(metric.get("value", ""))
        if value is None or value < min_score:
            continue
        if not any(keyword in metric_name.lower() for keyword in METRIC_KEYWORDS):
            continue

        timestamp_s = metric.get("timestamp_s", "")
        candidates.append(
            {
                "source_type": "metric",
                "source_id": metric.get("metric_id", ""),
                "frame_id": _nearest_frame_id(frames, timestamp_s),
                "object_id": "",
                "timestamp_s": timestamp_s,
                "reasons": f"metric:{metric_name}={_format_number(value)}",
                "score": value,
            }
        )
    return candidates


def _merge_frame_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    frame_groups: dict[str, list[dict[str, object]]] = {}
    standalone: list[dict[str, object]] = []
    for candidate in candidates:
        frame_id = str(candidate.get("frame_id", ""))
        if frame_id:
            frame_groups.setdefault(frame_id, []).append(candidate)
        else:
            standalone.append(candidate)

    rows: list[dict[str, object]] = []
    for frame_id, group in frame_groups.items():
        if len(group) == 1:
            rows.append(group[0])
            continue

        rows.append(
            {
                "source_type": "mixed",
                "source_id": "|".join(_unique_strings(group, "source_id")),
                "frame_id": frame_id,
                "object_id": "|".join(_unique_strings(group, "object_id")),
                "timestamp_s": _first_non_empty(group, "timestamp_s"),
                "reasons": " | ".join(_unique_strings(group, "reasons")),
                "score": max(float(candidate["score"]) for candidate in group),
            }
        )
    rows.extend(standalone)
    return sorted(rows, key=_candidate_sort_key)


def _with_candidate_ids(candidates: list[dict[str, object]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, candidate in enumerate(candidates):
        rows.append(
            {
                "candidate_id": f"candidate_{index:04d}",
                "source_type": str(candidate.get("source_type", "")),
                "source_id": str(candidate.get("source_id", "")),
                "frame_id": str(candidate.get("frame_id", "")),
                "object_id": str(candidate.get("object_id", "")),
                "timestamp_s": str(candidate.get("timestamp_s", "")),
                "reasons": str(candidate.get("reasons", "")),
                "score": _format_number(float(candidate.get("score", 0.0))),
            }
        )
    return rows


def _candidate_sort_key(candidate: Mapping[str, object]) -> tuple[float, str, str, str]:
    timestamp = _parse_float(str(candidate.get("timestamp_s", "")))
    return (
        float("inf") if timestamp is None else timestamp,
        str(candidate.get("frame_id", "")),
        str(candidate.get("source_type", "")),
        str(candidate.get("source_id", "")),
    )


def _event_score(event: Mapping[str, str]) -> float:
    haystack = f"{event.get('event_type', '')} {event.get('severity', '')}".lower()
    if "error" in haystack or "failure" in haystack:
        return 0.95
    if "risk" in haystack or "warning" in haystack:
        return 0.85
    if "success" in haystack:
        return 0.75
    return 0.5


def _nearest_frame_id(frames: list[dict[str, str]], timestamp_s: str) -> str:
    timestamp = _parse_float(timestamp_s)
    if timestamp is None:
        return ""
    return nearest_frame_id(frames, timestamp)


def _parse_float(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _format_number(value: float) -> str:
    return f"{value:.6g}"


def _join_reason_parts(parts: list[str]) -> str:
    return "; ".join(part for part in parts if part)


def _unique_strings(rows: list[Mapping[str, object]], key: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for row in rows:
        value = str(row.get(key, ""))
        if not value or value in seen:
            continue
        values.append(value)
        seen.add(value)
    return values


def _first_non_empty(rows: list[Mapping[str, object]], key: str) -> str:
    for row in rows:
        value = str(row.get(key, ""))
        if value:
            return value
    return ""


def _format_validation_errors(errors: list[ValidationMessage]) -> str:
    return "; ".join(f"{error.code}: {error.message}" for error in errors)
