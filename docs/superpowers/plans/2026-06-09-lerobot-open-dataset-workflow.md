# LeRobot Open Dataset Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Stage 4 LeRobot Open Dataset Workflow: a lazy/optional LeRobot adapter that imports LeRobot episodes into Physical AI Package, validates and summarizes them, exports candidates, converts them to Rerun `.rrd`, and documents PushT plus ALOHA smoke.

**Architecture:** Add focused LeRobot modules under `src/physical_ai_data/` without changing Stage 3 default workflows. Use a small internal episode representation for unit tests and mapping, then add a lazy real LeRobot loader for `import-lerobot`. PushT is the required full acceptance dataset; ALOHA is a representative smoke with `--max-frames` and a selected camera.

**Tech Stack:** Python 3.11+, stdlib `argparse/csv/json/math/pathlib/dataclasses`, existing `numpy`, `pillow`, `rerun-sdk`, optional `lerobot`, `pytest`.

---

## 0. Context and Boundaries

Spec:

- `docs/superpowers/specs/2026-06-09-lerobot-open-dataset-workflow-design.md`

Existing Stage 3 entry points:

- `src/physical_ai_data/schema.py`
- `src/physical_ai_data/package_io.py`
- `src/physical_ai_data/validation.py`
- `src/physical_ai_data/candidates.py`
- `src/physical_ai_data/rerun_adapter.py`
- `src/physical_ai_data/cli.py`
- `scripts/physical_ai_package.py`

Project constraints:

- Use `Physical AI Package` naming in new docs/code comments/help text. Do not use the lab name as a product/schema/package name.
- Do not connect robot hardware.
- Do not train models.
- Do not modify LeRobot source.
- Do not make LeRobot a default dependency that breaks `PYTHONPATH=src python3 -m pytest -q`.
- Do not commit generated packages, `.rrd`, caches, or downloaded datasets.
- Treat Rerun as an adapter backend.
- Keep implementation surgical; preserve Stage 3 commands and tests.

## 1. File Structure

Create:

- `src/physical_ai_data/lerobot_adapter.py`
  - Public API for importing a normalized LeRobot episode into Physical AI Package.
  - Contains small dataclasses for normalized frame/episode records.
  - Contains fake-fixture-friendly package writer that does not import LeRobot.
- `src/physical_ai_data/lerobot_profiles.py`
  - Dataset profile selection and profile-specific semantic mapping for `pusht`, `aloha`, and fallback.
- `src/physical_ai_data/lerobot_loader.py`
  - Lazy real LeRobot integration. Imports `lerobot` only inside functions.
  - Converts LeRobotDataset frames into the normalized episode representation.
- `tests/physical_ai_data/test_lerobot_adapter.py`
- `tests/physical_ai_data/test_lerobot_profiles.py`
- `tests/physical_ai_data/test_lerobot_cli.py`
- `docs/stage4/README.md`
- `docs/research/06-lerobot开放数据样板链路记录.md`
- `docs/research/06-lerobot到physical-ai-package映射.md`

Modify:

- `pyproject.toml`
  - Add optional dependency group `lerobot`.
- `src/physical_ai_data/schema.py`
  - Add `open_robot_manipulation` to `SUPPORTED_SCENARIOS`.
- `src/physical_ai_data/cli.py`
  - Add `import-lerobot`.
  - Remove old lab-name wording from the CLI description; use `Physical AI Package`.
- `src/physical_ai_data/candidates.py`
  - Extend candidate keywords to catch LeRobot metrics such as `action_delta`, `timestamp_gap`, and `image_missing`.
- `src/physical_ai_data/rerun_adapter.py`
  - Optional: log `image_refs_json` additional cameras if present, without breaking existing single-image packages.
- `README.md`
  - Add Stage 4 docs links and current status.
- `details.md`
  - Record Stage 4 execution status and next steps.

Do not rename or delete Stage 3 modules.

## Task 1: Schema Support and LeRobot Normalized Models

**Files:**

- Modify: `src/physical_ai_data/schema.py`
- Create: `src/physical_ai_data/lerobot_adapter.py`
- Create: `tests/physical_ai_data/test_lerobot_adapter.py`

- [ ] **Step 1: Write failing tests for scenario support and normalized package generation**

Create `tests/physical_ai_data/test_lerobot_adapter.py` with helper fixtures:

```python
from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image

from physical_ai_data.lerobot_adapter import (
    LeRobotEpisode,
    LeRobotFrame,
    import_lerobot_episode,
)
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


def test_import_lerobot_episode_creates_valid_physical_ai_package(tmp_path: Path):
    package = import_lerobot_episode(_episode(tmp_path), tmp_path / "package", max_frames=None)

    result = validate_package(package)
    manifest = json.loads((package / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    frames = _rows(package / "frames.csv")
    metrics = _rows(package / "metrics.csv")

    assert result.ok
    assert manifest["scenario_type"] == "open_robot_manipulation"
    assert manifest["source_dataset"]["format"] == "lerobot"
    assert manifest["source_dataset"]["repo_id"] == "lerobot/pusht"
    assert manifest["source_dataset"]["profile"] == "pusht"
    assert "root" in manifest["source_dataset"] or "local_path" in manifest["source_dataset"]
    assert manifest["source_dataset"]["feature_schema_ref"] == "artifacts/source/lerobot_features.json"
    assert manifest["source_dataset"]["stats_ref"] == "artifacts/source/lerobot_stats.json"
    assert manifest["source_dataset"]["episode_metadata_ref"] == "artifacts/source/lerobot_episode_metadata.json"
    assert manifest["source_dataset"]["task_metadata_ref"] == "artifacts/source/lerobot_task_metadata.json"
    assert "converted_at" in manifest["source_dataset"]
    assert (package / "artifacts" / "source" / "lerobot_features.json").exists()
    assert (package / "artifacts" / "source" / "lerobot_stats.json").exists()
    assert (package / "artifacts" / "source" / "lerobot_episode_metadata.json").exists()
    assert (package / "artifacts" / "source" / "lerobot_task_metadata.json").exists()
    assert len(frames) == 2
    assert frames[0]["timeline"] == "sim_time"
    assert frames[0]["image_ref"] == "artifacts/images/front/frame_0000.png"
    assert any(row["metric_name"] == "action_delta" for row in metrics)


def test_import_lerobot_episode_respects_max_frames(tmp_path: Path):
    package = import_lerobot_episode(_episode(tmp_path), tmp_path / "package", max_frames=1)

    assert validate_package(package).summary["frame_count"] == 1
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_lerobot_adapter.py -q
```

Expected: FAIL because `physical_ai_data.lerobot_adapter` does not exist and `open_robot_manipulation` is unsupported.

- [ ] **Step 3: Add `open_robot_manipulation` scenario support**

Modify `src/physical_ai_data/schema.py`:

```python
SUPPORTED_SCENARIOS = {"robot_welding_station", "arm_pick_sort", "open_robot_manipulation"}
```

- [ ] **Step 4: Implement normalized dataclasses and package writer**

Create `src/physical_ai_data/lerobot_adapter.py`:

```python
from __future__ import annotations

import math
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from physical_ai_data.package_io import ensure_dir, write_csv_rows, write_json
from physical_ai_data.schema import SCHEMA_VERSION


@dataclass(frozen=True)
class LeRobotFrame:
    frame_index: int
    timestamp_s: float | None
    images: Mapping[str, Path] = field(default_factory=dict)
    state: Sequence[float] = field(default_factory=list)
    action: Sequence[float] = field(default_factory=list)


@dataclass(frozen=True)
class LeRobotEpisode:
    repo_id: str
    episode_index: int
    fps: float
    frames: Sequence[LeRobotFrame]
    task_name: str = ""
    profile: str = "fallback"
    root: Path | None = None
    features: Mapping[str, object] = field(default_factory=dict)
    stats: Mapping[str, object] = field(default_factory=dict)
    episode_metadata: Mapping[str, object] = field(default_factory=dict)
    task_metadata: Mapping[str, object] = field(default_factory=dict)


def import_lerobot_episode(
    episode: LeRobotEpisode,
    output_dir: str | Path,
    *,
    max_frames: int | None = None,
    primary_camera: str | None = None,
    copy_images: bool = True,
) -> Path:
    ...
```

Implementation requirements:

- Validate `max_frames` if provided: must be positive.
- Remove only previously generated files under the target package directories that this importer owns.
- Create:
  - `physical_ai_manifest.json`
  - `frames.csv`
  - `events.csv`
  - `labels.csv`
  - `metrics.csv`
  - `artifacts/images/<camera>/frame_XXXX.png`
  - `artifacts/source/lerobot_features.json`
  - `artifacts/source/lerobot_stats.json`
  - `artifacts/source/lerobot_episode_metadata.json`
  - `artifacts/source/lerobot_task_metadata.json`
  - `artifacts/source/frame_state_action.csv`
  - `README.md`
