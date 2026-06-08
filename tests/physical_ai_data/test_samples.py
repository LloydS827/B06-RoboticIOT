from pathlib import Path

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


def test_welding_generator_is_deterministic(tmp_path: Path):
    first = generate_welding_package(tmp_path / "first", frame_count=6, random_seed=3)
    second = generate_welding_package(tmp_path / "second", frame_count=6, random_seed=3)

    _assert_packages_match(first, second)


def test_pick_sort_generator_is_deterministic(tmp_path: Path):
    first = generate_pick_sort_package(tmp_path / "first", frame_count=6, random_seed=3)
    second = generate_pick_sort_package(tmp_path / "second", frame_count=6, random_seed=3)

    _assert_packages_match(first, second)
