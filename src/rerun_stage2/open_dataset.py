"""Prepare a small open robot dataset comparison sample."""

from __future__ import annotations

import csv
import json
import shutil
import urllib.request
from pathlib import Path
from typing import Any


PUSHT_PARQUET_URL = (
    "https://huggingface.co/datasets/lerobot/pusht/resolve/"
    "aa68ad28f20ffd4c4b6fc0af7fde6e29d003bfdf/data/train-00000-of-00001.parquet"
)
PUSHT_PARQUET_NAME = "lerobot_pusht_train-00000-of-00001.parquet"


def write_open_robot_sample(root: Path) -> Path:
    root = Path(root)
    source_dir = root / "source"
    images_dir = root / "images"
    root.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(exist_ok=True)
    images_dir.mkdir(exist_ok=True)

    source_attempt: dict[str, Any] = {"url": PUSHT_PARQUET_URL, "status": "not_available"}
    schema_fields: list[str] = []
    field_mapping: dict[str, str | None] = {"index": None, "timestamp": None, "state": None, "action": None}
    row_count = 0
    rows: list[dict[str, Any]] = []

    try:
        parquet_path = source_dir / PUSHT_PARQUET_NAME
        _download_file(PUSHT_PARQUET_URL, parquet_path)
        rows, schema_fields, field_mapping, row_count = _read_parquet_rows(parquet_path)
        source_attempt.update(
            {
                "status": "downloaded",
                "saved_path": str(parquet_path.relative_to(root)),
            }
        )
    except Exception as exc:
        source_attempt.update(
            {
                "status": "not_available",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
        )
        rows = _placeholder_rows()
        row_count = len(rows)

    _write_frames_csv(root / "frames.csv", rows)
    _write_images(images_dir, rows)
    _write_metadata(
        root / "source_metadata.json",
        source_attempt=source_attempt,
        schema_fields=schema_fields,
        field_mapping=field_mapping,
        row_count=row_count,
    )
    return root


def _download_file(url: str, destination: Path, timeout_s: float = 10.0) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "b06-stage2-open-dataset-probe/1.0"})
    temp_path = destination.with_name(f".{destination.name}.tmp")
    temp_path.unlink(missing_ok=True)
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response, temp_path.open("wb") as output:
            shutil.copyfileobj(response, output)
        temp_path.replace(destination)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _read_parquet_rows(path: Path) -> tuple[list[dict[str, Any]], list[str], dict[str, str | None], int]:
    import pyarrow.parquet as pq

    parquet_file = pq.ParquetFile(path)
    schema_fields = parquet_file.schema_arrow.names
    batches = parquet_file.iter_batches(batch_size=32)
    batch = next(batches, None)
    if batch is None:
        return [], schema_fields, {"index": None, "timestamp": None, "state": None, "action": None}, 0

    table = batch.to_pydict()
    mapping = _choose_fields(parquet_file.schema_arrow, table)
    row_count = batch.num_rows
    rows = []
    for row_index in range(row_count):
        rows.append(
            {
                "source_index": _value_at(table, mapping["index"], row_index, row_index),
                "timestamp": _value_at(table, mapping["timestamp"], row_index, ""),
                "state_field": mapping["state"] or "",
                "state_value": _cell_value(_value_at(table, mapping["state"], row_index, "")),
                "action_field": mapping["action"] or "",
                "action_value": _cell_value(_value_at(table, mapping["action"], row_index, "")),
                "image_file": f"images/open_robot_{row_index % 4:04d}.png",
                "source_status": "downloaded",
            }
        )
    return rows, schema_fields, mapping, row_count


def _choose_fields(schema: Any, table: dict[str, list[Any]]) -> dict[str, str | None]:
    numeric_fields = [_field.name for _field in schema if _is_numeric_like(_field.type)]
    names = list(table.keys())
    return {
        "index": _first_match(names, ("index", "frame_index", "episode_index")) or _first_numeric(numeric_fields),
        "timestamp": _first_match(names, ("timestamp", "time", "task_index", "frame_index")),
        "state": _first_match(numeric_fields, ("observation.state", "state", "observation")),
        "action": _first_match(numeric_fields, ("action", "control", "command")),
    }


def _is_numeric_like(arrow_type: Any) -> bool:
    import pyarrow.types as pat

    if pat.is_integer(arrow_type) or pat.is_floating(arrow_type):
        return True
    if pat.is_list(arrow_type) or pat.is_large_list(arrow_type) or pat.is_fixed_size_list(arrow_type):
        return pat.is_integer(arrow_type.value_type) or pat.is_floating(arrow_type.value_type)
    return False


def _first_match(names: list[str], needles: tuple[str, ...]) -> str | None:
    lowered = {name.lower(): name for name in names}
    for needle in needles:
        if needle in lowered:
            return lowered[needle]
    for needle in needles:
        for name in names:
            if needle in name.lower():
                return name
    return None


def _first_numeric(names: list[str]) -> str | None:
    return names[0] if names else None


def _value_at(table: dict[str, list[Any]], field: str | None, index: int, default: Any) -> Any:
    if field is None:
        return default
    return table[field][index]


def _cell_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return json.dumps(value)
    if value is None:
        return ""
    return str(value)


def _placeholder_rows() -> list[dict[str, Any]]:
    return [
        {
            "source_index": index,
            "timestamp": "",
            "state_field": "",
            "state_value": "real open-source comparison not completed",
            "action_field": "",
            "action_value": "",
            "image_file": f"images/open_robot_{index:04d}.png",
            "source_status": "not_available",
        }
        for index in range(4)
    ]


def _write_frames_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "source_index",
        "timestamp",
        "state_field",
        "state_value",
        "action_field",
        "action_value",
        "image_file",
        "source_status",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_images(images_dir: Path, rows: list[dict[str, Any]]) -> None:
    from PIL import Image, ImageDraw

    image_names = sorted({Path(str(row["image_file"])).name for row in rows})[:4]
    for image_index, image_name in enumerate(image_names or ["open_robot_0000.png"]):
        image = Image.new("RGB", (240, 160), (32, 37, 43))
        draw = ImageDraw.Draw(image)
        draw.rectangle((18, 92, 222, 122), outline=(82, 92, 102), width=2)
        draw.line((34, 108, 88, 78, 146, 82, 202, 58), fill=(76, 195, 138), width=4)
        marker_x = 48 + image_index * 40
        draw.ellipse((marker_x - 7, 72, marker_x + 7, 86), fill=(245, 173, 66))
        image.save(images_dir / image_name)


def _write_metadata(
    path: Path,
    *,
    source_attempt: dict[str, Any],
    schema_fields: list[str],
    field_mapping: dict[str, str | None],
    row_count: int,
) -> None:
    metadata = {
        "purpose": "stage2_open_robot_comparison",
        "robot_family": "LeRobot PushT planar manipulation",
        "candidate_sources": [
            {
                "name": "LeRobot pusht dataset",
                "url": "https://huggingface.co/datasets/lerobot/pusht",
            },
            {
                "name": "PickNik UR10e welding demo",
                "url": "https://github.com/PickNikRobotics/UR10e_welding_demo",
            },
            {
                "name": "LeRobot project/datasets",
                "url": "https://github.com/huggingface/lerobot",
            },
        ],
        "source_attempt": source_attempt,
        "schema_fields": schema_fields,
        "field_mapping": field_mapping,
        "row_count": row_count,
        "limitation": (
            "First pass downloads only one small public parquet file; it does not mirror the full dataset. "
            "Real welding trajectory data still needs follow-up sourcing."
        ),
    }
    path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