- Use `package_id = "lerobot_<repo_id sanitized>_episode_<episode_index>_<profile>"`.
- Use `scenario_type = "open_robot_manipulation"`.
- Include `timelines`: `sim_time` and `episode_time`.
- Include `source_dataset` manifest extension with `format`, `repo_id`, `root` or `local_path`, `episode_index`, `profile`, `feature_schema_ref`, `stats_ref`, `episode_metadata_ref`, `task_metadata_ref`, `fps`, `frame_count`, and `converted_at`.
- `frames.csv`:
  - `frame_id`: `frame_0000`, etc.
  - `timestamp_s`: source timestamp or `frame_index / fps`.
  - `phase`: profile-friendly placeholder such as `episode`.
  - `coordinate_frame_id`: `robot_base`.
  - `image_ref`: selected primary camera image.
  - `robot_state_ref`: `artifacts/source/frame_state_action.csv`.
  - `tcp_pose_ref`, `point_cloud_ref`, `trajectory_ref`: empty.
  - Add optional extension columns: `source_frame_index`, `image_refs_json`.
  - Write `frames.csv` with fieldnames `REQUIRED_TABLE_COLUMNS["frames"] + ["source_frame_index", "image_refs_json"]`; do not pass extra keys to `write_csv_rows` without extending fieldnames.
- `events.csv`: include `episode_start` and `episode_end`.
- `labels.csv`: include one conservative `task_context` label on first frame; do not invent success/failure.
- `metrics.csv`: include `action_norm`, `state_norm`, `action_delta`, `image_available`.
- Use finite numeric checks; skip non-finite state/action values in norm calculations.
- Copy source images by default. If `copy_images=False`, keep implementation simple for now: still copy and leave link mode for later implementation unless directly needed.

- [ ] **Step 5: Run adapter tests and confirm pass**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_lerobot_adapter.py -q
```

Expected: PASS.

- [ ] **Step 6: Run Stage 3 regression tests**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_validation.py tests/physical_ai_data/test_samples.py tests/physical_ai_data/test_candidates.py tests/physical_ai_data/test_rerun_adapter.py tests/physical_ai_data/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit Task 1**

```bash
git add src/physical_ai_data/schema.py src/physical_ai_data/lerobot_adapter.py tests/physical_ai_data/test_lerobot_adapter.py
git commit -m "Add LeRobot episode package adapter"
```

## Task 2: Dataset Profiles and Candidate Export Compatibility

**Files:**

- Create: `src/physical_ai_data/lerobot_profiles.py`
- Modify: `src/physical_ai_data/lerobot_adapter.py`
- Modify: `src/physical_ai_data/candidates.py`
- Create: `tests/physical_ai_data/test_lerobot_profiles.py`
- Modify: `tests/physical_ai_data/test_lerobot_adapter.py`

- [ ] **Step 1: Write failing profile tests**

Create `tests/physical_ai_data/test_lerobot_profiles.py`:

```python
from physical_ai_data.lerobot_profiles import (
    AlohaProfile,
    FallbackProfile,
    PushTProfile,
    select_lerobot_profile,
)


def test_select_lerobot_profile_from_repo_id():
    assert isinstance(select_lerobot_profile("lerobot/pusht", "auto"), PushTProfile)
    assert isinstance(select_lerobot_profile("lerobot/aloha_sim_transfer_cube_human", "auto"), AlohaProfile)
    assert isinstance(select_lerobot_profile("unknown/repo", "auto"), FallbackProfile)


def test_explicit_profile_overrides_repo_id():
    assert isinstance(select_lerobot_profile("unknown/repo", "pusht"), PushTProfile)
    assert isinstance(select_lerobot_profile("lerobot/pusht", "fallback"), FallbackProfile)


def test_unknown_explicit_profile_raises():
    try:
        select_lerobot_profile("lerobot/pusht", "not-real")
    except ValueError as exc:
        assert "Unsupported LeRobot profile" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
