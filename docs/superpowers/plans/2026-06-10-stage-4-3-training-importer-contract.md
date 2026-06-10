# Stage 4.3 Training Importer Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 收紧 training/evaluation draft export contract，并用一个非 LeRobot CSV recording importer fixture 验证 external importer contract 是通用边界。

**Architecture:** 保持 Physical AI Package 为主数据结构，training export 只生成 draft sample index；新增 CSV importer fixture 通过现有 `ImportRequest`/`ImportResult`/`run_import` 边界输出标准 package。Rerun 不参与新增 contract，只继续作为已有 adapter backend。

**Tech Stack:** Python 3.11+、pytest、标准库 `csv/json/pathlib/shutil/datetime`、现有 `physical_ai_data` package。

---

## File Structure

- Modify: `src/physical_ai_data/training_export.py`
  - 收紧 export format、manifest 字段、split 校验和 samples 字段。
- Modify: `tests/physical_ai_data/test_training_export.py`
  - 更新 v0.2 contract 测试，覆盖 split、primary artifact、candidate 来源字段。
- Create: `src/physical_ai_data/csv_recording_importer.py`
  - 实现离线 `CsvRecordingPackageImporter` fixture。
- Modify: `tests/physical_ai_data/test_importers.py`
  - 增加 `csv_recording` importer contract 测试。
- Modify: `docs/stage4/README.md`
  - 更新 training draft v0.2 和 CSV importer fixture 示例。
- Modify: `README.md`
  - 增加 Stage 4.3 文档入口和当前状态摘要。
- Modify: `details.md`
  - 记录 Stage 4.3 完成事项、验证结果和下一步计划。

---

### Task 1: Training/Evaluation Draft Contract v0.2

**Files:**
- Modify: `src/physical_ai_data/training_export.py`
- Modify: `tests/physical_ai_data/test_training_export.py`

- [ ] **Step 1: Update tests for manifest v0.2**

In `tests/physical_ai_data/test_training_export.py`, update `test_export_training_eval_draft_creates_default_manifest_and_samples` to expect:

```python
assert manifest["export_format"] == "physical-ai-training-eval-draft/v0.2"
assert manifest["contract_status"] == "draft"
assert manifest["formal_format"] is False
assert manifest["allowed_splits"] == ["unspecified", "train", "eval", "validation", "test", "holdout"]
assert manifest["samples_schema_version"] == "physical-ai-training-eval-samples/v0.2"
assert manifest["sample_count"] == len(rows)
assert manifest["candidate_count"] == len(rows)
assert "not a formal training framework format" in manifest["notes"]
```

Also update expected sample columns to:

```python
[
    "sample_id",
    "split",
    "package_id",
    "frame_id",
    "timestamp_s",
    "candidate_id",
    "candidate_source_type",
    "candidate_source_id",
    "object_id",
    "score",
    "reasons",
    "label_status",
    "label_ref",
    "primary_artifact_ref",
    "package_root",
]
```

- [ ] **Step 2: Add split validation tests**

Add parameterized tests:

```python
@pytest.mark.parametrize("split", ["unspecified", "train", "eval", "validation", "test", "holdout"])
def test_export_training_eval_draft_accepts_allowed_splits(tmp_path: Path, split: str):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=10)
    output = export_training_eval_draft(package, split=split)
    manifest = json.loads((output / "training_eval_manifest.json").read_text(encoding="utf-8"))
    rows = _rows(output / "samples.csv")
    assert manifest["split"] == split
    assert {row["split"] for row in rows} == {split}


@pytest.mark.parametrize("split", ["", "Train", "dev", "train/eval"])
def test_export_training_eval_draft_rejects_invalid_split(tmp_path: Path, split: str):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=11)
    with pytest.raises(ValueError, match="split must be one of"):
        export_training_eval_draft(package, split=split)
```

Remove or replace the old `test_export_training_eval_draft_preserves_split_verbatim`.

- [ ] **Step 3: Add primary artifact fallback test**

Add a test that writes a manual `derived/candidates.csv` row with `frame_id="missing_frame"` and verifies:

```python
assert rows[0]["primary_artifact_ref"] == ""
```

This implements the reviewer recommendation that missing candidate frame references should not fail draft export.

