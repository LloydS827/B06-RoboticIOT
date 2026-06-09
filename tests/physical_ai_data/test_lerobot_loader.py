from __future__ import annotations

import sys
from types import ModuleType
from pathlib import Path
from types import SimpleNamespace

import pytest

from physical_ai_data.lerobot_adapter import LeRobotFrame
from physical_ai_data.lerobot_loader import load_lerobot_episode


class FakeTensor:
    def __init__(self, value: object) -> None:
        self.value = value

    def detach(self) -> FakeTensor:
        return self

    def cpu(self) -> FakeTensor:
        return self

    def numpy(self) -> FakeTensor:
        return self

    def tolist(self) -> object:
        return self.value


def install_fake_lerobot_module(
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    dataset_class: type | None,
) -> None:
    module_names = [
        "lerobot",
        "lerobot.datasets",
        "lerobot.datasets.lerobot_dataset",
        "lerobot.common",
        "lerobot.common.datasets",
        "lerobot.common.datasets.lerobot_dataset",
    ]
    for module_name in module_names:
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    parents = path.split(".")[:-1]
    for index in range(1, len(parents) + 1):
        module_name = ".".join(parents[:index])
        module = ModuleType(module_name)
        monkeypatch.setitem(sys.modules, module_name, module)
        if index > 1:
            parent_name = ".".join(parents[: index - 1])
            setattr(sys.modules[parent_name], parents[index - 1], module)

    dataset_module = ModuleType(path)
    if dataset_class is not None:
        dataset_module.LeRobotDataset = dataset_class
    monkeypatch.setitem(sys.modules, path, dataset_module)
    parent_name, child_name = path.rsplit(".", 1)
    setattr(sys.modules[parent_name], child_name, dataset_module)


def test_loader_raises_clear_error_when_lerobot_missing(monkeypatch: pytest.MonkeyPatch):
    install_fake_lerobot_module(monkeypatch, "lerobot.datasets.lerobot_dataset", None)
    monkeypatch.delitem(sys.modules, "lerobot.datasets.lerobot_dataset", raising=False)
    monkeypatch.delitem(sys.modules, "lerobot.common.datasets.lerobot_dataset", raising=False)

    with pytest.raises(RuntimeError, match="Install the lerobot optional dependency"):
        load_lerobot_episode(repo_id="lerobot/pusht", episode_index=0, max_frames=1)


def test_loader_imports_dataset_from_current_lerobot_path(monkeypatch: pytest.MonkeyPatch):
    class FakeDataset:
        def __init__(self, repo_id: str, root: Path | None = None, episodes: list[int] | None = None) -> None:
            self.hf_dataset = [{"episode_index": 0, "frame_index": 0}]

    install_fake_lerobot_module(
        monkeypatch,
        "lerobot.datasets.lerobot_dataset",
        FakeDataset,
    )

    episode = load_lerobot_episode(repo_id="lerobot/fake", episode_index=0, max_frames=1)

    assert len(episode.frames) == 1


def test_loader_falls_back_to_legacy_lerobot_path(monkeypatch: pytest.MonkeyPatch):
    class FakeDataset:
        def __init__(self, repo_id: str, root: Path | None = None, episodes: list[int] | None = None) -> None:
            self.hf_dataset = [{"episode_index": 0, "frame_index": 0}]

    install_fake_lerobot_module(
        monkeypatch,
        "lerobot.common.datasets.lerobot_dataset",
        FakeDataset,
    )

    episode = load_lerobot_episode(repo_id="lerobot/fake", episode_index=0, max_frames=1)

    assert len(episode.frames) == 1


