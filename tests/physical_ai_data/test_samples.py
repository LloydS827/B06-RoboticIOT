import csv
from pathlib import Path

import pytest

from physical_ai_data.samples import generate_pick_sort_package, generate_welding_package
from physical_ai_data.validation import validate_package

DETERMINISTIC_TEXT_FILES = [
    "physical_ai_manifest.json",
    "frames.csv",
    "events.csv",
    "labels.csv",
    "metrics.csv",
    "README.md",
    "artifacts/point_clouds/workpiece.csv",
    "artifacts/trajectories/tcp_path.csv",
]


def _assert_packages_match(first: Path, second: Path) -> None:
    for relative_path in DETERMINISTIC_TEXT_FILES:
        assert (first / relative_path).read_text(encoding="utf-8") == (second / relative_path).read_text(encoding="utf-8")

    first_images = sorted((first / "artifacts" / "images").glob("*.png"))
    second_images = sorted((second / "artifacts" / "images").glob("*.png"))
    assert [image.name for image in first_images] == [image.name for image in second_images]
    assert first_images
    for first_image, second_image in zip(first_images, second_images):
        assert first_image.read_bytes() == second_image.read_bytes()


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def test_generate_welding_package_creates_valid_package(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=7)

    result = validate_package(package)
    frames = _read_csv_rows(package / "frames.csv")
    events = _read_csv_rows(package / "events.csv")
    labels = _read_csv_rows(package / "labels.csv")
    metrics = _read_csv_rows(package / "metrics.csv")

    assert result.ok
    assert (package / "physical_ai_manifest.json").exists()
    assert (package / "frames.csv").exists()
    assert (package / "events.csv").exists()
    assert (package / "labels.csv").exists()
    assert (package / "metrics.csv").exists()
    assert (package / "artifacts" / "images").is_dir()
    assert result.summary["scenario_type"] == "robot_welding_station"
    assert result.summary["frame_count"] == 12
    assert {row["phase"] for row in frames} >= {"approach", "welding", "finish"}
    assert {row["event_type"] for row in events} >= {"start", "end", "porosity_risk"}
    assert {row["label_type"] for row in labels} >= {"quality"}
    assert {row["metric_name"] for row in metrics} >= {"weld_current", "weld_voltage", "defect_probability"}


def test_generate_pick_sort_package_creates_valid_package(tmp_path: Path):
    package = generate_pick_sort_package(tmp_path / "pick_sort", frame_count=10, random_seed=11)

    result = validate_package(package)
    frames = _read_csv_rows(package / "frames.csv")
    events = _read_csv_rows(package / "events.csv")
    labels = _read_csv_rows(package / "labels.csv")
    metrics = _read_csv_rows(package / "metrics.csv")
    frame_ids = {row["frame_id"] for row in frames}

    assert result.ok
    assert result.summary["scenario_type"] == "arm_pick_sort"
    assert result.summary["frame_count"] == 10
    assert len(list((package / "artifacts" / "images").glob("*.png"))) == 10
    assert {row["phase"] for row in frames} >= {"observe", "approach", "grasp", "transfer", "place", "finish"}
    event_types = {row["event_type"] for row in events}
    assert event_types >= {"object_detected", "grasp_attempt"}
    assert event_types & {"place_success", "place_failure"}
    assert {row["value"] for row in labels} & {"success", "failure"}
    assert all(row["target_ref"].startswith("frame:") for row in labels)
    assert {row["target_ref"].removeprefix("frame:") for row in labels} <= frame_ids
    assert {row["metric_name"] for row in metrics} >= {"grip_confidence", "object_confidence"}


def test_welding_generator_rejects_too_few_frames(tmp_path: Path):
    with pytest.raises(ValueError, match="welding frame_count must be at least 3"):
        generate_welding_package(tmp_path / "weld", frame_count=2)


def test_pick_sort_generator_rejects_too_few_frames(tmp_path: Path):
    with pytest.raises(ValueError, match="pick/sort frame_count must be at least 6"):
        generate_pick_sort_package(tmp_path / "pick_sort", frame_count=5)


def test_generator_preserves_unrelated_png_artifacts(tmp_path: Path):
    package = tmp_path / "weld"
    images = package / "artifacts" / "images"
    images.mkdir(parents=True)
    preserved = images / "calibration.png"
    stale_generated = images / "frame_9999.png"
    preserved.write_bytes(b"keep-me")
    stale_generated.write_bytes(b"old-frame")

    generate_welding_package(package, frame_count=3, random_seed=2)

    assert preserved.read_bytes() == b"keep-me"
    assert not stale_generated.exists()


def test_welding_generator_is_deterministic(tmp_path: Path):
    first = generate_welding_package(tmp_path / "first", frame_count=6, random_seed=3)
    second = generate_welding_package(tmp_path / "second", frame_count=6, random_seed=3)

    _assert_packages_match(first, second)


def test_pick_sort_generator_is_deterministic(tmp_path: Path):
    first = generate_pick_sort_package(tmp_path / "first", frame_count=6, random_seed=3)
    second = generate_pick_sort_package(tmp_path / "second", frame_count=6, random_seed=3)

    _assert_packages_match(first, second)
