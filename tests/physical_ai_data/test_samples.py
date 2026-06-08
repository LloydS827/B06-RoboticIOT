from pathlib import Path

from physical_ai_data.samples import generate_pick_sort_package, generate_welding_package
from physical_ai_data.validation import validate_package


def test_generate_welding_package_creates_valid_package(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=7)

    result = validate_package(package)

    assert result.ok
    assert (package / "physical_ai_manifest.json").exists()
    assert (package / "frames.csv").exists()
    assert (package / "events.csv").exists()
    assert (package / "labels.csv").exists()
    assert (package / "metrics.csv").exists()
    assert (package / "artifacts" / "images").is_dir()
    assert result.summary["scenario_type"] == "robot_welding_station"
    assert result.summary["frame_count"] == 12


def test_generate_pick_sort_package_creates_valid_package(tmp_path: Path):
    package = generate_pick_sort_package(tmp_path / "pick_sort", frame_count=10, random_seed=11)

    result = validate_package(package)

    assert result.ok
    assert result.summary["scenario_type"] == "arm_pick_sort"
    assert result.summary["frame_count"] == 10
    assert len(list((package / "artifacts" / "images").glob("*.png"))) == 10


def test_generators_are_deterministic(tmp_path: Path):
    first = generate_pick_sort_package(tmp_path / "first", frame_count=6, random_seed=3)
    second = generate_pick_sort_package(tmp_path / "second", frame_count=6, random_seed=3)

    assert (first / "frames.csv").read_text(encoding="utf-8") == (second / "frames.csv").read_text(encoding="utf-8")
    assert (first / "events.csv").read_text(encoding="utf-8") == (second / "events.csv").read_text(encoding="utf-8")