```

Add a test in `tests/physical_ai_data/test_lerobot_adapter.py`:

```python
def test_imported_lerobot_metrics_can_export_candidates(tmp_path: Path):
    package = import_lerobot_episode(_episode(tmp_path), tmp_path / "package", max_frames=None)

    from physical_ai_data.candidates import export_candidates

    output = export_candidates(package, min_score=0.5)
    rows = _rows(output)

    assert rows
    assert any("action_delta" in row["reasons"] for row in rows)
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_lerobot_profiles.py tests/physical_ai_data/test_lerobot_adapter.py -q
```

Expected: FAIL because profiles and LeRobot candidate metric keywords do not exist yet.

- [ ] **Step 3: Implement profiles**

Create `src/physical_ai_data/lerobot_profiles.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LeRobotProfile:
    name: str
    phase: str = "episode"

    def object_ids(self) -> list[dict[str, str]]:
        return [{"object_id": "task_object", "type": "object"}]


class PushTProfile(LeRobotProfile):
    def __init__(self) -> None:
        super().__init__(name="pusht", phase="pushing")

    def object_ids(self) -> list[dict[str, str]]:
        return [
            {"object_id": "block", "type": "object"},
            {"object_id": "target", "type": "target"},
        ]


class AlohaProfile(LeRobotProfile):
    def __init__(self) -> None:
        super().__init__(name="aloha", phase="manipulation")


class FallbackProfile(LeRobotProfile):
    def __init__(self) -> None:
        super().__init__(name="fallback", phase="episode")


def select_lerobot_profile(repo_id: str, requested: str = "auto") -> LeRobotProfile:
    ...
```

Profile selection rules:

- `requested == "auto"`:
  - repo id containing `pusht` -> `PushTProfile`
  - repo id containing `aloha` -> `AlohaProfile`
  - otherwise -> `FallbackProfile`
- explicit values: `pusht`, `aloha`, `fallback`.
- raise `ValueError` for unsupported explicit profile.

- [ ] **Step 4: Wire profiles into adapter**

Modify `src/physical_ai_data/lerobot_adapter.py`:

- Store `episode.profile` as the selected profile name.
- Use profile phase for `frames.phase`.
- Use profile objects in manifest.
- Add a warning event for fallback profile:
  - `event_type = "profile_fallback"`
  - `severity = "warning"`
  - message notes conservative mapping.

- [ ] **Step 5: Extend candidate export keywords for LeRobot metrics**

Modify `src/physical_ai_data/candidates.py`:

```python
METRIC_KEYWORDS = (
    "probability",
    "confidence",
    "risk",
    "score",
    "success",
    "action_delta",
    "timestamp_gap",
    "image_missing",
)
```

Make sure action delta values above `min_score` create candidate rows.

- [ ] **Step 6: Run profile and candidate tests**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_lerobot_profiles.py tests/physical_ai_data/test_lerobot_adapter.py tests/physical_ai_data/test_candidates.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit Task 2**

```bash
git add src/physical_ai_data/lerobot_profiles.py src/physical_ai_data/lerobot_adapter.py src/physical_ai_data/candidates.py tests/physical_ai_data/test_lerobot_profiles.py tests/physical_ai_data/test_lerobot_adapter.py
git commit -m "Add LeRobot dataset profiles"
```

## Task 3: Lazy Real LeRobot Loader

**Files:**

- Create: `src/physical_ai_data/lerobot_loader.py`
- Modify: `src/physical_ai_data/lerobot_adapter.py` if needed for normalized model compatibility
- Create: `tests/physical_ai_data/test_lerobot_loader.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing lazy import tests**

Create `tests/physical_ai_data/test_lerobot_loader.py`:

```python
from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from physical_ai_data.lerobot_loader import load_lerobot_episode


def test_loader_raises_clear_error_when_lerobot_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "lerobot", None)
    monkeypatch.setitem(sys.modules, "lerobot.common.datasets.lerobot_dataset", None)

    with pytest.raises(RuntimeError, match="Install the lerobot optional dependency"):
        load_lerobot_episode(repo_id="lerobot/pusht", episode_index=0, max_frames=1)


def test_loader_converts_fake_lerobot_dataset(monkeypatch, tmp_path):
    class FakeDataset:
        meta = SimpleNamespace(fps=10.0, features={"observation.state": {}, "action": {}})

        def __init__(self, repo_id, root=None, episodes=None):
            self.repo_id = repo_id
            self.root = root
            self.episodes = episodes
            self.hf_dataset = [
                {
                    "episode_index": 0,
                    "frame_index": 0,
                    "timestamp": 0.0,
                    "observation.state": [0.1, 0.2],
                    "action": [0.3, 0.4],
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
            ]

    fake_module = SimpleNamespace(LeRobotDataset=FakeDataset)
    monkeypatch.setitem(sys.modules, "lerobot.common.datasets.lerobot_dataset", fake_module)

    episode = load_lerobot_episode(repo_id="lerobot/fake", episode_index=0, max_frames=1)

    assert episode.repo_id == "lerobot/fake"
    assert episode.episode_index == 0
    assert episode.fps == 10.0
    assert episode.frames[0].state == [0.1, 0.2]
    assert episode.frames[0].action == [0.3, 0.4]
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_lerobot_loader.py -q
```

