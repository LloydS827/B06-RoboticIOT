# Stage 4.4 Weld Workcell Importer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增一个离线 `weld_workcell` 业务导出 importer candidate，把机器人焊接工位多文件导出转换成合法 `robot_welding_station` Physical AI Package。

**Architecture:** 新 importer 复用现有 `ImportRequest`、`ImportResult`、`run_import` contract，输入固定为本地目录中的 `job.json`、`frames.csv`、`process.csv`、`events.csv` 和可选 `review_labels.csv`。输出仍以 Physical AI Package v0.1 为唯一主数据结构；Rerun 只作为可替换 adapter backend，通过非 GUI `.rrd` smoke 验证。

**Tech Stack:** Python 3.11+、pytest、标准库 `csv/json/pathlib/shutil/datetime/math`、现有 `physical_ai_data` package。

---

## File Structure

- Create: `src/physical_ai_data/weld_workcell_importer.py`
  - 实现 `WeldWorkcellPackageImporter`、输入读取/校验、图片复制、业务表到 package 表映射、manifest/source traceability。
- Create: `tests/physical_ai_data/test_weld_workcell_importer.py`
  - 独立覆盖 happy path、错误处理、copy_images、pipeline 消费和 Rerun adapter smoke，避免继续扩大 `test_importers.py`。
- Modify: `docs/stage4/README.md`
  - 增加 Weld Workcell importer candidate 的输入 contract、最小使用示例、当前边界。
- Modify: `README.md`
  - 增加 Stage 4.4 spec/plan 入口和当前状态摘要。
- Modify: `details.md`
  - 记录 Stage 4.4 完成事项、验证结果和下一阶段计划。

No changes planned:

- No CLI command.
- No importer registry or plugin lifecycle.
- No Physical AI Package schema version change.
- No formal label/review schema.

---

### Task 1: Core Weld Workcell Importer Happy Path

**Files:**
- Create: `src/physical_ai_data/weld_workcell_importer.py`
- Create: `tests/physical_ai_data/test_weld_workcell_importer.py`

- [ ] **Step 1: Add the focused happy-path test fixture**

In `tests/physical_ai_data/test_weld_workcell_importer.py`, create local helpers that write the source directory:

```python
from __future__ import annotations

import csv
import json
import base64
from pathlib import Path

from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.validation import validate_package
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _write_weld_source(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "images").mkdir()
    tiny_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
    )
    (root / "images" / "front_0000.png").write_bytes(tiny_png)
    (root / "job.json").write_text(
        json.dumps(
            {
                "work_order_id": "WO-1001",
                "station_id": "station_A",
                "robot_id": "robot_17",
                "welder_id": "welder_03",
                "part_id": "part_alpha",
                "seam_id": "seam_root",
                "task_name": "Root pass weld",
                "created_at": "2026-06-10T09:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _write_csv(
        root / "frames.csv",
        [
            "timestamp_s",
            "phase",
            "tcp_x",
            "tcp_y",
            "tcp_z",
            "tcp_qx",
            "tcp_qy",
            "tcp_qz",
            "tcp_qw",
            "image_path",
        ],
        [
            {
                "timestamp_s": "0.0",
                "phase": "approach",
                "tcp_x": "0.10",
                "tcp_y": "0.20",
                "tcp_z": "0.30",
                "tcp_qx": "0.0",
                "tcp_qy": "0.0",
                "tcp_qz": "0.0",
                "tcp_qw": "1.0",
                "image_path": "images/front_0000.png",
            },
            {
                "timestamp_s": "0.2",
                "phase": "weld",
                "tcp_x": "0.15",
                "tcp_y": "0.22",
                "tcp_z": "0.31",
                "tcp_qx": "0.0",
                "tcp_qy": "0.0",
                "tcp_qz": "0.1",
                "tcp_qw": "0.99",
                "image_path": "",
            },
            {
                "timestamp_s": "0.4",
                "phase": "cooldown",
                "tcp_x": "0.18",
                "tcp_y": "0.23",
                "tcp_z": "0.32",
                "tcp_qx": "0.0",
                "tcp_qy": "0.0",
                "tcp_qz": "0.2",
                "tcp_qw": "0.98",
                "image_path": "",
            },
        ],
    )
    _write_csv(
        root / "process.csv",
        [
            "timestamp_s",
            "weld_current_a",
            "weld_voltage_v",
            "wire_feed_mpm",
            "gas_flow_lpm",
            "travel_speed_mm_s",
            "defect_probability",
        ],
        [
            {
                "timestamp_s": "0.1",
                "weld_current_a": "121.5",
                "weld_voltage_v": "23.2",
                "wire_feed_mpm": "7.1",
                "gas_flow_lpm": "15.0",
                "travel_speed_mm_s": "4.5",
                "defect_probability": "0.08",
            }
        ],
    )
    _write_csv(
        root / "events.csv",
        ["timestamp_s", "event_type", "severity", "message", "object_id"],
        [
            {
                "timestamp_s": "0.31",
                "event_type": "arc_start",
                "severity": "info",
                "message": "Arc stabilized",
                "object_id": "seam_root",
            }
        ],
    )
    _write_csv(
        root / "review_labels.csv",
        ["timestamp_s", "label_type", "value", "confidence", "review_status", "reviewer"],
        [
            {
                "timestamp_s": "0.19",
                "label_type": "bead_quality",
                "value": "acceptable",
                "confidence": "0.9",
                "review_status": "reviewed",
                "reviewer": "qa_01",
            }
        ],
    )
    return root
```

