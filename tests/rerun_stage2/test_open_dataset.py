import csv
import json
from pathlib import Path

import rerun_stage2.open_dataset as open_dataset


def test_write_open_robot_sample_records_downloaded_source_metadata_and_rows(
    tmp_path: Path,
    monkeypatch,
):
    rows = [
        {
            "source_index": 7,
            "timestamp": 1.25,
            "state_field": "observation.state",
            "state_value": "[1.0, 2.0]",
            "action_field": "action",
            "action_value": "[3.0, 4.0]",
            "image_file": "images/open_robot_0000.png",
            "source_status": "downloaded",
        }
    ]
    schema_fields = ["timestamp", "observation.state", "action", "index"]
    field_mapping = {
        "index": "index",
        "timestamp": "timestamp",
        "state": "observation.state",
        "action": "action",
    }

    def fake_download(url: str, destination: Path):
        assert url == open_dataset.PUSHT_PARQUET_URL
        destination.write_bytes(b"fake parquet bytes")

    def fake_read_parquet(path: Path):
        assert path.name == open_dataset.PUSHT_PARQUET_NAME
        return rows, schema_fields, field_mapping, len(rows)

    monkeypatch.setattr(open_dataset, "_download_file", fake_download)
    monkeypatch.setattr(open_dataset, "_read_parquet_rows", fake_read_parquet)

    sample = open_dataset.write_open_robot_sample(tmp_path / "open_robot_sample")

    metadata = json.loads((sample / "source_metadata.json").read_text(encoding="utf-8"))
    assert metadata["purpose"] == "stage2_open_robot_comparison"
    assert metadata["robot_family"]
    assert metadata["source_attempt"]["url"] == open_dataset.PUSHT_PARQUET_URL
    assert metadata["source_attempt"]["status"] == "downloaded"
    assert metadata["source_attempt"]["saved_path"] == f"source/{open_dataset.PUSHT_PARQUET_NAME}"
    assert metadata["schema_fields"] == schema_fields
    assert metadata["field_mapping"] == field_mapping
    assert metadata["row_count"] == 1

    frame_rows = _read_frame_rows(sample / "frames.csv")
    assert frame_rows == [
        {
            "source_index": "7",
            "timestamp": "1.25",
            "state_field": "observation.state",
            "state_value": "[1.0, 2.0]",
            "action_field": "action",
            "action_value": "[3.0, 4.0]",
            "image_file": "images/open_robot_0000.png",
            "source_status": "downloaded",
        }
    ]
    assert (sample / "frames.csv").exists()
    assert (sample / "images").is_dir()


def test_write_open_robot_sample_records_download_failure_and_placeholder_rows(
    tmp_path: Path,
    monkeypatch,
):
    def fake_download(url: str, destination: Path):
        raise TimeoutError("offline fixture")

    monkeypatch.setattr(open_dataset, "_download_file", fake_download)

    sample = open_dataset.write_open_robot_sample(tmp_path / "open_robot_sample")

    metadata = json.loads((sample / "source_metadata.json").read_text(encoding="utf-8"))
    assert metadata["source_attempt"]["url"] == open_dataset.PUSHT_PARQUET_URL
    assert metadata["source_attempt"]["status"] == "not_available"
    assert metadata["source_attempt"]["error_type"] == "TimeoutError"
    assert metadata["source_attempt"]["error_message"] == "offline fixture"

    frame_rows = _read_frame_rows(sample / "frames.csv")
    assert frame_rows
    assert {row["source_status"] for row in frame_rows} == {"not_available"}
    assert frame_rows[0]["state_value"] == "real open-source comparison not completed"
    assert (sample / "images").is_dir()


def _read_frame_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