Expected: FAIL because `lerobot_loader.py` does not exist.

- [ ] **Step 3: Add optional dependency group**

Modify `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
  "pytest>=8",
]
lerobot = [
  "lerobot>=0.3.0",
]
```

If package name or version cannot be installed during implementation, keep the optional dependency conservative and document the observed package requirement in docs.

- [ ] **Step 4: Implement `load_lerobot_episode`**

Create `src/physical_ai_data/lerobot_loader.py`.

Public function:

```python
def load_lerobot_episode(
    *,
    repo_id: str,
    episode_index: int,
    root: str | Path | None = None,
    profile: str = "auto",
    max_frames: int | None = None,
    camera: str | None = None,
) -> LeRobotEpisode:
    ...
```

Requirements:

- Lazy import:
  - Prefer `from lerobot.common.datasets.lerobot_dataset import LeRobotDataset`.
  - If import fails, raise `RuntimeError("Install the lerobot optional dependency with ...")`.
- Instantiate `LeRobotDataset(repo_id, root=root, episodes=[episode_index])` when supported.
- Read rows from `dataset.hf_dataset` or dataset iterable.
- Filter rows by `episode_index` when rows include that key.
- Stop at `max_frames` if provided.
- Extract:
  - `frame_index`
  - `timestamp`
  - image fields with keys containing `image` or values that look path/image-like
  - `observation.state`
  - `action`
  - `task`
  - feature schema from `dataset.meta.features` or `dataset.features`
  - stats from `dataset.meta.stats` when present, else `{}`
  - episode metadata from row-level episode fields plus any available dataset episode metadata, else at least `{"episode_index": episode_index}`
  - task metadata from row `task`, `dataset.meta.tasks`, or equivalent available metadata, else `{}`
  - fps from `dataset.meta.fps`, `dataset.fps`, or fallback `30.0`
- Normalize tensor/list/numpy-like values to Python lists/floats.
- For image values:
  - If already a path, store path.
  - If PIL image or array-like, write it later through adapter support if needed. Keep first implementation path-based where possible; tests cover no-image case.
- Select profile using `select_lerobot_profile(repo_id, profile)`.

- [ ] **Step 5: Run loader tests**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_lerobot_loader.py -q
```

Expected: PASS.

- [ ] **Step 6: Run full default tests**

Run:

```bash
PYTHONPATH=src python3 -m pytest -q
```

Expected: PASS without installing or downloading real LeRobot data.

- [ ] **Step 7: Commit Task 3**

```bash
git add pyproject.toml src/physical_ai_data/lerobot_loader.py tests/physical_ai_data/test_lerobot_loader.py
git commit -m "Add lazy LeRobot dataset loader"
```

## Task 4: CLI `import-lerobot`

**Files:**

- Modify: `src/physical_ai_data/cli.py`
- Create: `tests/physical_ai_data/test_lerobot_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/physical_ai_data/test_lerobot_cli.py`:

```python
from __future__ import annotations

import subprocess
from pathlib import Path


SCRIPT = Path("scripts/physical_ai_package.py")


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", str(SCRIPT), *args], check=False, text=True, capture_output=True)


def test_import_lerobot_calls_loader_and_writes_package(monkeypatch, tmp_path: Path, capsys):
    from physical_ai_data import cli
    from physical_ai_data.lerobot_adapter import LeRobotEpisode, LeRobotFrame

    front_image = tmp_path / "front.png"
    front_image.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01"
        b"\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    episode = LeRobotEpisode(
        repo_id="lerobot/pusht",
        episode_index=0,
        fps=10.0,
        frames=[
            LeRobotFrame(
                frame_index=0,
                timestamp_s=0.0,
                state=[0.0, 1.0],
                action=[0.5, 0.25],
                images={"front": front_image},
            )
        ],
        task_name="PushT",
        profile="pusht",
        root=None,
        features={"observation.state": {"dtype": "float32", "shape": [2]}},
        stats={"observation.state": {"mean": [0.0, 0.0]}},
        episode_metadata={"episode_index": 0},
        task_metadata={"task": "PushT"},
    )

    def fake_load_lerobot_episode(**kwargs):
        assert kwargs["repo_id"] == "lerobot/pusht"
        assert kwargs["episode_index"] == 0
        assert kwargs["max_frames"] == 1
        return episode

    monkeypatch.setattr("physical_ai_data.lerobot_loader.load_lerobot_episode", fake_load_lerobot_episode)

    output_dir = tmp_path / "pkg"
    result = cli.main([
        "import-lerobot",
        "--repo-id",
        "lerobot/pusht",
        "--episode-index",
        "0",
        "--output-dir",
        str(output_dir),
        "--max-frames",
        "1",
    ])

    captured = capsys.readouterr()
    assert result == 0
    assert "Physical AI Package" in captured.out
    assert (output_dir / "physical_ai_manifest.json").exists()