- [ ] **Step 2: Add happy-path assertions**

Add:

```python
def test_weld_workcell_importer_creates_valid_robot_welding_package(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    request = ImportRequest(
        source_format="weld_workcell",
        source={"root": source},
        output_dir=tmp_path / "package",
        options={"copy_images": True},
    )

    result = run_import(WeldWorkcellPackageImporter(), request)

    package = tmp_path / "package"
    validation = validate_package(package)
    assert validation.ok, validation.errors
    assert result.source_format == "weld_workcell"
    assert result.source_id == str(source)
    assert result.frame_count == 3
    manifest = json.loads((package / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenario_type"] == "robot_welding_station"
    assert manifest["package_id"] == "weld_workcell_WO-1001_station_A"
    assert manifest["task"]["name"] == "Root pass weld"
    assert manifest["source_dataset"]["format"] == "weld_workcell"
    assert manifest["source_dataset"]["image_copy_policy"] == "copied_to_artifacts_images_frame_id"
    assert (package / "artifacts/source/job.json").is_file()
    assert (package / "artifacts/source/frames.csv").is_file()
    assert (package / "artifacts/source/process.csv").is_file()
    assert (package / "artifacts/source/events.csv").is_file()
    assert (package / "artifacts/source/review_labels.csv").is_file()
```

- [ ] **Step 3: Run the focused test to verify it fails**

Run:

```bash
python -m pytest tests/physical_ai_data/test_weld_workcell_importer.py::test_weld_workcell_importer_creates_valid_robot_welding_package -q
```

Expected: FAIL with `ModuleNotFoundError` or missing `WeldWorkcellPackageImporter`.

- [ ] **Step 4: Create the minimal importer skeleton**

In `src/physical_ai_data/weld_workcell_importer.py`, add:

```python
from __future__ import annotations

import math
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Sequence

from physical_ai_data.importers import ImportRequest, ImportResult
from physical_ai_data.package_io import ensure_dir, read_csv_rows, read_json, write_csv_rows, write_json
from physical_ai_data.schema import REQUIRED_TABLE_COLUMNS, SCHEMA_VERSION
from physical_ai_data.validation import validate_package


MANIFEST_FILENAME = "physical_ai_manifest.json"
SOURCE_FILES = ("job.json", "frames.csv", "process.csv", "events.csv")


class WeldWorkcellPackageImporter:
    source_format = "weld_workcell"

    def import_package(self, request: ImportRequest) -> ImportResult:
        if request.source_format != self.source_format:
            raise ValueError(f"Weld workcell importer cannot handle {request.source_format}")
        source_root = _required_path(request.source, "root")
        copy_images = _optional_bool(request.options, "copy_images", default=True)
        package_root = _write_package(source_root, request.output_dir, copy_images=copy_images)
        validation = validate_package(package_root)
        if not validation.ok:
            raise ValueError(f"Imported package failed validation: {_format_validation_errors(validation.errors)}")
        return ImportResult(
            package_root=package_root,
            source_format=self.source_format,
            source_id=str(source_root),
            frame_count=int(validation.summary.get("frame_count", 0)),
            warnings=[f"{warning.code}: {warning.message}" for warning in validation.warnings],
        )
```