- [ ] **Step 4: Run focused failing tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_training_export.py -q
```

Expected: tests fail because production code still emits v0.1 fields and accepts arbitrary split.

- [ ] **Step 5: Implement constants and split validation**

In `src/physical_ai_data/training_export.py`, update constants:

```python
TRAINING_EVAL_EXPORT_FORMAT = "physical-ai-training-eval-draft/v0.2"
TRAINING_EVAL_SAMPLES_SCHEMA_VERSION = "physical-ai-training-eval-samples/v0.2"
TRAINING_EVAL_ALLOWED_SPLITS = ["unspecified", "train", "eval", "validation", "test", "holdout"]
TRAINING_EVAL_SAMPLE_COLUMNS = [
    "sample_id",
    "split",
    "package_id",
    "frame_id",
    "timestamp_s",
    "candidate_id",
    "candidate_source_type",
    "candidate_source_id",
    "object_id",
    "score",
    "reasons",
    "label_status",
    "label_ref",
    "primary_artifact_ref",
    "package_root",
]
```

Add:

```python
def _validate_split(split: str) -> None:
    if split not in TRAINING_EVAL_ALLOWED_SPLITS:
        raise ValueError(f"split must be one of: {', '.join(TRAINING_EVAL_ALLOWED_SPLITS)}")
```

Call `_validate_split(split)` after package validation starts or before it; either is acceptable, but keep behavior deterministic.

- [ ] **Step 6: Implement v0.2 manifest and sample rows**

Read frames once and build a `frame_id -> frame row` mapping:

```python
manifest_tables = package_manifest.get("tables", {})
frames = read_csv_rows(root / str(manifest_tables["frames"])) if isinstance(manifest_tables, Mapping) else []
frames_by_id = {row.get("frame_id", ""): row for row in frames}
```

Update `_sample_row` signature to include package id and frame mapping:

```python
def _sample_row(index, split, candidate, root, package_id, frames_by_id):
    frame = frames_by_id.get(candidate.get("frame_id", ""), {})
    return {
        "sample_id": f"sample_{index:04d}",
        "split": split,
        "package_id": package_id,
        "frame_id": candidate.get("frame_id", ""),
        "timestamp_s": candidate.get("timestamp_s", ""),
        "candidate_id": candidate.get("candidate_id", ""),
        "candidate_source_type": candidate.get("source_type", ""),
        "candidate_source_id": candidate.get("source_id", ""),
        "object_id": candidate.get("object_id", ""),
        "score": candidate.get("score", ""),
        "reasons": candidate.get("reasons", ""),
        "label_status": "unlabeled",
        "label_ref": "",
        "primary_artifact_ref": _primary_artifact_ref(frame),
        "package_root": str(root),
    }
```

Implement:

```python
def _primary_artifact_ref(frame: Mapping[str, str]) -> str:
    for field in ("image_ref", "point_cloud_ref", "trajectory_ref"):
        value = frame.get(field, "")
        if value:
            return value
    return ""
```

Update `_manifest` to include the v0.2 fields. `formal_format` must be JSON boolean `False`; `allowed_splits` must use `TRAINING_EVAL_ALLOWED_SPLITS` in that order.

- [ ] **Step 7: Run focused passing tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_training_export.py tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_cli.py -q
```

Expected: all selected tests pass.

- [ ] **Step 8: Commit Task 1**

```bash
git add src/physical_ai_data/training_export.py tests/physical_ai_data/test_training_export.py tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_cli.py
git commit -m "feat: tighten training eval draft contract"
```

Only include `test_sdk.py` or `test_cli.py` if they required updates.

---

### Task 2: CSV Recording Importer Fixture

**Files:**
- Create: `src/physical_ai_data/csv_recording_importer.py`
- Modify: `tests/physical_ai_data/test_importers.py`

- [ ] **Step 1: Add importer tests**

In `tests/physical_ai_data/test_importers.py`, import:

```python
import csv
from physical_ai_data.csv_recording_importer import CsvRecordingPackageImporter
from physical_ai_data.validation import validate_package
```

Add helpers:

```python
def _write_csv_recording_source(root: Path) -> Path:
    image = root / "images" / "frame_0000.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"fake png bytes")
    rows = [
        {
            "timestamp_s": "0.0",
            "phase": "observe",
            "image_path": "images/frame_0000.png",
            "metric_name": "object_confidence",
            "metric_value": "0.81",
            "event_type": "start",
            "event_severity": "info",
            "event_message": "Recording started",
            "label_type": "task_context",
            "label_value": "demo",
            "label_confidence": "1.0",
        },
        {
            "timestamp_s": "0.1",
            "phase": "grasp",
            "image_path": "",
            "metric_name": "grip_confidence",
            "metric_value": "0.73",
            "event_type": "grasp_attempt",
            "event_severity": "warning",
            "event_message": "Grip confidence needs review",
            "label_type": "quality",
            "label_value": "review",
            "label_confidence": "0.8",
        },
        {
            "timestamp_s": "0.2",
            "phase": "finish",
            "image_path": "",
            "metric_name": "",
            "metric_value": "",
            "event_type": "",
            "event_severity": "",
            "event_message": "",
            "label_type": "",
            "label_value": "",
            "label_confidence": "",
        },
    ]
    path = root / "frames.csv"
    root.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return root


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
```

Add test:

```python
def test_csv_recording_importer_generates_valid_package(tmp_path: Path):
    source = _write_csv_recording_source(tmp_path / "source")
    request = ImportRequest(source_format="csv_recording", source={"root": source}, output_dir=tmp_path / "package")

    result = run_import(CsvRecordingPackageImporter(), request)

    validation = validate_package(result.package_root)
    assert validation.ok
    assert result.source_format == "csv_recording"
    assert result.source_id == str(source)
    assert result.frame_count == 3
    assert (result.package_root / "artifacts" / "images" / "frame_0000.png").exists()
    assert (result.package_root / "artifacts" / "source" / "csv_recording_frames.csv").exists()
```

Also assert manifest source dataset traceability:

```python
manifest = json.loads((result.package_root / "physical_ai_manifest.json").read_text(encoding="utf-8"))
assert manifest["scenario_type"] == "arm_pick_sort"
assert manifest["source_dataset"]["format"] == "csv_recording"
assert manifest["source_dataset"]["root"] == str(source)
assert manifest["source_dataset"]["frame_count"] == 3
assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", manifest["source_dataset"]["converted_at"])
```

Add precise output table assertions:

```python
frames = _read_csv_rows(result.package_root / "frames.csv")
events = _read_csv_rows(result.package_root / "events.csv")
labels = _read_csv_rows(result.package_root / "labels.csv")
metrics = _read_csv_rows(result.package_root / "metrics.csv")

assert [row["frame_id"] for row in frames] == ["frame_0000", "frame_0001", "frame_0002"]
assert frames[0]["timeline"] == "sim_time"
assert frames[0]["coordinate_frame_id"] == "robot_base"
assert frames[0]["image_ref"] == "artifacts/images/frame_0000.png"
assert frames[1]["image_ref"] == ""

assert len(metrics) == 2
assert [row["metric_id"] for row in metrics] == ["metric_0000", "metric_0001"]
assert {row["metric_name"] for row in metrics} == {"object_confidence", "grip_confidence"}

assert len(events) == 2
assert events[0]["event_id"] == "event_0000"
assert events[0]["severity"] == "info"
assert events[0]["message"] == "Recording started"
assert events[0]["related_frame_id"] == "frame_0000"
assert events[1]["severity"] == "warning"
assert events[1]["related_frame_id"] == "frame_0001"

assert len(labels) == 2
assert labels[0]["label_id"] == "label_0000"
assert labels[0]["target_ref"] == "frame:frame_0000"
assert labels[0]["confidence"] == "1.0"
assert labels[1]["target_ref"] == "frame:frame_0001"
```

- [ ] **Step 2: Add negative tests**

Add tests for:

```python
def test_csv_recording_importer_rejects_source_format_mismatch(tmp_path: Path):
    request = ImportRequest(source_format="other", source={"root": tmp_path}, output_dir=tmp_path / "package")
    with pytest.raises(ValueError, match="CSV recording importer cannot handle other"):
        CsvRecordingPackageImporter().import_package(request)


def test_csv_recording_importer_rejects_missing_root(tmp_path: Path):
    request = ImportRequest(source_format="csv_recording", source={}, output_dir=tmp_path / "package")
    with pytest.raises(ValueError, match="source.root must be a path string or Path"):
        CsvRecordingPackageImporter().import_package(request)


def test_csv_recording_importer_rejects_missing_required_columns(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "frames.csv").write_text("timestamp_s,phase\n0.0,observe\n", encoding="utf-8")
    request = ImportRequest(source_format="csv_recording", source={"root": source}, output_dir=tmp_path / "package")
    with pytest.raises(ValueError, match="frames.csv missing required columns"):
        CsvRecordingPackageImporter().import_package(request)


@pytest.mark.parametrize("image_path", ["/tmp/frame.png", "../frame.png"])
def test_csv_recording_importer_rejects_absolute_or_parent_image_path(tmp_path: Path, image_path: str):
    source = _write_csv_recording_source(tmp_path / "source")
    rows = _read_csv_rows(source / "frames.csv")
    rows[0]["image_path"] = image_path
    _write_csv_rows(source / "frames.csv", list(rows[0].keys()), rows)
    request = ImportRequest(source_format="csv_recording", source={"root": source}, output_dir=tmp_path / "package")
    with pytest.raises(ValueError, match="image_path must be relative to source.root"):
        CsvRecordingPackageImporter().import_package(request)


def test_csv_recording_importer_copy_images_false_leaves_image_refs_empty(tmp_path: Path):
    source = _write_csv_recording_source(tmp_path / "source")
    request = ImportRequest(
        source_format="csv_recording",
        source={"root": source},
        output_dir=tmp_path / "package",
        options={"copy_images": False},
    )
    result = run_import(CsvRecordingPackageImporter(), request)
    frames = _read_csv_rows(result.package_root / "frames.csv")
    assert {row["image_ref"] for row in frames} == {""}
```

For `copy_images=False`, assert package validates and every `frames.csv` `image_ref` is empty.

For empty `metric_name`/`metric_value`, empty `event_type`, and empty `label_type`, assert only two metrics, two events, and two labels are generated from the helper source.

Add a dedicated default optional field test:

```python
def test_csv_recording_importer_defaults_optional_event_and_label_fields(tmp_path: Path):
    source = _write_csv_recording_source(tmp_path / "source")
    rows = _read_csv_rows(source / "frames.csv")
    rows[0]["event_severity"] = ""
    rows[0]["event_message"] = ""
    rows[0]["label_confidence"] = ""
    _write_csv_rows(source / "frames.csv", list(rows[0].keys()), rows)

    request = ImportRequest(source_format="csv_recording", source={"root": source}, output_dir=tmp_path / "package")
    result = run_import(CsvRecordingPackageImporter(), request)

    events = _read_csv_rows(result.package_root / "events.csv")
    labels = _read_csv_rows(result.package_root / "labels.csv")
    assert events[0]["severity"] == "info"
    assert events[0]["message"] == ""
    assert labels[0]["confidence"] == "1.0"
    assert labels[0]["target_ref"] == "frame:frame_0000"
```

- [ ] **Step 3: Run focused failing tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_importers.py -q
```

Expected: import fails because `physical_ai_data.csv_recording_importer` does not exist.

- [ ] **Step 4: Implement importer module**

Create `src/physical_ai_data/csv_recording_importer.py`.

Implement constants:

```python
CSV_RECORDING_REQUIRED_COLUMNS = ["timestamp_s", "phase", "image_path", "metric_name", "metric_value"]
CSV_RECORDING_OPTIONAL_COLUMNS = [
    "event_type",
    "event_severity",
    "event_message",
    "label_type",
    "label_value",
    "label_confidence",
]
```

Implement `CsvRecordingPackageImporter`:

```python
class CsvRecordingPackageImporter:
    source_format = "csv_recording"

    def import_package(self, request: ImportRequest) -> ImportResult:
        if request.source_format != self.source_format:
            raise ValueError(f"CSV recording importer cannot handle {request.source_format}")
        root = _required_path(request.source, "root")
        copy_images = _optional_bool(request.options, "copy_images", default=True)
        package_root = _write_package(root, request.output_dir, copy_images=copy_images)
        validation = validate_package(package_root)
        if not validation.ok:
            raise ValueError(f"Imported package failed validation: {_format_validation_errors(validation.errors)}")
        return ImportResult(
            package_root=package_root,
            source_format=self.source_format,
            source_id=str(root),
            frame_count=int(validation.summary.get("frame_count", 0)),
            warnings=[f"{warning.code}: {warning.message}" for warning in validation.warnings],
        )