def test_loader_converts_fake_hf_dataset(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    calls: list[dict[str, object]] = []

    class FakeDataset:
        meta = SimpleNamespace(
            fps=10.0,
            features={"observation.state": {}, "action": {}},
            stats={"action": {"mean": [0.0, 0.0]}},
            tasks={7: "fake task"},
        )

        def __init__(self, repo_id: str, root: Path | None = None, episodes: list[int] | None = None) -> None:
            calls.append({"repo_id": repo_id, "root": root, "episodes": episodes})
            self.hf_dataset = [
                {
                    "episode_index": 0,
                    "frame_index": 0,
                    "timestamp": FakeTensor(0.0),
                    "observation.state": FakeTensor([0.1, 0.2]),
                    "action": FakeTensor([0.3, 0.4]),
                    "task": "fake task",
                },
                {
                    "episode_index": 1,
                    "frame_index": 0,
                    "timestamp": 0.0,
                    "observation.state": [9.0],
                    "action": [9.0],
                    "task": "other",
                },
                {
                    "episode_index": 0,
                    "frame_index": 1,
                    "timestamp": 0.1,
                    "observation.state": [0.5, 0.6],
                    "action": [0.7, 0.8],
                    "task": "fake task",
                },
            ]

    install_fake_lerobot_module(
        monkeypatch,
        "lerobot.common.datasets.lerobot_dataset",
        FakeDataset,
    )

    episode = load_lerobot_episode(
        repo_id="lerobot/fake",
        episode_index=0,
        root=tmp_path,
        profile="fallback",
        max_frames=1,
    )

    assert calls == [{"repo_id": "lerobot/fake", "root": tmp_path, "episodes": [0]}]
    assert episode.repo_id == "lerobot/fake"
    assert episode.episode_index == 0
    assert episode.root == tmp_path
    assert episode.fps == 10.0
    assert episode.profile == "fallback"
    assert episode.task_name == "fake task"
    assert episode.features == {"observation.state": {}, "action": {}}
    assert episode.stats == {"action": {"mean": [0.0, 0.0]}}
    assert episode.episode_metadata["episode_index"] == 0
    assert episode.task_metadata == {"task": "fake task", "tasks": {7: "fake task"}}
    assert episode.frames == [
        LeRobotFrame(
            frame_index=0,
            timestamp_s=0.0,
            images={},
            state=[0.1, 0.2],
            action=[0.3, 0.4],
        )
    ]


def test_loader_falls_back_to_dataset_iterable(monkeypatch: pytest.MonkeyPatch):
    class FakeDataset:
        fps = 12.5
        features = {"observation.state": {"dtype": "float32"}}

        def __init__(self, repo_id: str, root: Path | None = None, episodes: list[int] | None = None) -> None:
            self.repo_id = repo_id
            self.root = root
            self.episodes = episodes

        def __iter__(self):
            return iter(
                [
                    {
                        "frame_index": 3,
                        "timestamp": 0.25,
                        "observation.state": (1, 2),
                        "action": FakeTensor([3, 4]),
                    }
                ]
            )

    install_fake_lerobot_module(
        monkeypatch,
        "lerobot.common.datasets.lerobot_dataset",
        FakeDataset,
    )

    episode = load_lerobot_episode(repo_id="lerobot/pusht", episode_index=2)

    assert episode.fps == 12.5
    assert episode.profile == "pusht"
    assert episode.features == {"observation.state": {"dtype": "float32"}}
    assert episode.episode_metadata == {"episode_index": 2}
    assert episode.frames[0].frame_index == 3
    assert episode.frames[0].timestamp_s == 0.25
    assert episode.frames[0].state == [1.0, 2.0]
    assert episode.frames[0].action == [3.0, 4.0]


def test_loader_collects_path_like_images(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    image_path = tmp_path / "front.png"

    class FakeDataset:
        meta = SimpleNamespace(fps=30.0)

        def __init__(self, repo_id: str, root: Path | None = None, episodes: list[int] | None = None) -> None:
            self.hf_dataset = [
                {
                    "episode_index": 0,
                    "frame_index": 0,
                    "observation.images.front": str(image_path),
                    "observation.state": [],
                    "action": [],
                }
            ]

    install_fake_lerobot_module(
        monkeypatch,
        "lerobot.common.datasets.lerobot_dataset",
        FakeDataset,
    )

    episode = load_lerobot_episode(repo_id="lerobot/fake", episode_index=0, camera="front")

    assert episode.frames[0].images == {"front": image_path}


def test_loader_writes_tensor_images_to_temporary_png(monkeypatch: pytest.MonkeyPatch):
    class FakeDataset:
        def __init__(self, repo_id: str, root: Path | None = None, episodes: list[int] | None = None) -> None:
            self.hf_dataset = [
                {
                    "episode_index": 0,
                    "frame_index": 0,
                    "observation.images.front_left": FakeTensor(
                        [
                            [[1.0, 0.0], [0.0, 1.0]],
                            [[0.0, 1.0], [1.0, 0.0]],
                            [[0.5, 0.5], [0.25, 0.75]],
                        ]
                    ),
                    "observation.state": [],
                    "action": [],
                }
            ]

    install_fake_lerobot_module(
        monkeypatch,
        "lerobot.datasets.lerobot_dataset",
        FakeDataset,
    )

    episode = load_lerobot_episode(repo_id="lerobot/fake", episode_index=0, camera="front_left")
    image_path = episode.frames[0].images["front_left"]

    assert image_path.suffix == ".png"
    assert image_path.exists()