Then implement helpers copied in style from `csv_recording_importer.py`: `_required_path`, `_optional_bool`, `_finite_float`, `_format_validation_errors`, `_utc_now`, `_prepare_package`.

- [ ] **Step 5: Implement enough package writing for the happy path**

Implement `_write_package(source_root, output_dir, copy_images)` to:

- require `job.json`, `frames.csv`, `process.csv`, `events.csv`;
- treat `review_labels.csv` as optional and copy it into `artifacts/source/` only when it exists;
- create `artifacts/images`, `artifacts/point_clouds`, `artifacts/trajectories`, `artifacts/source`;
- copy required source files `job.json`, `frames.csv`, `process.csv`, `events.csv` into `artifacts/source/`;
- write `frames.csv`, `events.csv`, `labels.csv`, `metrics.csv`, `artifacts/trajectories/tcp_path.csv`, `physical_ai_manifest.json`, and package `README.md`;
- copy non-empty source images to `artifacts/images/frame_XXXX.ext` when `copy_images=True`.

Use stable frame ids and trajectory rows:

```python
trajectory_rows.append(
    {
        "frame_id": frame_id,
        "timestamp_s": timestamp_s,
        "x": row["tcp_x"].strip(),
        "y": row["tcp_y"].strip(),
        "z": row["tcp_z"].strip(),
        "qx": row["tcp_qx"].strip(),
        "qy": row["tcp_qy"].strip(),
        "qz": row["tcp_qz"].strip(),
        "qw": row["tcp_qw"].strip(),
    }
)
```

Write trajectory columns in this exact order:

```python
["frame_id", "timestamp_s", "x", "y", "z", "qx", "qy", "qz", "qw"]
```

Set each frame `trajectory_ref` to `artifacts/trajectories/tcp_path.csv`.

- [ ] **Step 6: Run focused happy-path test**

Run:

```bash
python -m pytest tests/physical_ai_data/test_weld_workcell_importer.py::test_weld_workcell_importer_creates_valid_robot_welding_package -q
```

Expected: PASS.

- [ ] **Step 7: Commit Task 1**

```bash
git add src/physical_ai_data/weld_workcell_importer.py tests/physical_ai_data/test_weld_workcell_importer.py
git commit -m "feat: add weld workcell importer candidate"
```

---

### Task 2: Mapping Contract and Pipeline Compatibility

**Files:**
- Modify: `tests/physical_ai_data/test_weld_workcell_importer.py`
- Modify: `src/physical_ai_data/weld_workcell_importer.py`

- [ ] **Step 1: Add detailed mapping tests**

Add a test that imports the fixture and asserts:

```python
def test_weld_workcell_importer_maps_tables_and_source_dataset(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    package = tmp_path / "package"
    run_import(
        WeldWorkcellPackageImporter(),
        ImportRequest("weld_workcell", {"root": source}, package, {"copy_images": True}),
    )

    frames = _rows(package / "frames.csv")
    metrics = _rows(package / "metrics.csv")
    events = _rows(package / "events.csv")
    labels = _rows(package / "labels.csv")
    trajectory = _rows(package / "artifacts/trajectories/tcp_path.csv")
    manifest = json.loads((package / "physical_ai_manifest.json").read_text(encoding="utf-8"))

    assert [row["frame_id"] for row in frames] == ["frame_0000", "frame_0001", "frame_0002"]
    assert frames[0]["timeline"] == "sim_time"
    assert frames[0]["coordinate_frame_id"] == "tcp"
    assert frames[0]["image_ref"] == "artifacts/images/frame_0000.png"
    assert frames[1]["trajectory_ref"] == "artifacts/trajectories/tcp_path.csv"
    assert (package / frames[0]["image_ref"]).read_bytes() == (source / "images/front_0000.png").read_bytes()
    assert trajectory[1]["x"] == "0.15"

    assert [(row["metric_name"], row["unit"]) for row in metrics] == [
        ("weld_current", "A"),
        ("weld_voltage", "V"),
        ("wire_feed", "m/min"),
        ("gas_flow", "L/min"),
        ("travel_speed", "mm/s"),
        ("defect_probability", "ratio"),
    ]
    assert events[0]["related_frame_id"] == "frame_0002"
    assert events[0]["related_object_id"] == "seam_root"
    assert labels[0]["target_ref"] == "frame:frame_0001"
    assert labels[0]["source"] == "weld_workcell_review"
    assert manifest["source_dataset"]["frame_count"] == 3
    assert manifest["source_dataset"]["process_row_count"] == 1
    assert manifest["source_dataset"]["event_count"] == 1
    assert manifest["source_dataset"]["label_count"] == 1
    assert "review_labels_csv_ref" in manifest["source_dataset"]
```

