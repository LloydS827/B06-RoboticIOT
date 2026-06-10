from __future__ import annotations

from collections.abc import Mapping
import json
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


def test_loader_falls_back_to_hf_dataset_when_lerobot_rejects_old_format(
    monkeypatch: pytest.MonkeyPatch,
):
    class FakeBackwardCompatibilityError(Exception):
        pass

    class FakeDataset:
        def __init__(self, repo_id: str, root: Path | None = None, episodes: list[int] | None = None) -> None:
            raise FakeBackwardCompatibilityError("dataset is in 2.1 format")

    class FakeHFDataset:
        features = {
            "episode_index": {},
            "frame_index": {},
            "timestamp": {},
            "observation.state": {},
            "action": {},
        }

        def __iter__(self):
            return iter(
                [
                    {
                        "episode_index": 0,
                        "frame_index": 0,
                        "timestamp": 0.0,
                        "observation.state": [1.0, 2.0],
                        "action": [3.0, 4.0],
                    }
                ]
            )

    calls: list[dict[str, object]] = []

    def fake_load_dataset(repo_id: str, split: str, streaming: bool):
        calls.append({"repo_id": repo_id, "split": split, "streaming": streaming})
        return FakeHFDataset()

    install_fake_lerobot_module(
        monkeypatch,
        "lerobot.datasets.lerobot_dataset",
        FakeDataset,
    )
    backward_module = ModuleType("lerobot.datasets.backward_compatibility")
    backward_module.BackwardCompatibilityError = FakeBackwardCompatibilityError
    monkeypatch.setitem(sys.modules, "lerobot.datasets.backward_compatibility", backward_module)
    datasets_module = ModuleType("datasets")
    datasets_module.load_dataset = fake_load_dataset
    monkeypatch.setitem(sys.modules, "datasets", datasets_module)

    episode = load_lerobot_episode(repo_id="lerobot/old-format", episode_index=0, max_frames=1)

    assert calls == [{"repo_id": "lerobot/old-format", "split": "train", "streaming": True}]
    assert episode.features == FakeHFDataset.features
    assert episode.frames == [
        LeRobotFrame(
            frame_index=0,
            timestamp_s=0.0,
            images={},
            state=[1.0, 2.0],
            action=[3.0, 4.0],
        )
    ]


def test_loader_normalizes_hf_fallback_features_with_to_dict(
    monkeypatch: pytest.MonkeyPatch,
):
    class FakeBackwardCompatibilityError(Exception):
        pass

    class FakeDataset:
        def __init__(self, repo_id: str, root: Path | None = None, episodes: list[int] | None = None) -> None:
            raise FakeBackwardCompatibilityError("dataset is in 2.1 format")

    class FakeFeature:
        pass

    class FakeFeatures(Mapping[str, object]):
        _plain = {
            "episode_index": {"dtype": "int64"},
            "observation.state": {"dtype": "float32", "shape": [2]},
            "action": {"dtype": "float32", "shape": [2]},
        }

        def __getitem__(self, key: str) -> object:
            return FakeFeature()

        def __iter__(self):
            return iter(self._plain)

        def __len__(self) -> int:
            return len(self._plain)

        def to_dict(self) -> dict[str, object]:
            return self._plain

    class FakeHFDataset:
        features = FakeFeatures()

        def __iter__(self):
            return iter(
                [
                    {
                        "episode_index": 0,
                        "frame_index": 0,
                        "observation.state": [1.0, 2.0],
                        "action": [3.0, 4.0],
                    }
                ]
            )

    def fake_load_dataset(repo_id: str, split: str, streaming: bool):
        return FakeHFDataset()

    install_fake_lerobot_module(
        monkeypatch,
        "lerobot.datasets.lerobot_dataset",
        FakeDataset,
    )
    backward_module = ModuleType("lerobot.datasets.backward_compatibility")
    backward_module.BackwardCompatibilityError = FakeBackwardCompatibilityError
    monkeypatch.setitem(sys.modules, "lerobot.datasets.backward_compatibility", backward_module)
    datasets_module = ModuleType("datasets")
    datasets_module.load_dataset = fake_load_dataset
    monkeypatch.setitem(sys.modules, "datasets", datasets_module)

    episode = load_lerobot_episode(repo_id="lerobot/old-format", episode_index=0, max_frames=1)

    assert episode.features == FakeFeatures._plain
    json.dumps(dict(episode.features))