def test_import_lerobot_help_lists_options():
    result = _run(["import-lerobot", "--help"])

    assert result.returncode == 0
    assert "--repo-id" in result.stdout
    assert "--episode-index" in result.stdout
    assert "--max-frames" in result.stdout
    assert "--profile" in result.stdout
```

The package-writing test must call `physical_ai_data.cli.main` with a monkeypatched `load_lerobot_episode`; default pytest must not require LeRobot installation, network, cache, or real dataset download. Keep real PushT and ALOHA dataset access only in explicit smoke commands later in this plan.

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_lerobot_cli.py -q
```

Expected: FAIL because `import-lerobot` command does not exist.

- [ ] **Step 3: Add CLI command**

Modify `src/physical_ai_data/cli.py`:

- Change the parser description from the old lab-name wording to:

```python
parser = argparse.ArgumentParser(description="Manage Physical AI Package data packages.")
```

- Add parser:

```python
import_lerobot = subcommands.add_parser("import-lerobot", help="Import a LeRobot episode into a Physical AI Package.")
import_lerobot.add_argument("--repo-id", required=True)
import_lerobot.add_argument("--episode-index", type=int, required=True)
import_lerobot.add_argument("--output-dir", type=Path, required=True)
import_lerobot.add_argument("--root", type=Path)
import_lerobot.add_argument("--profile", default="auto", choices=["auto", "pusht", "aloha", "fallback"])
import_lerobot.add_argument("--max-frames", type=int)
import_lerobot.add_argument("--camera")
import_lerobot.set_defaults(func=_import_lerobot)
```

- Implement `_import_lerobot(args)`:

```python
def _import_lerobot(args: argparse.Namespace) -> int:
    from physical_ai_data.lerobot_adapter import import_lerobot_episode
    from physical_ai_data.lerobot_loader import load_lerobot_episode

    episode = load_lerobot_episode(
        repo_id=args.repo_id,
        episode_index=args.episode_index,
        root=args.root,
        profile=args.profile,
        max_frames=args.max_frames,
        camera=args.camera,
    )
    package = import_lerobot_episode(episode, args.output_dir, max_frames=args.max_frames, primary_camera=args.camera)
    print(f"Imported LeRobot episode to Physical AI Package: {package}")
    return 0
```

Requirements:

- Keep imports lazy inside `_import_lerobot`.
- Let existing top-level `main()` catch errors and return non-zero with stderr.
- Validate `--max-frames` if provided: positive integer.

- [ ] **Step 4: Run CLI tests**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_lerobot_cli.py tests/physical_ai_data/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 5: Run all tests**

Run:

```bash
PYTHONPATH=src python3 -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 4**

```bash
git add src/physical_ai_data/cli.py tests/physical_ai_data/test_lerobot_cli.py
git commit -m "Add LeRobot import CLI"
```

## Task 5: Rerun Adapter Support for Imported Multi-Camera Metadata

**Files:**

- Modify: `src/physical_ai_data/rerun_adapter.py`
- Modify: `tests/physical_ai_data/test_rerun_adapter.py`
- Modify: `tests/physical_ai_data/test_lerobot_adapter.py`

- [ ] **Step 1: Write failing multi-camera Rerun tests**

Add to `tests/physical_ai_data/test_lerobot_adapter.py`:

```python
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

    package = import_lerobot_episode(episode, tmp_path / "package")
    row = _rows(package / "frames.csv")[0]

    assert "image_refs_json" in row
    assert "side" in row["image_refs_json"]
