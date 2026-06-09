import json
import shutil
import subprocess
from pathlib import Path

import pytest
from PIL import Image

from physical_ai_data import rerun_adapter
from physical_ai_data.lerobot_adapter import (
    LeRobotEpisode,
    LeRobotFrame,
    import_lerobot_episode,
)
from physical_ai_data.rerun_adapter import write_rrd
from physical_ai_data.samples import generate_pick_sort_package, generate_welding_package


def _verify_rrd(output: Path) -> None:
    if shutil.which("rerun") is None:
        pytest.skip("rerun CLI is not installed")

    verify = subprocess.run(["rerun", "rrd", "verify", str(output)], check=False, text=True, capture_output=True)
    assert verify.returncode == 0, verify.stderr + verify.stdout


def _image(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 16), color).save(path)


def _lerobot_multicamera_package(tmp_path: Path) -> Path:
    source_images = tmp_path / "source_images"
    front = source_images / "front_0000.png"
    side = source_images / "side_0000.png"
    _image(front, (255, 0, 0))
    _image(side, (0, 0, 255))
    episode = LeRobotEpisode(
        repo_id="lerobot/pusht",
        episode_index=0,
        fps=10.0,
        task_name="PushT",
        profile="pusht",
        features={"observation.image": {"dtype": "image", "shape": [16, 16, 3]}},
        stats={},
        episode_metadata={"episode_index": 0},
        task_metadata={"task": "PushT"},
        frames=[
            LeRobotFrame(
                frame_index=0,
                timestamp_s=0.0,
                images={"front": front, "side": side},
                state=[0.1, 0.2],
                action=[0.3, 0.4],
            )
        ],
    )
    return import_lerobot_episode(episode, tmp_path / "package", primary_camera="front")


class _FakeRerun:
    def __init__(self) -> None:
        self.logs: list[tuple[str, object]] = []
        self.times: list[tuple[str, float]] = []

    def set_time(self, timeline: str, *, duration: float) -> None:
        self.times.append((timeline, duration))

    def Image(self, image: object) -> tuple[str, object]:
        return ("Image", image)

    def log(self, entity_path: str, archetype: object) -> None:
        self.logs.append((entity_path, archetype))


def test_write_welding_rrd_and_verify(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=8, random_seed=8)
    output = tmp_path / "weld.rrd"

    result = write_rrd(package, output)

    assert result == output
    assert output.exists()
    _verify_rrd(output)


def test_write_pick_sort_rrd_and_verify(tmp_path: Path):
    package = generate_pick_sort_package(tmp_path / "pick", frame_count=8, random_seed=9)
    output = tmp_path / "pick.rrd"

    result = write_rrd(package, output)

    assert result == output
    assert output.exists()
    _verify_rrd(output)


def test_write_lerobot_multicamera_rrd_and_verify(tmp_path: Path):
    package = _lerobot_multicamera_package(tmp_path)
    output = tmp_path / "lerobot.rrd"

    result = write_rrd(package, output)

    assert result == output
    assert output.exists()
    _verify_rrd(output)


def test_log_frames_ignores_invalid_image_refs_json_and_logs_additional_cameras(tmp_path: Path):
    root = tmp_path / "package"
    front = root / "artifacts" / "images" / "front" / "frame_0000.png"
    side = root / "artifacts" / "images" / "side" / "frame_0000.png"
    directory = root / "artifacts" / "images" / "directory"
    corrupt = root / "artifacts" / "images" / "corrupt" / "frame_0000.png"
    outside = tmp_path / "outside.png"
    _image(front, (255, 0, 0))
    _image(side, (0, 0, 255))
    directory.mkdir(parents=True)
    corrupt.parent.mkdir(parents=True)
    corrupt.write_text("not an image", encoding="utf-8")
    _image(outside, (0, 255, 0))
    rr = _FakeRerun()
    frames = [
        {
            "frame_id": "frame_0000",
            "timestamp_s": "0.0",
            "image_ref": "artifacts/images/front/frame_0000.png",
            "image_refs_json": json.dumps(
                {
                    "front": "artifacts/images/front/frame_0000.png",
                    "side/camera": "artifacts/images/side/frame_0000.png",
                    "missing": "artifacts/images/missing/frame_0000.png",
                    "outside": "../outside.png",
                    "absolute": str(outside),
                    "directory": "artifacts/images/directory",
                    "corrupt": "artifacts/images/corrupt/frame_0000.png",
                    "duplicate": "artifacts/images/front/frame_0000.png",
                }
            ),
            "point_cloud_ref": "",
            "trajectory_ref": "",
        },
        {
            "frame_id": "frame_0001",
            "timestamp_s": "0.1",
            "image_ref": "",
            "image_refs_json": "{not json",
            "point_cloud_ref": "",
            "trajectory_ref": "",
        },
        {
            "frame_id": "frame_0002",
            "timestamp_s": "0.2",
            "image_ref": "",
            "image_refs_json": '["not", "an", "object"]',
            "point_cloud_ref": "",
            "trajectory_ref": "",
        },
    ]

    rerun_adapter._log_frames(rr, root, frames, "/package/open_robot_manipulation")

    log_paths = [path for path, _ in rr.logs]
    assert "/package/open_robot_manipulation/frames/frame_0000/image" in log_paths
    assert "/package/open_robot_manipulation/frames/frame_0000/images/side_camera" in log_paths
    assert "/package/open_robot_manipulation/frames/frame_0000/images/missing" not in log_paths
    assert "/package/open_robot_manipulation/frames/frame_0000/images/outside" not in log_paths
    assert "/package/open_robot_manipulation/frames/frame_0000/images/absolute" not in log_paths
    assert "/package/open_robot_manipulation/frames/frame_0000/images/directory" not in log_paths
    assert "/package/open_robot_manipulation/frames/frame_0000/images/corrupt" not in log_paths
    assert "/package/open_robot_manipulation/frames/frame_0000/images/duplicate" not in log_paths


def test_invalid_package_raises_validator_summary(tmp_path: Path):
    with pytest.raises(ValueError, match="missing_manifest: Missing physical_ai_manifest.json"):
        write_rrd(tmp_path, tmp_path / "invalid.rrd")


def test_float_helper_rejects_non_finite_values():
    assert rerun_adapter._float_or_none("nan") is None
    assert rerun_adapter._float_or_none("inf") is None
    assert rerun_adapter._float_or_none("-inf") is None
    assert rerun_adapter._float_or_none("1.25") == 1.25


def test_xyz_reader_skips_non_finite_rows(tmp_path: Path):
    xyz = tmp_path / "points.csv"
    xyz.write_text("x,y,z\n1,2,3\nnan,2,3\n1,inf,3\n1,2,-inf\n", encoding="utf-8")

    assert rerun_adapter._read_xyz_csv(xyz) == [(1.0, 2.0, 3.0)]


def test_pose_mapping_degrades_non_finite_values_to_defaults():
    default = {"translation": (0.0, 0.0, 0.0), "quaternion": (0.0, 0.0, 0.0, 1.0)}

    assert rerun_adapter._pose_from_mapping({"x": "nan", "y": "1", "z": "2"}, default) == default
    assert rerun_adapter._pose_from_mapping(
        {"x": "1", "y": "2", "z": "3", "qx": "0", "qy": "inf", "qz": "0", "qw": "1"},
        default,
    ) == {"translation": (1.0, 2.0, 3.0), "quaternion": default["quaternion"]}