def test_loader_reraises_non_backward_compatibility_lerobot_errors(
    monkeypatch: pytest.MonkeyPatch,
):
    class FakeBackwardCompatibilityError(Exception):
        pass

    class FakeDataset:
        def __init__(self, repo_id: str, root: Path | None = None, episodes: list[int] | None = None) -> None:
            raise RuntimeError("network is unavailable")

    def fake_load_dataset(repo_id: str, split: str, streaming: bool):
        raise AssertionError("HF fallback should not run")

    install_fake_lerobot_module(
        monkeypatch,
        "lerobot.datasets.lerobot_dataset",
        FakeDataset,
    )
    backward_module = ModuleType("lerobot.datasets.backward_compatibility")
    backward_module.BackwardCompatibilityError = FakeBackwardCompatibilityError
    monkeypatch.setitem(sys.modules, "lerobot.datasets.backward_compatibility", backward_module)
    datasets_module = ModuleType("datasets")
    datasets_module.load_dataset = fake_load_dataset
    monkeypatch.setitem(sys.modules, "datasets", datasets_module)

    with pytest.raises(RuntimeError, match="network is unavailable"):
        load_lerobot_episode(repo_id="lerobot/fake", episode_index=0, max_frames=1)


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


def test_loader_normalizes_dataframe_like_task_metadata(monkeypatch: pytest.MonkeyPatch):
    class FakeDataFrame:
        def to_dict(self, orient: str = "dict") -> list[dict[str, object]]:
            assert orient == "records"
            return [{"task_index": 0, "task": "fake task"}]

        def __eq__(self, other: object) -> object:
            raise ValueError("truth value is ambiguous")

    class FakeDataset:
        meta = SimpleNamespace(tasks=FakeDataFrame())

        def __init__(self, repo_id: str, root: Path | None = None, episodes: list[int] | None = None) -> None:
            self.hf_dataset = [
                {
                    "episode_index": 0,
                    "frame_index": 0,
                    "timestamp": 0.0,
                    "observation.state": [1.0],
                    "action": [2.0],
                }
            ]

    install_fake_lerobot_module(
        monkeypatch,
        "lerobot.common.datasets.lerobot_dataset",
        FakeDataset,
    )

    episode = load_lerobot_episode(repo_id="lerobot/fake", episode_index=0, max_frames=1)

    assert episode.task_metadata == {"tasks": [{"task_index": 0, "task": "fake task"}]}


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


def test_loader_extracts_metadata_video_cameras_to_temporary_pngs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    from PIL import Image

    class FakeVideoFrame:
        def __init__(self, color: tuple[int, int, int]) -> None:
            self.color = color

        def to_image(self) -> Image.Image:
            return Image.new("RGB", (2, 2), self.color)

    class FakeContainer:
        def __init__(self, path: str) -> None:
            self.path = path

        def __enter__(self) -> FakeContainer:
            return self

        def __exit__(self, *exc_info: object) -> None:
            pass

        def decode(self, video: int = 0):
            assert video == 0
            color = (255, 0, 0) if "cam_high" in self.path else (0, 255, 0)
            yield FakeVideoFrame(color)
            yield FakeVideoFrame(color)

    def fake_av_open(path: str) -> FakeContainer:
        return FakeContainer(path)

    class FakeMeta:
        fps = 50.0
        root = tmp_path
        video_keys = ["observation.images.cam_high", "observation.images.cam_left_wrist"]
        features = {
            "observation.images.cam_high": {"dtype": "video"},
            "observation.images.cam_left_wrist": {"dtype": "video"},
            "observation.state": {},
            "action": {},
        }

        def get_video_file_path(self, ep_index: int, vid_key: str) -> Path:
            assert ep_index == 0
            return Path("videos") / vid_key / "chunk-000" / "file-000.mp4"

    class FakeDataset:
        meta = FakeMeta()

        def __init__(self, repo_id: str, root: Path | None = None, episodes: list[int] | None = None) -> None:
            for video_key in self.meta.video_keys:
                video_path = tmp_path / self.meta.get_video_file_path(0, video_key)
                video_path.parent.mkdir(parents=True, exist_ok=True)
                video_path.write_bytes(b"fake video")
            self.hf_dataset = [
                {
                    "episode_index": 0,
                    "frame_index": 0,
                    "timestamp": 0.0,
                    "observation.state": [],
                    "action": [],
                },
                {
                    "episode_index": 0,
                    "frame_index": 1,
                    "timestamp": 0.02,
                    "observation.state": [],
                    "action": [],
                },
            ]

    fake_av_module = ModuleType("av")
    fake_av_module.open = fake_av_open
    monkeypatch.setitem(sys.modules, "av", fake_av_module)
    install_fake_lerobot_module(
        monkeypatch,
        "lerobot.datasets.lerobot_dataset",
        FakeDataset,
    )

    episode = load_lerobot_episode(repo_id="lerobot/aloha_static_towel", episode_index=0, max_frames=2)

    assert sorted(episode.frames[0].images) == ["cam_high", "cam_left_wrist"]
    assert sorted(episode.frames[1].images) == ["cam_high", "cam_left_wrist"]
    assert all(path.suffix == ".png" and path.exists() for path in episode.frames[0].images.values())
