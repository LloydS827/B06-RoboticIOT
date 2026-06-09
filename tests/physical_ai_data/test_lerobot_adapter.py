from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from PIL import Image

from physical_ai_data.lerobot_adapter import LeRobotEpisode, LeRobotFrame, import_lerobot_episode
from physical_ai_data.schema import SUPPORTED_SCENARIOS
from physical_ai_data.validation import validate_package


def _image(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 16), color).save(path)


def _episode(tmp_path: Path) -> LeRobotEpisode:
    source_images = tmp_path / "source_images"
    _image(source_images / "front_0000.png", (255, 0, 0))
    _image(source_images / "front_0001.png", (0, 255, 0))
    return LeRobotEpisode(
        repo_id="lerobot/pusht",
        episode_index=0,
        fps=10.0,
        task_name="PushT",
        profile="pusht",
        root=tmp_path / "dataset_root",
        features={
            "observation.image": {"dtype": "image", "shape": [16, 16, 3]},
            "observation.state": {"dtype": "float32", "shape": [4]},
            "action": {"dtype": "float32", "shape": [2]},
        },
        stats={"observation.state": {"mean": [0.0, 0.0, 0.0, 0.0]}},
        episode_metadata={"episode_index": 0},
        task_metadata={"task": "PushT"},
        frames=[
            LeRobotFrame(
                frame_index=0,
                timestamp_s=0.0,
                images={"front": source_images / "front_0000.png"},
                state=[0.1, 0.2, 0.3, 0.4],
                action=[0.0, 0.0],
            ),
            LeRobotFrame(
                frame_index=1,
                timestamp_s=0.1,
                images={"front": source_images / "front_0001.png"},
                state=[0.2, 0.3, 0.4, 0.5],
                action=[0.8, 0.2],
            ),
        ],
    )


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def test_open_robot_manipulation_is_supported():
    assert "open_robot_manipulation" in SUPPORTED_SCENARIOS


