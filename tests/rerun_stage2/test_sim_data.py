import builtins
from pathlib import Path

import pytest

from rerun_stage2.sim_data import RecordingConfig, generate_frames, generate_point_cloud, write_simulation_package


def test_generate_frames_is_deterministic_and_contains_required_timelines():
    config = RecordingConfig(frame_count=8, random_seed=42)

    first = generate_frames(config)
    second = generate_frames(config)

    assert len(first) == 8
    assert [f.tcp_position for f in first] == [f.tcp_position for f in second]
    assert [f.weld_current for f in first] == [f.weld_current for f in second]
    assert first[0].event == "arc_start"
    assert any(frame.event == "porosity_risk" for frame in first)
    assert first[-1].event == "arc_end"
    assert {f.weld_phase for f in first} >= {"approach", "welding", "finish"}
    assert all(isinstance(f.robot_tick, int) for f in first)
    assert all(isinstance(f.camera_frame, int) for f in first)


def test_generate_point_cloud_is_deterministic_and_non_empty():
    config = RecordingConfig(frame_count=8, random_seed=42)

    points_a = generate_point_cloud(config)
    points_b = generate_point_cloud(config)

    assert points_a == points_b
    assert len(points_a) >= 40
    assert all(len(point) == 3 for point in points_a)


def test_write_simulation_package_creates_manifest_tables_images_and_point_cloud(tmp_path: Path):
    config = RecordingConfig(frame_count=6, random_seed=7)

    package = write_simulation_package(tmp_path / "sim_weld_001", config)

    assert package.root.exists()
    assert (package.root / "manifest.json").exists()
    assert (package.root / "frames.csv").exists()
    assert (package.root / "events.csv").exists()
    assert (package.root / "quality.json").exists()
    assert (package.root / "point_cloud.csv").exists()
    assert (package.root / "images").is_dir()
    assert len(list((package.root / "images").glob("*.png"))) == 6


def test_write_simulation_package_removes_stale_images_when_regenerating(tmp_path: Path):
    package_root = tmp_path / "sim_weld_001"

    write_simulation_package(package_root, RecordingConfig(frame_count=6, random_seed=7))
    package = write_simulation_package(package_root, RecordingConfig(frame_count=3, random_seed=7))

    image_files = sorted(path.name for path in (package.root / "images").glob("*.png"))
    assert image_files == ["frame_0000.png", "frame_0001.png", "frame_0002.png"]


def test_write_simulation_package_fails_loudly_when_pillow_is_missing(tmp_path: Path, monkeypatch):
    original_import = builtins.__import__

    def fail_pillow_import(name, *args, **kwargs):
        if name == "PIL" or name.startswith("PIL."):
            raise ImportError("simulated missing pillow")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_pillow_import)

    with pytest.raises(RuntimeError, match="Pillow"):
        write_simulation_package(tmp_path / "sim_weld_001", RecordingConfig(frame_count=1, random_seed=7))
