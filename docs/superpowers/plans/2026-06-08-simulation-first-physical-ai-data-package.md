# Simulation-first Physical AI Data Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking and are now marked complete.

**Goal:** Build the Stage 3 simulation-first Physical AI data package prototype: CavLAB package v0.1 schema, validator, two simulation sample packages, Rerun adapter, candidate export, CLI, tests, and docs.

**Completion note:** This plan has been executed. Final smoke results and remaining follow-up items are recorded in `docs/research/05-physical-ai数据包阶段三实施记录.md`.

**Architecture:** Add a new `physical_ai_data` Python package beside the existing `rerun_stage2` experiment package. `physical_ai_data` owns the CavLAB package schema, package IO, validator, sample generators, candidate export, summary, Rerun adapter, and CLI; `rerun_stage2` remains the Stage 2 Rerun evaluation implementation. The default flow is: generate package -> validate package -> summarize/export candidates -> convert to Rerun `.rrd`.

**Tech Stack:** Python 3.11+, stdlib `csv/json/pathlib/dataclasses/argparse`, existing dependencies `numpy`, `pillow`, `rerun-sdk`, `pytest`.

---

## 0. Context and Boundaries

Design spec:

- `docs/superpowers/specs/2026-06-08-simulation-first-physical-ai-data-package-design.md`

Project constraints:

- Use Chinese for project-facing docs.
- Keep changes surgical and focused on Stage 3.
- Do not connect robot hardware.
- Do not introduce ROS/Gazebo/MoveIt.
- Do not build a database, Web platform, permissions system, or production governance system.
- Treat Rerun as an adapter backend, not the CavLAB business schema.
- Generated packages, `.rrd`, and local artifacts remain under `artifacts/` and are not committed.
- Implementation tasks follow TDD: write failing tests, verify failure, implement, verify pass, commit.

## 1. File Structure

Create:

- `src/physical_ai_data/__init__.py`
  - Package version and public module docstring.
- `src/physical_ai_data/schema.py`
  - Constants for schema version, supported scenarios, required manifest fields, table columns, candidate columns, and reference rules.
  - Small dataclasses for validation messages/results and package summary.
- `src/physical_ai_data/package_io.py`
  - JSON/CSV read/write helpers, package path helpers, nearest-frame lookup helpers.
- `src/physical_ai_data/validation.py`
  - Validator implementation for CavLAB Physical AI package v0.1.
- `src/physical_ai_data/samples.py`
  - Deterministic generators for `robot_welding_station` and `arm_pick_sort` packages.
- `src/physical_ai_data/candidates.py`
  - Candidate sample export from CavLAB package tables.
- `src/physical_ai_data/rerun_adapter.py`
  - Convert validated CavLAB package to Rerun `.rrd`.
- `src/physical_ai_data/cli.py`
  - CLI subcommands for generation, validation, summary, candidate export, and Rerun conversion.
- `scripts/physical_ai_package.py`
  - Thin wrapper around `physical_ai_data.cli.main`.
- `tests/physical_ai_data/test_validation.py`
- `tests/physical_ai_data/test_samples.py`
- `tests/physical_ai_data/test_candidates.py`
- `tests/physical_ai_data/test_rerun_adapter.py`
- `tests/physical_ai_data/test_cli.py`
- `docs/stage3/README.md`
- `docs/research/05-physical-ai数据包阶段三实施记录.md`

Modify:

- `README.md`
  - Add Stage 3 running docs and report links.
- `details.md`
  - Record plan creation and implementation status.

Do not rename or delete existing `rerun_stage2` modules.

## Task 1: Core Schema, Package IO, and Validator

**Files:**

- Create: `src/physical_ai_data/__init__.py`
- Create: `src/physical_ai_data/schema.py`
- Create: `src/physical_ai_data/package_io.py`
- Create: `src/physical_ai_data/validation.py`
- Create: `tests/physical_ai_data/test_validation.py`

- [x] **Step 1: Write failing validator tests**

Create `tests/physical_ai_data/test_validation.py`:

```python
from __future__ import annotations

import csv
import json
from pathlib import Path

from physical_ai_data.validation import validate_package


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_minimal_package(root: Path) -> None:
    (root / "artifacts" / "images").mkdir(parents=True)
    (root / "artifacts" / "images" / "frame_0000.png").write_bytes(b"placeholder")
    manifest = {
        "schema_version": "physical-ai-package/v0.1",
        "package_id": "pkg_test_001",
        "scenario_type": "robot_welding_station",
        "created_at": "2026-06-08T00:00:00Z",
        "task": {"task_id": "task_001", "name": "test"},
        "devices": [{"device_id": "robot_001", "type": "robot_arm"}],
        "objects": [{"object_id": "workpiece_001", "type": "workpiece"}],
        "coordinate_frames": [
            {"frame_id": "station", "parent_frame_id": "", "pose_ref": ""},
            {"frame_id": "tcp", "parent_frame_id": "station", "pose_ref": ""},
        ],
        "timelines": [{"timeline_id": "sim_time", "unit": "s"}],
        "tables": {
            "frames": "frames.csv",
            "events": "events.csv",
            "labels": "labels.csv",
            "metrics": "metrics.csv",
        },
        "artifacts": {"images": "artifacts/images"},
    }
    (root / "physical_ai_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _write_csv(
        root / "frames.csv",
        [
            "frame_id",
            "timestamp_s",
            "timeline",
            "phase",
            "coordinate_frame_id",
            "robot_state_ref",
            "tcp_pose_ref",
            "image_ref",
            "point_cloud_ref",
            "trajectory_ref",
        ],
        [
            {
                "frame_id": "frame_0000",
                "timestamp_s": 0.0,
                "timeline": "sim_time",
                "phase": "test",
                "coordinate_frame_id": "tcp",
                "robot_state_ref": "",
                "tcp_pose_ref": "",
                "image_ref": "artifacts/images/frame_0000.png",
                "point_cloud_ref": "",
                "trajectory_ref": "",
            }
        ],
    )
    _write_csv(
        root / "events.csv",
        ["event_id", "timestamp_s", "event_type", "severity", "message", "related_frame_id", "related_object_id"],
        [{"event_id": "event_0000", "timestamp_s": 0.0, "event_type": "start", "severity": "info", "message": "start", "related_frame_id": "frame_0000", "related_object_id": ""}],
    )
    _write_csv(
        root / "labels.csv",
        ["label_id", "label_type", "target_ref", "value", "confidence", "source"],
        [{"label_id": "label_0000", "label_type": "quality", "target_ref": "frame:frame_0000", "value": "ok", "confidence": 1.0, "source": "sim"}],
    )
    _write_csv(
        root / "metrics.csv",
        ["metric_id", "timestamp_s", "metric_name", "value", "unit", "source"],
        [{"metric_id": "metric_0000", "timestamp_s": 0.0, "metric_name": "score", "value": 0.1, "unit": "ratio", "source": "sim"}],
    )


def test_valid_minimal_package_passes(tmp_path: Path):
    _write_minimal_package(tmp_path)

    result = validate_package(tmp_path)

    assert result.ok
    assert result.summary["scenario_type"] == "robot_welding_station"
    assert result.summary["frame_count"] == 1
    assert result.errors == []


def test_missing_manifest_reports_error(tmp_path: Path):
    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "missing_manifest" for error in result.errors)


def test_missing_required_table_column_reports_error(tmp_path: Path):
    _write_minimal_package(tmp_path)
    _write_csv(tmp_path / "frames.csv", ["frame_id"], [{"frame_id": "frame_0000"}])

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "missing_table_columns" and "timestamp_s" in error.message for error in result.errors)


def test_non_empty_ref_must_exist(tmp_path: Path):
    _write_minimal_package(tmp_path)
    rows = list(csv.DictReader((tmp_path / "frames.csv").open(newline="", encoding="utf-8")))
    rows[0]["image_ref"] = "artifacts/images/missing.png"
    _write_csv(tmp_path / "frames.csv", list(rows[0].keys()), rows)

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "missing_artifact_ref" for error in result.errors)


def test_manifest_pose_ref_must_exist_when_non_empty(tmp_path: Path):
    _write_minimal_package(tmp_path)
    manifest = json.loads((tmp_path / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    manifest["coordinate_frames"][1]["pose_ref"] = "artifacts/poses/missing_tcp_pose.csv"
    (tmp_path / "physical_ai_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "missing_artifact_ref" and "pose_ref" in error.message for error in result.errors)


def test_events_and_metrics_timestamp_must_be_numeric(tmp_path: Path):
    _write_minimal_package(tmp_path)
    _write_csv(
        tmp_path / "events.csv",
        ["event_id", "timestamp_s", "event_type", "severity", "message", "related_frame_id", "related_object_id"],
        [{"event_id": "event_0000", "timestamp_s": "not-a-number", "event_type": "start", "severity": "info", "message": "start", "related_frame_id": "frame_0000", "related_object_id": ""}],
    )
    _write_csv(
        tmp_path / "metrics.csv",
        ["metric_id", "timestamp_s", "metric_name", "value", "unit", "source"],
        [{"metric_id": "metric_0000", "timestamp_s": "also-bad", "metric_name": "score", "value": 0.1, "unit": "ratio", "source": "sim"}],
    )

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "invalid_timestamp" and "events.csv" in error.message for error in result.errors)
    assert any(error.code == "invalid_timestamp" and "metrics.csv" in error.message for error in result.errors)


def test_missing_recommended_artifact_directory_reports_warning(tmp_path: Path):
    _write_minimal_package(tmp_path)
    (tmp_path / "artifacts" / "point_clouds").rmdir() if (tmp_path / "artifacts" / "point_clouds").exists() else None

    result = validate_package(tmp_path)

    assert result.ok
    assert any(warning.code == "missing_recommended_artifact_dir" for warning in result.warnings)


def test_timelines_must_include_sim_time(tmp_path: Path):
    _write_minimal_package(tmp_path)
    manifest = json.loads((tmp_path / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    manifest["timelines"] = [{"timeline_id": "robot_tick", "unit": "tick"}]
    (tmp_path / "physical_ai_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_package(tmp_path)

    assert not result.ok
    assert any(error.code == "missing_sim_time" for error in result.errors)
```