The event timestamp `0.31` must resolve to `frame_0002`; the label timestamp `0.19` must resolve to `frame_0001`.

- [ ] **Step 2: Add copy_images=False test**

Add:

```python
def test_weld_workcell_importer_can_skip_copying_images(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    package = tmp_path / "package"

    run_import(
        WeldWorkcellPackageImporter(),
        ImportRequest("weld_workcell", {"root": source}, package, {"copy_images": False}),
    )

    frames = _rows(package / "frames.csv")
    manifest = json.loads((package / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    assert [row["image_ref"] for row in frames] == ["", "", ""]
    assert manifest["source_dataset"]["image_copy_policy"] == "image_refs_empty_when_copy_images_false"
    assert not any((package / "artifacts/images").iterdir())
    assert validate_package(package).ok


def test_weld_workcell_importer_accepts_missing_review_labels(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    (source / "review_labels.csv").unlink()
    package = tmp_path / "package"

    run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, package))

    manifest = json.loads((package / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    assert _rows(package / "labels.csv") == []
    assert "review_labels_csv_ref" not in manifest["source_dataset"]
    assert not (package / "artifacts/source/review_labels.csv").exists()
    assert validate_package(package).ok
```

- [ ] **Step 3: Add pipeline compatibility smoke tests**

Add imports:

```python
from physical_ai_data.candidates import export_candidates
from physical_ai_data.candidates import summarize_package
from physical_ai_data.package_io import read_json
from physical_ai_data.rerun_adapter import write_rrd
from physical_ai_data.training_export import export_training_eval_draft
```

Add:

```python
def test_weld_workcell_package_feeds_existing_export_pipeline(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    package = tmp_path / "package"
    run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, package))

    summary = summarize_package(package)
    candidates = export_candidates(package)
    draft = export_training_eval_draft(package, split="eval")
    rrd = write_rrd(package, tmp_path / "weld_workcell.rrd")

    assert summary["package_id"] == "weld_workcell_WO-1001_station_A"
    assert candidates.is_file()
    assert read_json(draft / "training_eval_manifest.json")["export_format"] == "physical-ai-training-eval-draft/v0.2"
    assert rrd.is_file()
    assert rrd.stat().st_size > 0
```

- [ ] **Step 4: Run mapping and pipeline tests to verify failures**

Run:

```bash
python -m pytest tests/physical_ai_data/test_weld_workcell_importer.py -q
```

Expected: new tests fail until mapping details, copy policy, nearest-frame behavior, and pipeline compatibility are complete.

- [ ] **Step 5: Implement manifest source_dataset and stable mappings**

In `weld_workcell_importer.py`, implement:

- `_manifest(job, source_root, counts, converted_at, copy_images, has_review_labels)`;
- `source_dataset.format == "weld_workcell"`;
- `source_dataset` refs for `job_json_ref`, `frames_csv_ref`, `process_csv_ref`, `events_csv_ref`, and optional `review_labels_csv_ref`;
- counts for frames, process rows, events, labels;
- `image_copy_policy` exactly as in the spec.

Use manifest objects directly from job:

```python
"objects": [
    {"object_id": str(job["part_id"]), "type": "workpiece"},
    {"object_id": str(job["seam_id"]), "type": "weld_seam"},
]
```