```

Use existing helpers from `package_io`: `ensure_dir`, `read_csv_rows`, `write_csv_rows`, `write_json`.

- [ ] **Step 5: Implement package writer rules**

The writer should:

- clear known generated files in output, similar to LeRobot importer but scoped to this importer;
- copy source `frames.csv` to `artifacts/source/csv_recording_frames.csv`;
- generate `frames.csv` with `REQUIRED_TABLE_COLUMNS["frames"]`;
- generate `events.csv`, `labels.csv`, `metrics.csv`;
- write `physical_ai_manifest.json` with `SCHEMA_VERSION`, `scenario_type="arm_pick_sort"`, required manifest sections, and `source_dataset`;
- write `README.md`.

Manifest coordinate frames:

```python
[
    {"frame_id": "station", "parent_frame_id": "", "pose_ref": ""},
    {"frame_id": "robot_base", "parent_frame_id": "station", "pose_ref": ""},
]
```

Objects can be one generic object:

```python
[{"object_id": "recording_object", "type": "fixture_object"}]
```

Devices can include robot and camera:

```python
[
    {"device_id": "robot_arm", "type": "robot"},
    {"device_id": "camera_fixture", "type": "rgb_camera"},
]
```

Manifest `source_dataset` must include:

```python
{
    "format": "csv_recording",
    "root": str(source_root),
    "frames_csv_ref": "artifacts/source/csv_recording_frames.csv",
    "frame_count": len(input_rows),
    "converted_at": _utc_now(),
}
```

- [ ] **Step 6: Implement path and row validation**

Rules:

- `source.root` must be `str` or `Path`, must exist, and must contain `frames.csv`.
- Missing required input columns raises a `ValueError` containing `frames.csv missing required columns`.
- `timestamp_s` and `metric_value` for generated metrics must parse as finite floats.
- `image_path` must be relative to source root and cannot include `..`; absolute paths and parent traversal raise `ValueError`.
- If `copy_images=True` and `image_path` is non-empty, source image must exist.
- If `copy_images=False`, output `image_ref` is empty.

- [ ] **Step 7: Run focused passing tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_importers.py tests/physical_ai_data/test_validation.py -q
```

Expected: all selected tests pass.

- [ ] **Step 8: Commit Task 2**

```bash
git add src/physical_ai_data/csv_recording_importer.py tests/physical_ai_data/test_importers.py
git commit -m "feat: add csv recording importer fixture"
```

---

### Task 3: Documentation and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `docs/stage4/README.md`

- [ ] **Step 1: Update Stage 4 README**

In `docs/stage4/README.md`:

- Update Training Draft Export section to say Stage 4.3 emits `physical-ai-training-eval-draft/v0.2`.
- List the draft manifest boundary: `contract_status=draft`, `formal_format=false`, allowed splits.
- Add the `samples.csv` field list.
- Add a short Python example for `CsvRecordingPackageImporter` using `ImportRequest` and `run_import`.
- State this importer is a fixture, not a production connector or CLI.

- [ ] **Step 2: Update project README**

In `README.md`:

- Add a document link for the Stage 4.3 spec and plan.
- Update current status to mention Stage 4.3 training/evaluation draft v0.2 and non-LeRobot CSV importer fixture.
- Keep Viewer/Blueprint GUI acceptance listed as pending.

- [ ] **Step 3: Update details**

In `details.md` under `2026-06-10`:

- Add Stage 4.3 spec and plan.
- Record training/evaluation draft v0.2 contract.
- Record `CsvRecordingPackageImporter` fixture and its purpose.
- Leave final test result out until full verification has actually run.

In `下一步计划`, keep:

- GUI Viewer/Blueprint 人工视觉验收 when GUI environment is available.
- Move toward Stage 4.4/Stage 5: decide first real business importer candidate, label schema, and formal training export boundary.

- [ ] **Step 4: Run documentation grep check**

Run:

```bash
rg -n "Stage 4\\.3|training-eval-draft/v0\\.2|csv_recording|CsvRecordingPackageImporter|Viewer/Blueprint" README.md details.md docs/stage4/README.md
```

Expected: all new Stage 4.3 concepts are discoverable.

- [ ] **Step 5: Run full verification**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 6: Record final verification result**

After Step 5 passes, update `details.md` with the exact command and result, for example:

```text
本轮最终验证结果：`python -m pytest -q` 返回 `NN passed in X.XXs`。
```

- [ ] **Step 7: Commit Task 3**

```bash
git add README.md details.md docs/stage4/README.md docs/superpowers/plans/2026-06-10-stage-4-3-training-importer-contract.md
git commit -m "docs: document Stage 4.3 training importer contract"
```

---

## Final Integration Checks

- [ ] Run:

```bash
git status --short
git log --oneline --decorate -5
python -m pytest -q
```

Publication steps are intentionally not assigned to implementation subagents. After this plan is implemented and reviewed, the coordinating agent will push the branch, create the PR, wait for remote merge, and clean up the local worktree/branch according to project workflow.