- [x] **Step 2: Run validator tests and confirm they fail**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_validation.py -q
```

Expected: FAIL because `physical_ai_data` does not exist.

- [x] **Step 3: Implement schema constants and validation result types**

Create `src/physical_ai_data/__init__.py`:

```python
"""CavLAB Physical AI data package utilities."""

__version__ = "0.1.0"
```

Create `src/physical_ai_data/schema.py` with:

- `SCHEMA_VERSION = "physical-ai-package/v0.1"`
- `SUPPORTED_SCENARIOS = {"robot_welding_station", "arm_pick_sort"}`
- `REQUIRED_MANIFEST_FIELDS`
- `REQUIRED_TABLE_COLUMNS`
- `CANDIDATE_COLUMNS`
- dataclasses:
  - `ValidationMessage(code: str, message: str, path: str = "")`
  - `ValidationResult(errors: list[ValidationMessage], warnings: list[ValidationMessage], summary: dict[str, object])`
  - `ValidationResult.ok` property returns `not errors`

- [x] **Step 4: Implement package IO helpers**

Create `src/physical_ai_data/package_io.py`:

- `read_json(path: Path) -> dict[str, object]`
- `write_json(path: Path, payload: Mapping[str, object]) -> None`
- `read_csv_rows(path: Path) -> list[dict[str, str]]`
- `write_csv_rows(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None`
- `nearest_frame_id(frames, timestamp_s) -> str`
- `ensure_dir(path: Path) -> None`

Keep helpers small and dependency-free.

- [x] **Step 5: Implement validator**

Create `src/physical_ai_data/validation.py`:

- `validate_package(package_root: str | Path) -> ValidationResult`
- Check:
  - package root exists;
  - `physical_ai_manifest.json` exists and parses;
  - required manifest fields exist;
  - `schema_version` matches v0.1;
  - `scenario_type` is supported;
  - `timelines` contains `sim_time`;
  - `coordinate_frames` entries have `frame_id`, `parent_frame_id`, `pose_ref`;
  - declared table files exist;
  - required table columns exist;
  - `frames.timestamp_s`, `events.timestamp_s`, and `metrics.timestamp_s` are numeric;
  - key IDs are non-empty;
  - `frames.timeline` exists in manifest timelines;
  - `frames.coordinate_frame_id` exists in manifest coordinate frames;
  - non-empty `_ref` file references point to existing package-relative files, including `frames.*_ref` fields and `coordinate_frames.pose_ref`;
  - `labels.target_ref` starts with `frame:` or `object:`.
  - missing recommended artifact directories such as `artifacts/point_clouds` or `artifacts/trajectories` produce warnings, not errors.
- Produce summary:
  - `package_id`, `scenario_type`, `frame_count`, `event_count`, `label_count`, `metric_count`, `artifact_ref_count`.

- [x] **Step 6: Run tests and confirm pass**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_validation.py -q
```

Expected: PASS.

- [x] **Step 7: Commit Task 1**

```bash
git add src/physical_ai_data/__init__.py src/physical_ai_data/schema.py src/physical_ai_data/package_io.py src/physical_ai_data/validation.py tests/physical_ai_data/test_validation.py
git commit -m "Add physical AI package validator"
```

## Task 2: Deterministic Simulation Package Generators

**Files:**

- Create: `src/physical_ai_data/samples.py`
- Create: `tests/physical_ai_data/test_samples.py`
- Modify: `src/physical_ai_data/package_io.py` if additional write helper is needed

- [x] **Step 1: Write failing sample generation tests**

Create `tests/physical_ai_data/test_samples.py`:

```python
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
```

- [x] **Step 2: Run sample tests and confirm failure**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_samples.py -q
```

Expected: FAIL because `physical_ai_data.samples` does not exist.

- [x] **Step 3: Implement welding package generator**

Create `generate_welding_package(root: str | Path, frame_count: int = 60, random_seed: int = 42) -> Path`.

Implementation guidance:

- Use deterministic math/random, following the Stage 2 weld trajectory idea.
- Output v0.1 package structure:
  - `physical_ai_manifest.json`
  - `frames.csv`
  - `events.csv`
  - `labels.csv`
  - `metrics.csv`
  - `artifacts/images/*.png`
  - `artifacts/point_clouds/workpiece.csv`
  - `artifacts/trajectories/tcp_path.csv`
  - `README.md`
- Required manifest values:
  - `scenario_type = "robot_welding_station"`
  - `timelines` includes `sim_time`
  - coordinate frames include `station`, `robot_base`, `tcp`, `camera_front`, `workpiece`
- Required semantic content:
  - frames include approach/welding/finish phases;
  - one start event, one end event, at least one risk event;
  - labels include at least one `quality` label;
  - metrics include `weld_current`, `weld_voltage`, `defect_probability`.

- [x] **Step 4: Implement pick/sort package generator**

Create `generate_pick_sort_package(root: str | Path, frame_count: int = 40, random_seed: int = 42) -> Path`.

Required content:

- `scenario_type = "arm_pick_sort"`
- coordinate frames include `station`, `robot_base`, `tcp`, `camera_front`, `bin_source`, `bin_target`
- phases include `observe`, `approach`, `grasp`, `transfer`, `place`, `finish`
- events include `object_detected`, `grasp_attempt`, `place_success` or `place_failure`
- labels include success/failure label using `frame:<frame_id>`
- metrics include `grip_confidence`, `object_confidence`
- deterministic generated images under `artifacts/images/`

- [x] **Step 5: Run sample tests and confirm pass**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_samples.py -q
```

Expected: PASS.

- [x] **Step 6: Run validator tests again**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_validation.py tests/physical_ai_data/test_samples.py -q
```

Expected: PASS.

- [x] **Step 7: Commit Task 2**

```bash
git add src/physical_ai_data/samples.py src/physical_ai_data/package_io.py tests/physical_ai_data/test_samples.py
git commit -m "Add physical AI simulation package generators"
```

## Task 3: Candidate Export and Package Summary

**Files:**

- Create: `src/physical_ai_data/candidates.py`
- Modify: `src/physical_ai_data/package_io.py` if needed
- Create: `tests/physical_ai_data/test_candidates.py`

- [x] **Step 1: Write failing candidate export tests**

Create `tests/physical_ai_data/test_candidates.py`:

```python
import csv
from pathlib import Path

from physical_ai_data.candidates import export_candidates, summarize_package
from physical_ai_data.samples import generate_pick_sort_package, generate_welding_package
from physical_ai_data.schema import CANDIDATE_COLUMNS


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def test_export_welding_candidates_creates_stable_csv(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=18, random_seed=5)

    output = export_candidates(package, min_score=0.5)
    rows = _rows(output)

    assert output == package / "derived" / "candidates.csv"
    assert rows
    assert list(rows[0].keys()) == CANDIDATE_COLUMNS
    assert any(row["source_type"] in {"event", "metric", "mixed"} for row in rows)
    assert all(row["frame_id"] for row in rows if row["source_type"] != "label")


def test_export_pick_sort_candidates_includes_label_or_event(tmp_path: Path):
    package = generate_pick_sort_package(tmp_path / "pick", frame_count=12, random_seed=4)

    output = export_candidates(package, min_score=0.5)
    rows = _rows(output)

    assert rows
    assert any(row["source_type"] in {"event", "label", "mixed"} for row in rows)


def test_summarize_package_returns_counts(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=8, random_seed=2)

    summary = summarize_package(package)

    assert summary["scenario_type"] == "robot_welding_station"
    assert summary["frame_count"] == 8
    assert summary["event_count"] >= 2
```

- [x] **Step 2: Run candidate tests and confirm failure**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_candidates.py -q
```

Expected: FAIL because `physical_ai_data.candidates` does not exist.

- [x] **Step 3: Implement candidate export**

Create `src/physical_ai_data/candidates.py`:

- `summarize_package(package_root: str | Path) -> dict[str, object]`
  - May call `validate_package`; if invalid, raise `ValueError` with error summary.
  - Return scenario, package ID, counts, phase list, event types, label types, metric names.
- `export_candidates(package_root: str | Path, output_csv: str | Path | None = None, min_score: float = 0.5) -> Path`
  - Read `frames.csv`, `events.csv`, `labels.csv`, `metrics.csv`.
  - Event candidates:
    - include warning/error/risk/failure/success style events;
    - use `related_frame_id` or nearest `sim_time` frame.
  - Label candidates:
    - include labels with confidence >= `min_score`;
    - support `frame:<frame_id>` and `object:<object_id>`.
  - Metric candidates:
    - include metric rows where numeric value >= `min_score` and metric name contains `probability`, `confidence`, `risk`, `score`, or `success`.
  - Merge duplicate frame-level candidates into one row with `source_type = "mixed"` and joined reasons.
  - Write columns exactly as `CANDIDATE_COLUMNS`.

- [x] **Step 4: Run candidate tests and confirm pass**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_candidates.py -q
```

Expected: PASS.

- [x] **Step 5: Run related tests**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_validation.py tests/physical_ai_data/test_samples.py tests/physical_ai_data/test_candidates.py -q
```

Expected: PASS.

- [x] **Step 6: Commit Task 3**

```bash
git add src/physical_ai_data/candidates.py tests/physical_ai_data/test_candidates.py
git commit -m "Add physical AI candidate export"
```

## Task 4: Rerun Adapter for CavLAB Packages

**Files:**

- Create: `src/physical_ai_data/rerun_adapter.py`
- Create: `tests/physical_ai_data/test_rerun_adapter.py`

- [x] **Step 1: Write failing Rerun adapter tests**

Create `tests/physical_ai_data/test_rerun_adapter.py`:

```python
import subprocess
from pathlib import Path

from physical_ai_data.rerun_adapter import write_rrd
from physical_ai_data.samples import generate_pick_sort_package, generate_welding_package


def test_write_welding_rrd_and_verify(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=8, random_seed=8)
    output = tmp_path / "weld.rrd"

    result = write_rrd(package, output)

    assert result == output
    assert output.exists()
    verify = subprocess.run(["rerun", "rrd", "verify", str(output)], check=False, text=True, capture_output=True)
    assert verify.returncode == 0, verify.stderr + verify.stdout


def test_write_pick_sort_rrd_and_verify(tmp_path: Path):
    package = generate_pick_sort_package(tmp_path / "pick", frame_count=8, random_seed=9)
    output = tmp_path / "pick.rrd"

    result = write_rrd(package, output)

    assert result == output
    assert output.exists()
    verify = subprocess.run(["rerun", "rrd", "verify", str(output)], check=False, text=True, capture_output=True)
    assert verify.returncode == 0, verify.stderr + verify.stdout
```

- [x] **Step 2: Run adapter tests and confirm failure**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_rerun_adapter.py -q
```

Expected: FAIL because `physical_ai_data.rerun_adapter` does not exist.

- [x] **Step 3: Implement Rerun adapter**

Create `src/physical_ai_data/rerun_adapter.py`:

- `write_rrd(package_root: str | Path, output_rrd: str | Path) -> Path`
- Import `rerun`, `numpy`, and `PIL.Image` lazily inside functions.
- Validate package first; raise `ValueError` if invalid.
- Write to temp sibling file and atomically replace output.
- Reference `src/rerun_stage2/rerun_writer.py` for Rerun SDK compatibility patterns such as `rr.set_time`, Transform3D constructor fallbacks, `TextLog` fallback, and atomic `.rrd` writing.
- Log:
  - coordinate frames as Transform3D;
  - images as `rr.Image`;
  - point clouds as `rr.Points3D` when CSV artifact has `x,y,z`;
  - trajectories as `rr.LineStrips3D` when CSV artifact has `x,y,z`;
  - metrics as `rr.Scalars`;
  - events as `rr.TextLog` or fallback `rr.TextDocument`;
  - labels as text under `/labels`.
- Set timeline:
  - use `rr.set_time("sim_time", duration=timestamp_s)` for frames/events/metrics.
- Use default entity paths:
  - `/package/<scenario_type>/frames/...`
  - `/package/<scenario_type>/metrics/<metric_name>`
  - `/package/<scenario_type>/events`
  - `/package/<scenario_type>/labels`

- [x] **Step 4: Run adapter tests and confirm pass**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_rerun_adapter.py -q
```

Expected: PASS.

- [x] **Step 5: Run all physical_ai_data tests**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data -q
```

Expected: PASS.

- [x] **Step 6: Commit Task 4**

```bash
git add src/physical_ai_data/rerun_adapter.py tests/physical_ai_data/test_rerun_adapter.py
git commit -m "Add physical AI Rerun adapter"
```

## Task 5: CLI Wrapper and End-to-End Commands

**Files:**

- Create: `src/physical_ai_data/cli.py`
- Create: `scripts/physical_ai_package.py`
- Create: `tests/physical_ai_data/test_cli.py`

- [x] **Step 1: Write failing CLI tests**

Create `tests/physical_ai_data/test_cli.py`:

```python
import json
import subprocess
from pathlib import Path


SCRIPT = Path("scripts/physical_ai_package.py")


def test_cli_generate_validate_summarize_and_export(tmp_path: Path):
    package = tmp_path / "weld"

    generate = subprocess.run(
        ["python3", str(SCRIPT), "generate", "welding", "--output-dir", str(package), "--frames", "8"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert generate.returncode == 0, generate.stderr

    validate = subprocess.run(
        ["python3", str(SCRIPT), "validate", str(package), "--json"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert validate.returncode == 0, validate.stderr
    payload = json.loads(validate.stdout)
    assert payload["ok"] is True

    summarize = subprocess.run(
        ["python3", str(SCRIPT), "summarize", str(package), "--json"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert summarize.returncode == 0, summarize.stderr
    assert json.loads(summarize.stdout)["frame_count"] == 8

    export = subprocess.run(
        ["python3", str(SCRIPT), "export-candidates", str(package)],
        check=False,
        text=True,
        capture_output=True,
    )
    assert export.returncode == 0, export.stderr
    assert (package / "derived" / "candidates.csv").exists()


def test_cli_convert_rerun(tmp_path: Path):
    package = tmp_path / "pick"
    output_rrd = tmp_path / "pick.rrd"

    subprocess.run(
        ["python3", str(SCRIPT), "generate", "pick-sort", "--output-dir", str(package), "--frames", "8"],
        check=True,
        text=True,
        capture_output=True,
    )
    convert = subprocess.run(
        ["python3", str(SCRIPT), "convert-rerun", str(package), "--output-rrd", str(output_rrd)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert convert.returncode == 0, convert.stderr
    assert output_rrd.exists()


def test_cli_invalid_package_returns_nonzero(tmp_path: Path):
    validate = subprocess.run(
        ["python3", str(SCRIPT), "validate", str(tmp_path)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert validate.returncode != 0
    assert "missing_manifest" in validate.stdout or "missing_manifest" in validate.stderr
```

- [x] **Step 2: Run CLI tests and confirm failure**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_cli.py -q
```

Expected: FAIL because CLI does not exist.

- [x] **Step 3: Implement CLI**

Create `src/physical_ai_data/cli.py` using `argparse`.

Required commands:

- `generate welding --output-dir PATH --frames N --seed N`
- `generate pick-sort --output-dir PATH --frames N --seed N`
- `validate PACKAGE [--json]`
- `summarize PACKAGE [--json]`
- `export-candidates PACKAGE [--output-csv PATH] [--min-score FLOAT]`
- `convert-rerun PACKAGE --output-rrd PATH`

Behavior:

- `validate` returns exit code `0` if ok, `1` if errors.
- `--json` emits machine-readable JSON.
- Human output must be concise and include key paths.
- Bad arguments use argparse default non-zero behavior.

Create `scripts/physical_ai_package.py`:

```python
#!/usr/bin/env python3
from physical_ai_data.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run CLI tests and confirm pass**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/physical_ai_data/test_cli.py -q
```

Expected: PASS.

- [x] **Step 5: Run all tests**

Run:

```bash
PYTHONPATH=src python3 -m pytest -q
```

Expected: PASS.

- [x] **Step 6: Commit Task 5**

```bash
git add src/physical_ai_data/cli.py scripts/physical_ai_package.py tests/physical_ai_data/test_cli.py
git commit -m "Add physical AI package CLI"
```

## Task 6: Stage 3 Docs, Smoke Verification, and Status Updates

**Files:**

- Create: `docs/stage3/README.md`
- Create: `docs/research/05-physical-ai数据包阶段三实施记录.md`
- Modify: `README.md`
- Modify: `details.md`

- [x] **Step 1: Write Stage 3 run docs**

Create `docs/stage3/README.md` in Chinese with:

- Stage 3 goal.
- Install command:

```bash
python3 -m pip install -e ".[dev]"
```

- Generate welding package:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py generate welding --output-dir artifacts/stage3/weld_demo --frames 24
```

- Generate pick/sort package:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py generate pick-sort --output-dir artifacts/stage3/pick_sort_demo --frames 24
```

- Validate:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage3/weld_demo --json
```

- Summarize:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py summarize artifacts/stage3/weld_demo --json
```

- Export candidates:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage3/weld_demo
```

- Convert to Rerun:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage3/weld_demo --output-rrd artifacts/stage3/weld_demo.rrd
```

- Known limits:
  - No hardware.
  - No ROS/Gazebo/MoveIt.
  - Rerun is adapter backend.
  - Validator is dev diagnostics, not production governance.

- [x] **Step 2: Create Stage 3 implementation record**

Create `docs/research/05-physical-ai数据包阶段三实施记录.md` in Chinese with sections:

- 阶段目标
- 已实现能力
- 验证命令
- 两个仿真样例说明
- validator 结果
- Rerun adapter 结果
- 候选导出结果
- 风险与限制
- 下一步

Only claim smoke results after Step 4 has actually run.

- [x] **Step 3: Update README and details**

Modify `README.md`:

- Add link to `docs/stage3/README.md`.
- Add link to `docs/research/05-physical-ai数据包阶段三实施记录.md`.
- Update current status to say Stage 3 has a runnable package/validator/adapter prototype after implementation.

Modify `details.md`:

- Add dated implementation completion bullets.
- Update next steps.

- [x] **Step 4: Run final smoke commands**

Run:

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 scripts/physical_ai_package.py generate welding --output-dir artifacts/stage3/final_weld --frames 24
PYTHONPATH=src python3 scripts/physical_ai_package.py generate pick-sort --output-dir artifacts/stage3/final_pick_sort --frames 24
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage3/final_weld --json
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage3/final_pick_sort --json
PYTHONPATH=src python3 scripts/physical_ai_package.py summarize artifacts/stage3/final_weld --json
PYTHONPATH=src python3 scripts/physical_ai_package.py summarize artifacts/stage3/final_pick_sort --json
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage3/final_weld
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage3/final_pick_sort
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage3/final_weld --output-rrd artifacts/stage3/final_weld.rrd
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage3/final_pick_sort --output-rrd artifacts/stage3/final_pick_sort.rrd
rerun rrd verify artifacts/stage3/final_weld.rrd
rerun rrd verify artifacts/stage3/final_pick_sort.rrd
```

Expected:

- All tests pass.
- Both validations return `"ok": true`.
- Both candidate CSV files exist.
- Both `.rrd` files verify without error.

- [x] **Step 5: Update implementation record with real results**

After Step 4, update `docs/research/05-physical-ai数据包阶段三实施记录.md` with exact observed results and any warnings. Do not claim GUI Viewer/Blueprint manual inspection unless actually performed.

- [x] **Step 6: Run docs/status checks**

Run:

```bash
rg -n "阶段三|stage3|physical_ai_package|Simulation-first" README.md details.md docs/stage3/README.md docs/research/05-physical-ai数据包阶段三实施记录.md
git diff --check
git status --short --branch
```

Expected:

- Stage 3 links and status are visible.
- No whitespace errors.
- Only intended files are modified.

- [x] **Step 7: Commit Task 6**

```bash
git add README.md details.md docs/stage3/README.md docs/research/05-physical-ai数据包阶段三实施记录.md
git commit -m "Document physical AI package stage 3"
```

## Final Verification

After all tasks are complete, use `superpowers:verification-before-completion` before claiming completion.

Run:

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 scripts/physical_ai_package.py generate welding --output-dir artifacts/stage3/release_weld --frames 24
PYTHONPATH=src python3 scripts/physical_ai_package.py generate pick-sort --output-dir artifacts/stage3/release_pick_sort --frames 24
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage3/release_weld --json
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage3/release_pick_sort --json
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage3/release_weld
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage3/release_pick_sort
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage3/release_weld --output-rrd artifacts/stage3/release_weld.rrd
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage3/release_pick_sort --output-rrd artifacts/stage3/release_pick_sort.rrd
rerun rrd verify artifacts/stage3/release_weld.rrd
rerun rrd verify artifacts/stage3/release_pick_sort.rrd
git status --short --branch
```

Expected:

- Tests pass.
- Both packages validate.
- Both candidate exports exist.
- Both `.rrd` files verify.
- Working tree is clean after commits, except ignored artifacts/cache.

Do not push automatically from a subagent. After final verification, the main agent should inspect `git status --short --branch` and push `main` only after confirming the completed commits are intended for the remote.

## Execution Notes for Subagents

- Use one fresh worker subagent per task.
- Workers are not alone in the codebase. They must not revert edits made by others and must adapt to current repository state.
- After each worker completes:
  - review changed files;
  - run task-specific tests;
  - dispatch review if the change is broad or risky;
  - commit before starting the next task.
- Do not skip failing-test steps unless a task is documentation-only.
- Keep generated artifacts under `artifacts/`.
