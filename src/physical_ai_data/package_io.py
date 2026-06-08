from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence


def read_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv_rows(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def nearest_frame_id(frames: Iterable[Mapping[str, object]], timestamp_s: float) -> str:
    nearest_id = ""
    nearest_delta: float | None = None
    for frame in frames:
        frame_id = str(frame.get("frame_id", ""))
        try:
            frame_timestamp = float(str(frame.get("timestamp_s", "")))
        except ValueError:
            continue
        delta = abs(frame_timestamp - timestamp_s)
        if nearest_delta is None or delta < nearest_delta:
            nearest_id = frame_id
            nearest_delta = delta
    return nearest_id


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