```

Add to `tests/physical_ai_data/test_rerun_adapter.py` a test that a package with `image_refs_json` still writes and verifies `.rrd`.

- [ ] **Step 2: Run tests and confirm failure or insufficient behavior**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_lerobot_adapter.py tests/physical_ai_data/test_rerun_adapter.py -q
```

Expected: FAIL if `image_refs_json` is not emitted or ignored in Rerun adapter.

- [ ] **Step 3: Emit `image_refs_json` from LeRobot adapter**

Modify `src/physical_ai_data/lerobot_adapter.py`:

- Add `image_refs_json` as an extension column in `frames.csv`.
- Store JSON object mapping camera name to package-relative image path.
- Keep `image_ref` as selected primary camera path.
- Ensure the `frames.csv` writer uses fieldnames `REQUIRED_TABLE_COLUMNS["frames"] + ["source_frame_index", "image_refs_json"]` so `csv.DictWriter` does not reject extension keys.

- [ ] **Step 4: Log additional camera images in Rerun adapter**

Modify `src/physical_ai_data/rerun_adapter.py`:

- In `_log_frames`, parse `image_refs_json` if present.
- For each camera path:
  - skip if same as primary `image_ref`;
  - log under `f"{frame_path}/images/{_safe_entity_name(camera_name)}"`;
  - handle invalid JSON by ignoring it, not failing a valid package.
- Keep existing single `image_ref` behavior unchanged.

- [ ] **Step 5: Run Rerun and LeRobot adapter tests**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_lerobot_adapter.py tests/physical_ai_data/test_rerun_adapter.py -q
```

Expected: PASS.

- [ ] **Step 6: Run all physical_ai_data tests**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data -q
```

Expected: PASS.

- [ ] **Step 7: Commit Task 5**

```bash
git add src/physical_ai_data/lerobot_adapter.py src/physical_ai_data/rerun_adapter.py tests/physical_ai_data/test_lerobot_adapter.py tests/physical_ai_data/test_rerun_adapter.py
git commit -m "Support LeRobot multi-camera package refs"
```

## Task 6: Stage 4 Mapping Docs, Smoke Commands, and Status Updates

**Files:**

- Create: `docs/stage4/README.md`
- Create: `docs/research/06-lerobot开放数据样板链路记录.md`
- Create: `docs/research/06-lerobot到physical-ai-package映射.md`
- Modify: `README.md`
- Modify: `details.md`

- [ ] **Step 1: Write Stage 4 run docs**

Create `docs/stage4/README.md` in Chinese with:

- Stage 4 goal.
- Install default dev command:

```bash
python3 -m pip install -e ".[dev]"
```

- Optional LeRobot command:

```bash
python3 -m pip install -e ".[dev,lerobot]"
```

- PushT full acceptance import:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/pusht \
  --episode-index 0 \
  --output-dir artifacts/stage4/pusht_episode_0000 \
  --profile pusht
```

- Optional quick PushT import for local iteration:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/pusht \
  --episode-index 0 \
  --output-dir artifacts/stage4/pusht_quick_episode_0000 \
  --profile pusht \
  --max-frames 120
```

- ALOHA smoke import:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/aloha_sim_transfer_cube_human \
  --episode-index 0 \
  --output-dir artifacts/stage4/aloha_smoke_episode_0000 \
  --profile aloha \
  --max-frames 60
```

- Shared commands:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage4/pusht_episode_0000 --json
PYTHONPATH=src python3 scripts/physical_ai_package.py summarize artifacts/stage4/pusht_episode_0000 --json
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage4/pusht_episode_0000
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage4/pusht_episode_0000 --output-rrd artifacts/stage4/pusht_episode_0000.rrd
rerun rrd verify artifacts/stage4/pusht_episode_0000.rrd
```

- Known limits:
  - no hardware;
  - no training;
  - real LeRobot smoke may depend on network/dataset availability;
  - ALOHA smoke is compatibility smoke, not full semantic mapping.

- [ ] **Step 2: Write mapping document**

Create `docs/research/06-lerobot到physical-ai-package映射.md` in Chinese with:

- LeRobot source fields.
- Physical AI Package manifest mapping.
- frames/events/labels/metrics mapping.
- image/state/action artifact mapping.
- PushT profile mapping.
- ALOHA profile mapping.
- fallback profile behavior.
- fields intentionally not inferred.

- [ ] **Step 3: Write implementation record placeholder**

Create `docs/research/06-lerobot开放数据样板链路记录.md` in Chinese with:

- Stage goal.
- Implemented capability.
- Unit test results placeholder.
- PushT full acceptance result placeholder.
- PushT quick smoke result placeholder, if full acceptance is blocked by size/time.
- ALOHA smoke placeholder.
- Risks and limits.
- Next steps.

Do not claim real smoke results until Step 5 actually runs.

- [ ] **Step 4: Update README and details**

Modify `README.md`:

- Add Stage 4 docs links.
- Current status: Stage 4 LeRobot adapter implemented or in progress depending on actual implementation state.
- Use `Physical AI Package` naming.

Modify `details.md`:

- Add dated Stage 4 implementation bullets.
- Next steps: real smoke result calibration, Viewer checks, SDK wrapper, training/evaluation export.

- [ ] **Step 5: Run verification and real smoke where available**

Always run:

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot --help
```

Then try PushT full acceptance if optional dependency, dataset access, and local time budget are available:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/pusht \
  --episode-index 0 \
  --output-dir artifacts/stage4/final_pusht_episode_0000 \
  --profile pusht
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage4/final_pusht_episode_0000 --json
PYTHONPATH=src python3 scripts/physical_ai_package.py summarize artifacts/stage4/final_pusht_episode_0000 --json
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage4/final_pusht_episode_0000
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage4/final_pusht_episode_0000 --output-rrd artifacts/stage4/final_pusht_episode_0000.rrd
rerun rrd verify artifacts/stage4/final_pusht_episode_0000.rrd
```

Then try ALOHA representative smoke if feasible:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/aloha_sim_transfer_cube_human \
  --episode-index 0 \
  --output-dir artifacts/stage4/final_aloha_smoke_episode_0000 \
  --profile aloha \
  --max-frames 60
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage4/final_aloha_smoke_episode_0000 --json
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage4/final_aloha_smoke_episode_0000 --output-rrd artifacts/stage4/final_aloha_smoke_episode_0000.rrd
rerun rrd verify artifacts/stage4/final_aloha_smoke_episode_0000.rrd
```

If real smoke cannot run because optional dependency, dataset availability, auth, network, or size blocks it:

- Do not mark real smoke as passed.
- If only full PushT is blocked by size/time, run the quick PushT command with `--max-frames 120` and record it as quick smoke, not full acceptance.
- Record the exact blocker in `docs/research/06-lerobot开放数据样板链路记录.md`.
- Keep unit tests and fake-fixture smoke passing.

- [ ] **Step 6: Update implementation record with real results**

Update `docs/research/06-lerobot开放数据样板链路记录.md` with:

- exact pytest result;
- exact PushT full acceptance result or blocker;
- exact PushT quick smoke result if full acceptance is blocked by size/time and quick smoke was run;
- exact ALOHA smoke result or blocker;
- generated candidate counts if smoke ran;
- `.rrd` verify result if smoke ran;
- known limits.

- [ ] **Step 7: Run docs/status checks**

Run:

```bash
rg -n "LeRobot|Physical AI Package|stage4|pusht|ALOHA|CavLAB|待最终" README.md details.md docs/stage4/README.md docs/research/06-lerobot开放数据样板链路记录.md docs/research/06-lerobot到physical-ai-package映射.md src/physical_ai_data/cli.py src/physical_ai_data/lerobot_adapter.py src/physical_ai_data/lerobot_loader.py src/physical_ai_data/lerobot_profiles.py
git diff --check
git status --short --branch
```

Expected:

- New docs visible.
- No new lab-name usage in Stage 4 docs except the `rg` check proves none.
- No whitespace errors.
- Generated artifacts remain ignored.

- [ ] **Step 8: Commit Task 6**

```bash
git add README.md details.md docs/stage4/README.md docs/research/06-lerobot开放数据样板链路记录.md docs/research/06-lerobot到physical-ai-package映射.md
git commit -m "Document LeRobot open dataset workflow"
```

## Final Verification

After all tasks complete, use `superpowers:verification-before-completion`.

Run:

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot --help
git diff --check
git status --short --branch
```

If real PushT/ALOHA smoke ran, also verify the final `.rrd` outputs:

```bash
rerun rrd verify artifacts/stage4/final_pusht_episode_0000.rrd
rerun rrd verify artifacts/stage4/final_aloha_smoke_episode_0000.rrd
```

Expected:

- default tests pass;
- Stage 3 workflows remain usable;
- LeRobot import CLI is present;
- docs record real smoke results or exact blockers;
- worktree is clean after final commit;
- no generated artifacts are tracked.