Use coordinate frames:

```python
[
    {"frame_id": "station", "parent_frame_id": "", "pose_ref": ""},
    {"frame_id": "robot_base", "parent_frame_id": "station", "pose_ref": ""},
    {"frame_id": "tcp", "parent_frame_id": "robot_base", "pose_ref": ""},
    {"frame_id": "camera_front", "parent_frame_id": "robot_base", "pose_ref": ""},
    {"frame_id": "workpiece", "parent_frame_id": "station", "pose_ref": ""},
]
```

- [ ] **Step 6: Implement nearest-frame and metric mapping**

Use a local helper instead of changing `package_io.nearest_frame_id`, because the spec requires tie-breaking by earlier input frame:

```python
def _nearest_frame_id(frames: Sequence[Mapping[str, str]], timestamp_s: float) -> str:
    nearest_id = ""
    nearest_delta: float | None = None
    for frame in frames:
        frame_id = frame.get("frame_id", "")
        frame_timestamp = _finite_float(frame.get("timestamp_s", ""), "timestamp_s")
        delta = abs(frame_timestamp - timestamp_s)
        if nearest_delta is None or delta < nearest_delta:
            nearest_id = frame_id
            nearest_delta = delta
    return nearest_id
```

Map process columns in this exact order:

```python
PROCESS_METRICS = [
    ("weld_current_a", "weld_current", "A"),
    ("weld_voltage_v", "weld_voltage", "V"),
    ("wire_feed_mpm", "wire_feed", "m/min"),
    ("gas_flow_lpm", "gas_flow", "L/min"),
    ("travel_speed_mm_s", "travel_speed", "mm/s"),
    ("defect_probability", "defect_probability", "ratio"),
]
```

- [ ] **Step 7: Run focused passing tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_weld_workcell_importer.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit Task 2**

```bash
git add src/physical_ai_data/weld_workcell_importer.py tests/physical_ai_data/test_weld_workcell_importer.py
git commit -m "test: cover weld workcell package mappings"
```

---

### Task 3: Input Contract Validation and Edge Cases

**Files:**
- Modify: `tests/physical_ai_data/test_weld_workcell_importer.py`
- Modify: `src/physical_ai_data/weld_workcell_importer.py`

- [ ] **Step 1: Add source format mismatch and missing source tests**

Add:

```python
import pytest
```

Then add tests:

```python
def test_weld_workcell_importer_rejects_source_format_mismatch(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    with pytest.raises(ValueError, match="cannot handle other"):
        run_import(
            WeldWorkcellPackageImporter(),
            ImportRequest("other", {"root": source}, tmp_path / "package"),
        )


def test_weld_workcell_importer_rejects_missing_required_file(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    (source / "process.csv").unlink()
    with pytest.raises(ValueError, match="source.root must contain process.csv"):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))
```

- [ ] **Step 2: Add job and required-column tests**

Add helper mutators:

```python
def _rewrite_csv_without_column(path: Path, missing: str) -> None:
    rows = _rows(path)
    fieldnames = [field for field in rows[0].keys() if field != missing]
    _write_csv(path, fieldnames, [{key: value for key, value in row.items() if key != missing} for row in rows])
```

Add tests:

```python
def test_weld_workcell_importer_rejects_missing_job_field(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    job = json.loads((source / "job.json").read_text(encoding="utf-8"))
    del job["robot_id"]
    (source / "job.json").write_text(json.dumps(job) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="job.json missing required fields: robot_id"):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))


def test_weld_workcell_importer_rejects_missing_csv_column(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _rewrite_csv_without_column(source / "frames.csv", "tcp_x")
    with pytest.raises(ValueError, match="frames.csv missing required columns: tcp_x"):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))


def test_weld_workcell_importer_rejects_missing_process_csv_column(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _rewrite_csv_without_column(source / "process.csv", "weld_current_a")
    with pytest.raises(ValueError, match="process.csv missing required columns: weld_current_a"):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))


def test_weld_workcell_importer_rejects_missing_review_label_column(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _rewrite_csv_without_column(source / "review_labels.csv", "confidence")
    with pytest.raises(ValueError, match="review_labels.csv missing required columns: confidence"):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))
```