def test_import_lerobot_episode_creates_valid_physical_ai_package(tmp_path: Path):
    package = import_lerobot_episode(_episode(tmp_path), tmp_path / "package", max_frames=None)

    result = validate_package(package)
    manifest = json.loads((package / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    frames = _rows(package / "frames.csv")
    events = _rows(package / "events.csv")
    labels = _rows(package / "labels.csv")
    metrics = _rows(package / "metrics.csv")
    state_action = _rows(package / "artifacts" / "source" / "frame_state_action.csv")

    assert result.ok
    assert manifest["scenario_type"] == "open_robot_manipulation"
    assert manifest["source_dataset"]["format"] == "lerobot"
    assert manifest["source_dataset"]["repo_id"] == "lerobot/pusht"
    assert manifest["source_dataset"]["root"] == str(tmp_path / "dataset_root")
    assert manifest["source_dataset"]["episode_index"] == 0
    assert manifest["source_dataset"]["profile"] == "pusht"
    assert manifest["source_dataset"]["feature_schema_ref"] == "artifacts/source/lerobot_features.json"
    assert manifest["source_dataset"]["stats_ref"] == "artifacts/source/lerobot_stats.json"
    assert manifest["source_dataset"]["episode_metadata_ref"] == "artifacts/source/lerobot_episode_metadata.json"
    assert manifest["source_dataset"]["task_metadata_ref"] == "artifacts/source/lerobot_task_metadata.json"
    assert manifest["source_dataset"]["fps"] == 10.0
    assert manifest["source_dataset"]["frame_count"] == 2
    assert "converted_at" in manifest["source_dataset"]
    assert manifest["objects"] == [
        {"object_id": "block", "type": "object"},
        {"object_id": "target", "type": "target"},
    ]
    assert (package / "artifacts" / "source" / "lerobot_features.json").exists()
    assert (package / "artifacts" / "source" / "lerobot_stats.json").exists()
    assert (package / "artifacts" / "source" / "lerobot_episode_metadata.json").exists()
    assert (package / "artifacts" / "source" / "lerobot_task_metadata.json").exists()
    assert (package / "artifacts" / "images" / "front" / "frame_0000.png").exists()
    assert (package / "README.md").exists()
    assert len(frames) == 2
    assert frames[0]["timeline"] == "sim_time"
    assert frames[0]["phase"] == "pushing"
    assert frames[0]["image_ref"] == "artifacts/images/front/frame_0000.png"
    assert frames[0]["source_frame_index"] == "0"
    assert json.loads(frames[0]["image_refs_json"]) == {"front": "artifacts/images/front/frame_0000.png"}
    assert events[0]["event_type"] == "episode_start"
    assert events[-1]["event_type"] == "episode_end"
    assert labels[0]["label_type"] == "task_context"
    assert not any(label["value"] in {"success", "failure"} for label in labels)
    assert any(row["metric_name"] == "action_delta" for row in metrics)
    assert any(row["metric_name"] == "image_available" for row in metrics)
    assert state_action[0]["state_json"] == "[0.1, 0.2, 0.3, 0.4]"


def test_import_lerobot_episode_records_additional_camera_refs(tmp_path: Path):
    episode = _episode(tmp_path)
    side = tmp_path / "source_images" / "side_0000.png"
    _image(side, (0, 0, 255))
    frames = list(episode.frames)
    frames[0] = LeRobotFrame(
        frame_index=0,
        timestamp_s=0.0,
        images={**frames[0].images, "side": side},
        state=frames[0].state,
        action=frames[0].action,
    )
    episode = LeRobotEpisode(
        repo_id=episode.repo_id,
        episode_index=episode.episode_index,
        fps=episode.fps,
        frames=frames,
        task_name=episode.task_name,
        profile=episode.profile,
        root=episode.root,
        features=episode.features,
        stats=episode.stats,
        episode_metadata=episode.episode_metadata,
        task_metadata=episode.task_metadata,
    )

    package = import_lerobot_episode(episode, tmp_path / "package", primary_camera="front")
    row = _rows(package / "frames.csv")[0]
    image_refs = json.loads(row["image_refs_json"])

    assert row["image_ref"] == "artifacts/images/front/frame_0000.png"
    assert image_refs == {
        "front": "artifacts/images/front/frame_0000.png",
        "side": "artifacts/images/side/frame_0000.png",
    }


def test_import_lerobot_episode_adds_fallback_profile_warning(tmp_path: Path):
    episode = _episode(tmp_path)
    fallback_episode = LeRobotEpisode(
        repo_id="unknown/repo",
        episode_index=episode.episode_index,
        fps=episode.fps,
        task_name=episode.task_name,
        profile="fallback",
        root=episode.root,
        features=episode.features,
        stats=episode.stats,
        episode_metadata=episode.episode_metadata,
        task_metadata=episode.task_metadata,
        frames=episode.frames,
    )

    package = import_lerobot_episode(fallback_episode, tmp_path / "package", max_frames=None)
    manifest = json.loads((package / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    frames = _rows(package / "frames.csv")
    events = _rows(package / "events.csv")

    assert validate_package(package).ok
    assert manifest["source_dataset"]["profile"] == "fallback"
    assert manifest["objects"] == [{"object_id": "task_object", "type": "object"}]
    assert frames[0]["phase"] == "episode"
    assert any(
        row["event_type"] == "profile_fallback" and row["severity"] == "warning"
        for row in events
    )


def test_import_lerobot_episode_respects_max_frames(tmp_path: Path):
    package = import_lerobot_episode(_episode(tmp_path), tmp_path / "package", max_frames=1)

    assert validate_package(package).summary["frame_count"] == 1


def test_imported_lerobot_metrics_can_export_candidates(tmp_path: Path):
    package = import_lerobot_episode(_episode(tmp_path), tmp_path / "package", max_frames=None)

    from physical_ai_data.candidates import export_candidates

    output = export_candidates(package, min_score=0.5)
    rows = _rows(output)

    assert rows
    assert any("action_delta" in row["reasons"] for row in rows)


def test_import_lerobot_episode_rejects_missing_primary_camera(tmp_path: Path):
    with pytest.raises(ValueError, match="primary_camera not found: missing"):
        import_lerobot_episode(_episode(tmp_path), tmp_path / "package", primary_camera="missing")


def test_import_lerobot_episode_rejects_non_positive_max_frames(tmp_path: Path):
    with pytest.raises(ValueError, match="max_frames must be positive"):
        import_lerobot_episode(_episode(tmp_path), tmp_path / "package", max_frames=0)


def test_import_lerobot_episode_skips_non_finite_numeric_values(tmp_path: Path):
    episode = _episode(tmp_path)
    episode = LeRobotEpisode(
        repo_id=episode.repo_id,
        episode_index=episode.episode_index,
        fps=episode.fps,
        task_name=episode.task_name,
        profile=episode.profile,
        root=episode.root,
        features=episode.features,
        stats=episode.stats,
        episode_metadata=episode.episode_metadata,
        task_metadata=episode.task_metadata,
        frames=[
            LeRobotFrame(
                frame_index=0,
                timestamp_s=0.0,
                images=episode.frames[0].images,
                state=[1.0, float("nan"), float("inf")],
                action=[2.0, float("-inf")],
            )
        ],
    )

    package = import_lerobot_episode(episode, tmp_path / "package")
    metric_values = [float(row["value"]) for row in _rows(package / "metrics.csv")]

    assert validate_package(package).ok
    assert all(value == value and value not in {float("inf"), float("-inf")} for value in metric_values)
