import json
from pathlib import Path

from rerun_stage2.open_dataset import write_open_robot_sample


def test_write_open_robot_sample_creates_source_metadata_and_attempt_record(tmp_path: Path):
    sample = write_open_robot_sample(tmp_path / "open_robot_sample")

    metadata = json.loads((sample / "source_metadata.json").read_text(encoding="utf-8"))
    assert metadata["purpose"] == "stage2_open_robot_comparison"
    assert metadata["robot_family"]
    assert metadata["source_attempt"]["url"]
    assert metadata["source_attempt"]["status"] in {"downloaded", "not_available"}
    assert (sample / "frames.csv").exists()
    assert (sample / "images").is_dir()