- [ ] **Step 3: Add malformed row and numeric validation tests**

Append one extra CSV line to create a malformed row:

```python
def test_weld_workcell_importer_rejects_malformed_csv_row(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    with (source / "events.csv").open("a", encoding="utf-8") as file:
        file.write("0.5,too,many,columns,here,extra\n")
    with pytest.raises(ValueError, match="events.csv has malformed rows"):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))


def test_weld_workcell_importer_rejects_nonfinite_numeric_values(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    rows = _rows(source / "process.csv")
    rows[0]["weld_current_a"] = "nan"
    _write_csv(source / "process.csv", list(rows[0].keys()), rows)
    with pytest.raises(ValueError, match="weld_current_a must be a finite number"):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))


def test_weld_workcell_importer_rejects_nonfinite_review_label_confidence(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    rows = _rows(source / "review_labels.csv")
    rows[0]["confidence"] = "inf"
    _write_csv(source / "review_labels.csv", list(rows[0].keys()), rows)
    with pytest.raises(ValueError, match="confidence must be a finite number"):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))
```

- [ ] **Step 4: Add frames empty, image path, unknown object, and nearest-frame edge tests**

Add:

```python
@pytest.mark.parametrize("bad_path, message", [
    ("/tmp/front.png", "image_path must be relative to source.root"),
    ("../front.png", "image_path must be relative to source.root"),
    ("images/missing.png", "source image does not exist: images/missing.png"),
])
def test_weld_workcell_importer_rejects_invalid_image_paths(tmp_path: Path, bad_path: str, message: str):
    source = _write_weld_source(tmp_path / "source")
    rows = _rows(source / "frames.csv")
    rows[0]["image_path"] = bad_path
    _write_csv(source / "frames.csv", list(rows[0].keys()), rows)
    with pytest.raises(ValueError, match=message):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))


def test_weld_workcell_importer_rejects_symlink_escape_image(tmp_path: Path):
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"outside")
    source = _write_weld_source(tmp_path / "source")
    (source / "images" / "escape.png").symlink_to(outside)
    rows = _rows(source / "frames.csv")
    rows[0]["image_path"] = "images/escape.png"
    _write_csv(source / "frames.csv", list(rows[0].keys()), rows)
    with pytest.raises(ValueError, match="image_path must be relative to source.root"):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))


def test_weld_workcell_importer_rejects_empty_frames_csv(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _write_csv(source / "frames.csv", [
        "timestamp_s", "phase", "tcp_x", "tcp_y", "tcp_z", "tcp_qx", "tcp_qy", "tcp_qz", "tcp_qw", "image_path"
    ], [])
    with pytest.raises(ValueError, match="frames.csv must contain at least one data row"):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))


def test_weld_workcell_importer_rejects_unknown_event_object_id(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    rows = _rows(source / "events.csv")
    rows[0]["object_id"] = "unknown_object"
    _write_csv(source / "events.csv", list(rows[0].keys()), rows)
    with pytest.raises(ValueError, match="events.csv object_id must be one of"):
        run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))


def test_weld_workcell_importer_uses_nearest_endpoint_and_earlier_frame_for_ties(tmp_path: Path):
    source = _write_weld_source(tmp_path / "source")
    _write_csv(
        source / "events.csv",
        ["timestamp_s", "event_type", "severity", "message", "object_id"],
        [
            {"timestamp_s": "-1.0", "event_type": "before", "severity": "info", "message": "", "object_id": ""},
            {"timestamp_s": "0.1", "event_type": "tie", "severity": "info", "message": "", "object_id": ""},
            {"timestamp_s": "9.0", "event_type": "after", "severity": "info", "message": "", "object_id": ""},
        ],
    )
    run_import(WeldWorkcellPackageImporter(), ImportRequest("weld_workcell", {"root": source}, tmp_path / "package"))
    events = _rows(tmp_path / "package" / "events.csv")
    assert [row["related_frame_id"] for row in events] == ["frame_0000", "frame_0000", "frame_0002"]
```

- [ ] **Step 5: Run validation tests to verify failures**

Run:

```bash
python -m pytest tests/physical_ai_data/test_weld_workcell_importer.py -q
```

Expected: validation tests fail until all guardrails are implemented.

- [ ] **Step 6: Implement validation helpers**

In `weld_workcell_importer.py`, add:

- required column constants for frames/process/events/review labels;
- `_require_source_file(source_root, filename)`;
- `_validate_job(job)`;
- `_validate_columns(rows, path, required_columns)`;
- `_validate_rows(rows, path)`;
- `_read_csv_header(path)`;
- `_source_relative_path(value)`;
- `_copy_image(...)`.

Validation details:

- For empty CSV, read header from disk and still validate required columns.
- Reject `None in row` or any `value is None` as malformed.
- For frames, reject zero data rows after header validation.
- Validate all numeric fields with `_finite_float` before writing outputs.
- Validate event `object_id` only when non-empty.
- For image paths, reject absolute paths, `..`, symlink escape, and missing files even when `copy_images=False`, because the input contract still requires referenced images to exist.

- [ ] **Step 7: Run focused passing tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_weld_workcell_importer.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit Task 3**

```bash
git add src/physical_ai_data/weld_workcell_importer.py tests/physical_ai_data/test_weld_workcell_importer.py
git commit -m "test: harden weld workcell importer contract"
```

---

### Task 4: Documentation and Full Verification

**Files:**
- Modify: `docs/stage4/README.md`
- Modify: `README.md`
- Modify: `details.md`

- [ ] **Step 1: Update Stage 4 documentation**

In `docs/stage4/README.md`, add a Stage 4.4 section covering:

- `weld_workcell` is an offline business importer candidate;
- required input directory structure;
- required fields/columns;
- minimal Python usage:

```python
from pathlib import Path

from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter

result = run_import(
    WeldWorkcellPackageImporter(),
    ImportRequest(
        source_format="weld_workcell",
        source={"root": Path("fixtures/weld_workcell_export")},
        output_dir=Path("artifacts/stage4/weld_workcell_package"),
        options={"copy_images": True},
    ),
)
```

- output remains Physical AI Package v0.1;
- Rerun remains optional adapter backend;
- `review_status`/`reviewer` stay only in `artifacts/source/review_labels.csv`.

- [ ] **Step 2: Update README**

In `README.md`, add:

- Stage 4.4 status bullet;
- links to:
  - `docs/superpowers/specs/2026-06-10-stage-4-4-weld-workcell-importer-design.md`
  - `docs/superpowers/plans/2026-06-10-stage-4-4-weld-workcell-importer.md`
  - `docs/stage4/README.md`
- a short note that the default path remains offline and testable.

- [ ] **Step 3: Update details**

In `details.md`, add a dated Stage 4.4 entry with:

- completed importer candidate summary;
- verification commands and results;
- known limitations/non-goals;
- next-stage recommendation.

Use final actual test output after Step 5.

- [ ] **Step 4: Run focused docs-adjacent tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_weld_workcell_importer.py tests/physical_ai_data/test_rerun_adapter.py tests/physical_ai_data/test_training_export.py -q
```

Expected: PASS.

- [ ] **Step 5: Run full verification**

Run:

```bash
python -m pytest -q
```

Expected: all tests PASS.

- [ ] **Step 6: Record actual verification output in details**

Update `details.md` with the exact full-test summary, for example:

```text
Verification: python -m pytest -q -> 168 passed in 3.20s
```

Use the real output, not this example.

- [ ] **Step 7: Commit Task 4**

```bash
git add docs/stage4/README.md README.md details.md
git commit -m "docs: document weld workcell importer candidate"
```

---

## Final Verification Before PR

- [ ] Run:

```bash
git status --short
python -m pytest -q
```

Expected:

- `git status --short` has no uncommitted source changes before push.
- All tests pass.

- [ ] Push and create PR after verification:

```bash
git push -u origin codex/stage-4-4-weld-workcell-importer
gh pr create --fill
```

- [ ] After remote merge is confirmed, run cleanup from the parent/main worktree, then pull, remove the feature worktree, and delete the local branch:

```bash
git switch main
git pull --ff-only
git worktree remove .worktrees/stage-4-4-weld-workcell-importer
git branch -d codex/stage-4-4-weld-workcell-importer
```
