# Stage 11 H300 Sample Replacement Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为真实/脱敏 H300 最小样本到位后的替换评审提供轻量 readiness checker、CLI 入口和 Stage 11 文档路径，同时保持 Stage 8 synthetic demo 作为默认可运行链路。

**Architecture:** 新增独立 `physical_ai_data.stage11_readiness` 模块，只读取本地 Clean/Raw 目录并返回结构化 report，不写 package、不联网、不提交真实样本。CLI 只作为薄封装调用该 SDK helper；README/details/docs 记录 Stage 11 定位、边界、验证和下一阶段计划。

**Tech Stack:** Python 3.11+、pytest、argparse、dataclasses、csv/json/pathlib、现有 Stage 8 synthetic fixture 和 `physical-ai-package` CLI。

---

## File Structure

- Create `src/physical_ai_data/stage11_readiness.py`: SDK readiness checker, report dataclasses, Clean/Raw file checks, gap status mapping, JSON-ready payload.
- Create `tests/physical_ai_data/test_stage11_readiness.py`: focused SDK tests for Stage 8 fixture, blocked Clean files, missing images, Clean-only Raw gap behavior, and report serialization.
- Modify `src/physical_ai_data/cli.py`: add `assess-h300-readiness` subcommand and JSON/text output.
- Modify `tests/physical_ai_data/test_cli.py`: add CLI argument mapping and JSON smoke coverage for Stage 11 readiness.
- Create `docs/stage11/README.md`: Stage 11 sample replacement readiness workflow, input expectations, commands, gap status interpretation, non-goals, next-stage gate.
- Modify `README.md`: add Stage 11 to adoption path, current first sample replacement readiness, current capabilities, engineering handoff links, route plan, and next-stage note.
- Modify `details.md`: record Stage 11 decisions, deliverables, verification results, and Stage 12 recommendation.

---

### Task 1: SDK Readiness Checker

**Files:**
- Create: `src/physical_ai_data/stage11_readiness.py`
- Create: `tests/physical_ai_data/test_stage11_readiness.py`

- [ ] **Step 1: Write failing SDK tests**

Create `tests/physical_ai_data/test_stage11_readiness.py`:

```python
from __future__ import annotations

import csv
from pathlib import Path

from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo
from physical_ai_data.stage11_readiness import assess_h300_sample_readiness


def _gap_status(report, gap_id: str):
    return next(gap for gap in report.gap_statuses if gap.gap_id == gap_id)


def test_stage11_readiness_stage8_fixture_with_raw_is_review_required(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")

    report = assess_h300_sample_readiness(fixture.clean_root, raw_root=fixture.raw_root)

    assert report.overall_status == "review_required"
    assert report.summary["clean_required_files_present"] is True
    assert report.summary["frame_count"] == 5
    assert len(report.gap_statuses) == 12
    assert all(check.status != "block" for check in report.checks)
    assert _gap_status(report, "G-001").status == "ready_to_review"
    assert _gap_status(report, "G-002").status == "ready_to_review"
    assert _gap_status(report, "G-003").status == "needs_raw_review"
    assert _gap_status(report, "G-004").status == "needs_raw_review"
    assert _gap_status(report, "G-005").status == "needs_raw_review"
    assert _gap_status(report, "G-010").status == "needs_raw_review"
    assert _gap_status(report, "G-011").status == "needs_raw_review"
    assert _gap_status(report, "G-012").status == "needs_raw_review"
    payload = report.to_dict()
    assert payload["overall_status"] == "review_required"
    assert payload["gap_statuses"][0]["gap_id"] == "G-001"


def test_stage11_readiness_blocks_missing_required_clean_file(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    (fixture.clean_root / "process.csv").unlink()

    report = assess_h300_sample_readiness(fixture.clean_root, raw_root=fixture.raw_root)

    assert report.overall_status == "blocked"
    assert any(check.check_id == "clean_required:process.csv" and check.status == "block" for check in report.checks)


def test_stage11_readiness_blocks_missing_image_reference(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    (fixture.clean_root / "images" / "front_0000.png").unlink()

    report = assess_h300_sample_readiness(fixture.clean_root, raw_root=fixture.raw_root)

    assert report.overall_status == "blocked"
    assert any(check.check_id == "frames:image_path" and check.status == "block" for check in report.checks)


def test_stage11_readiness_allows_empty_image_references(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")

    report = assess_h300_sample_readiness(fixture.clean_root, raw_root=fixture.raw_root)

    assert report.overall_status == "review_required"
    assert all(check.status != "block" for check in report.checks)


def test_stage11_readiness_clean_only_keeps_raw_gaps_blocked_without_blocking_overall(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")

    report = assess_h300_sample_readiness(fixture.clean_root)

    assert report.overall_status == "review_required"
    assert _gap_status(report, "G-003").status == "blocked"
    assert _gap_status(report, "G-004").status == "blocked"
    assert _gap_status(report, "G-005").status == "blocked"
    assert _gap_status(report, "G-010").status == "needs_raw_review"
    assert _gap_status(report, "G-011").status == "blocked"
    assert _gap_status(report, "G-012").status == "blocked"


def test_stage11_readiness_raw_artifact_gaps_do_not_block_pipeline_smoke(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    (fixture.raw_root / "manifest.raw.json").unlink()
    (fixture.raw_root / "files" / "model_outputs.json").unlink()

    report = assess_h300_sample_readiness(fixture.clean_root, raw_root=fixture.raw_root)

    assert report.overall_status == "review_required"
    assert _gap_status(report, "G-005").status == "blocked"
    assert any(check.check_id == "raw:manifest.raw.json" and check.status == "review" for check in report.checks)


def test_stage11_readiness_blocks_missing_timestamp_column(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    frames_path = fixture.clean_root / "frames.csv"
    rows = list(csv.DictReader(frames_path.open(newline="", encoding="utf-8")))
    fieldnames = [field for field in rows[0] if field != "timestamp_s"]
    with frames_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row.pop("timestamp_s", None)
            writer.writerow(row)

    report = assess_h300_sample_readiness(fixture.clean_root)

    assert report.overall_status == "blocked"
    assert any(check.check_id == "frames:timestamp_s" and check.status == "block" for check in report.checks)
```

- [ ] **Step 2: Run red tests and confirm failure**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage11_readiness.py -q
```

Expected: import failure because `physical_ai_data.stage11_readiness` does not exist.

- [ ] **Step 3: Implement minimal SDK checker**

Create `src/physical_ai_data/stage11_readiness.py` with:

```python
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CHECK_PASS = "pass"
CHECK_REVIEW = "review"
CHECK_BLOCK = "block"

OVERALL_READY = "ready_for_pipeline_smoke"
OVERALL_REVIEW = "review_required"
OVERALL_BLOCKED = "blocked"

GAP_READY = "ready_to_review"
GAP_RAW_REVIEW = "needs_raw_review"
GAP_BLOCKED = "blocked"
GAP_NOT_APPLICABLE = "not_applicable"

REQUIRED_CLEAN_FILES = ("job.json", "frames.csv", "process.csv", "events.csv")
TCP_POSE_COLUMNS = ("tcp_x", "tcp_y", "tcp_z")
JOB_ID_KEYS = ("job_window_id", "task_id", "work_order_id", "job_id")


@dataclass(frozen=True)
class ReadinessCheck:
    check_id: str
    status: str
    message: str
    path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "check_id": self.check_id,
            "status": self.status,
            "message": self.message,
            "path": self.path,
        }


@dataclass(frozen=True)
class GapStatus:
    gap_id: str
    status: str
    evidence: str
    next_step: str

    def to_dict(self) -> dict[str, object]:
        return {
            "gap_id": self.gap_id,
            "status": self.status,
            "evidence": self.evidence,
            "next_step": self.next_step,
        }


@dataclass(frozen=True)
class H300ReadinessReport:
    clean_root: Path
    raw_root: Path | None
    overall_status: str
    checks: list[ReadinessCheck]
    gap_statuses: list[GapStatus]
    summary: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "clean_root": str(self.clean_root),
            "raw_root": str(self.raw_root) if self.raw_root is not None else None,
            "overall_status": self.overall_status,
            "checks": [check.to_dict() for check in self.checks],
            "gap_statuses": [gap.to_dict() for gap in self.gap_statuses],
            "summary": self.summary,
        }
```

Implementation details:

- `assess_h300_sample_readiness(clean_root, raw_root=None)` converts paths to `Path`, appends checks, builds summary, maps gaps, and returns `H300ReadinessReport`.
- Required file checks:
  - Missing required file -> `ReadinessCheck("clean_required:<name>", "block", ..., path=str(path))`.
  - Present required file -> `pass`.
- `job.json`:
  - If readable JSON and contains at least one `JOB_ID_KEYS` key either at top level or under `job`/`window`, add pass check.
  - If no ID clue, add block check `job:id_fields`.
- `frames.csv`:
  - Parse with `csv.DictReader`.
  - Missing or empty headers -> block `frames:readable`.
  - No rows -> block `frames:rows`.
  - Missing `timestamp_s` -> block `frames:timestamp_s`.
  - Missing any `TCP_POSE_COLUMNS` -> block `frames:tcp_pose`.
  - If `image_path` column exists, empty values are allowed and mean this frame has no image. Non-empty values must be relative, non-escaping, symlink-safe, and point to existing files; violations block `frames:image_path`.
- `process.csv` and `events.csv`: parse headers; missing headers -> block `<file>:header`.
- `review_labels.csv`: present -> review/pass check; absent -> review check, not block.
- Raw artifact evidence:
  - If `raw_root` is provided and `manifest.raw.json` is missing or unreadable, add a `review` check, not a `block` check.
  - Raw/source artifact gaps never make `overall_status` blocked by themselves; they are represented through gap statuses and review checks.
  - Check these paths explicitly:
    - G-003: `files/point_clouds/window_0000.pcd`, `files/pcl_seam_candidates.json`
    - G-004: `files/images/front_0000.png`
    - G-005: `files/model_outputs.json`
    - G-009: `files/quality_result.json`
    - G-011: `tcp_json/hmi_task_messages.ndjson`
    - G-012: `files/seam_trajectory.json`, `files/pcl_seam_candidates.json`
- Overall status:
  - If any check status is `block`, `blocked`.
  - Else if any check status is `review`, or any gap status is not `ready_to_review`, `review_required`.
  - Else `ready_for_pipeline_smoke`.
- Gap mapping:
  - G-001: `ready_to_review` if job ID clue is present, else `blocked`.
  - G-002: `ready_to_review` if timestamp and TCP pose checks pass, else `blocked`.
  - G-003/G-004/G-005/G-011/G-012: `needs_raw_review` if corresponding raw evidence exists, else `blocked`.
  - G-006: `ready_to_review` if `review_labels.csv` exists, else `needs_raw_review`.
  - G-007: `ready_to_review` if `process.csv` header check passes, else `blocked`.
  - G-008: `ready_to_review` if `events.csv` header check passes, else `blocked`.
  - G-009: `needs_raw_review` if `review_labels.csv` or raw quality result exists, else `blocked`.
  - G-010: always `needs_raw_review`.
- Keep helper functions private and focused: `_read_csv_rows`, `_load_job`, `_has_job_id_clue`, `_path_exists_within_root`, `_raw_evidence`.

- [ ] **Step 4: Run focused SDK tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage11_readiness.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/physical_ai_data/stage11_readiness.py tests/physical_ai_data/test_stage11_readiness.py
git commit -m "feat: add H300 sample readiness checker"
```

---

### Task 2: CLI Readiness Entry

**Files:**
- Modify: `src/physical_ai_data/cli.py`
- Modify: `tests/physical_ai_data/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Add to `tests/physical_ai_data/test_cli.py`:

```python
def test_cli_assess_h300_readiness_maps_args(monkeypatch, tmp_path: Path, capsys):
    from physical_ai_data import cli
    from physical_ai_data.stage11_readiness import H300ReadinessReport

    calls = []

    def fake_assess(clean_root, raw_root=None):
        calls.append((clean_root, raw_root))
        return H300ReadinessReport(
            clean_root=Path(clean_root),
            raw_root=Path(raw_root) if raw_root is not None else None,
            overall_status="review_required",
            checks=[],
            gap_statuses=[],
            summary={"frame_count": 5},
        )

    monkeypatch.setattr(cli, "assess_h300_sample_readiness", fake_assess)

    result = cli.main(
        [
            "assess-h300-readiness",
            "--clean-root",
            str(tmp_path / "clean"),
            "--raw-root",
            str(tmp_path / "raw"),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert result == 0
    assert calls == [(tmp_path / "clean", tmp_path / "raw")]
    assert payload["overall_status"] == "review_required"
    assert payload["summary"]["frame_count"] == 5


def test_cli_assess_h300_readiness_stage8_json_smoke(tmp_path: Path):
    from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo

    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")

    result = _run(
        [
            "assess-h300-readiness",
            "--clean-root",
            str(fixture.clean_root),
            "--raw-root",
            str(fixture.raw_root),
            "--json",
        ]
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["overall_status"] == "review_required"
    assert payload["summary"]["frame_count"] == 5
    assert len(payload["gap_statuses"]) == 12
```

- [ ] **Step 2: Run red tests and confirm failure**

Run:

```bash
python -m pytest tests/physical_ai_data/test_cli.py::test_cli_assess_h300_readiness_maps_args tests/physical_ai_data/test_cli.py::test_cli_assess_h300_readiness_stage8_json_smoke -q
```

Expected: parser does not know `assess-h300-readiness`.

- [ ] **Step 3: Implement CLI command**

In `src/physical_ai_data/cli.py`:

- Import `assess_h300_sample_readiness`.
- Add subparser after `run-weld-workcell`:

```python
    readiness = subcommands.add_parser(
        "assess-h300-readiness",
        help="Assess H300 Clean/Raw sample replacement readiness.",
    )
    readiness.add_argument("--clean-root", type=Path, required=True, help="Clean weld workcell root directory.")
    readiness.add_argument("--raw-root", type=Path, help="Optional Raw Zone root directory for source artifact checks.")
    readiness.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    readiness.set_defaults(func=_assess_h300_readiness)
```

- Add handler:

```python
def _assess_h300_readiness(args: argparse.Namespace) -> int:
    report = assess_h300_sample_readiness(args.clean_root, raw_root=args.raw_root)
    if args.json:
        _print_json(report.to_dict())
        return 0

    print(f"H300 readiness: {report.overall_status}")
    print(f"clean_root: {report.clean_root}")
    if report.raw_root is not None:
        print(f"raw_root: {report.raw_root}")
    for check in report.checks:
        if check.status != "pass":
            location = f" ({check.path})" if check.path else ""
            print(f"- {check.status}: {check.check_id}: {check.message}{location}")
    for gap in report.gap_statuses:
        if gap.status != "ready_to_review":
            print(f"- gap {gap.gap_id}: {gap.status}: {gap.next_step}")
    return 0
```

Do not make `overall_status=blocked` return non-zero; this command is an assessment tool and should return 0 when the assessment itself succeeds.

- [ ] **Step 4: Run focused CLI tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_cli.py::test_cli_assess_h300_readiness_maps_args tests/physical_ai_data/test_cli.py::test_cli_assess_h300_readiness_stage8_json_smoke -q
```

Expected: both tests pass.

- [ ] **Step 5: Run combined Stage 11 tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage11_readiness.py tests/physical_ai_data/test_cli.py -q
```

Expected: selected tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/physical_ai_data/cli.py tests/physical_ai_data/test_cli.py
git commit -m "feat: expose H300 readiness assessment in CLI"
```

---

### Task 3: Stage 11 Docs And Route Updates

**Files:**
- Create: `docs/stage11/README.md`
- Modify: `README.md`
- Modify: `details.md`

- [ ] **Step 1: Create Stage 11 docs**

Create `docs/stage11/README.md` in Chinese. It must cover:

- Stage 11 定位：H300 sample replacement readiness，不是 real data pilot 完成态。
- 输入边界：
  - `weld_workcell` Clean Zone root is required.
  - optional Raw Zone root can provide source artifact evidence.
  - real/de-identified samples stay in local/onsite controlled directories and are not committed.
- Recommended flow:
  1. Generate/run Stage 8 synthetic fixture as baseline.
  2. Point `assess_h300_sample_readiness` or CLI to the candidate Clean/Raw roots.
  3. If `overall_status=blocked`, fix Clean Zone replacement before pipeline smoke.
  4. If `review_required`, run `physical-ai-package run-weld-workcell` smoke and review gap statuses.
  5. Close/split/escalate Stage 8 gaps manually.
- SDK and CLI examples.
- Gap status interpretation: `ready_to_review`, `needs_raw_review`, `blocked`, `not_applicable`.
- Non-goals: no production connector, DB/schema, package schema changes, demo UI, A02 converter, H300 field protocol.
- Stage 12 gate: at least one de-identified H300 minimum job window sample with access/submission boundary confirmed.

- [ ] **Step 2: Update README**

Modify `README.md`:

- In `如何使用本项目`, mention Stage 11 readiness checker after Stage 10 adoption path and before real sample replacement.
- In current first sample/current capability sections, state current post-Stage-10 next step is Stage 11 sample replacement readiness, not real data pilot completion.
- Add `docs/stage11/README.md` to A01/H300 reading list.
- Add Stage 11 section to route planning after Stage 8/10 narrative.
- Preserve existing non-goals and do not claim real H300 sample exists in repo.

- [ ] **Step 3: Update details**

Modify `details.md`:

- Add a new `### 2026-06-24` entry.
- Record:
  - Stage 11 decision and assumptions.
  - New files.
  - Readiness checker behavior and boundaries.
  - Verification commands to be filled with final observed results after Task 3 verification.
  - Next-stage recommendation: Stage 12 first de-identified H300 sample replacement pilot only after at least one de-identified sample passes access/submission boundary.

- [ ] **Step 4: Run documentation scans**

Run:

```bash
rg -n "Stage 11|sample replacement readiness|assess-h300-readiness|gap register|Stage 12|脱敏 H300|不实现 production connector|不修改 Physical AI Package" README.md details.md docs/stage11 docs/superpowers/specs/2026-06-24-stage-11-h300-sample-replacement-readiness-design.md
```

Expected: exit 0 with hits in README, details, docs/stage11, and spec.

Run:

```bash
rg -n "真实 H300 样本已|real data pilot 已完成|生产 connector 已完成|H300 现场协议已确定|DB schema 已完成|demo UI 已实现" README.md details.md docs/stage11
```

Expected: exit 1 with no matches.

- [ ] **Step 5: Run final verification**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage11_readiness.py tests/physical_ai_data/test_cli.py -q
python -m pytest -q
python scripts/generate_stage8_h300_synthetic_demo.py --output-root /tmp/stage11_h300_demo --frames 5
physical-ai-package assess-h300-readiness --clean-root /tmp/stage11_h300_demo/clean/weld_workcell --raw-root /tmp/stage11_h300_demo/raw --json
```

Expected:

- Focused tests pass.
- Full test suite passes.
- Stage 8 generator exits 0.
- CLI readiness JSON returns `overall_status: "review_required"`, `summary.frame_count: 5`, and 12 gap statuses.

- [ ] **Step 6: Fill details verification results**

Update `details.md` with exact observed verification results from Step 5. Do not claim tests pass until Step 5 has actually run.

- [ ] **Step 7: Commit**

```bash
git add docs/stage11/README.md README.md details.md
git commit -m "docs: document Stage 11 sample readiness workflow"
```

---

## Final Verification

After all tasks and reviews complete, run:

```bash
git status --short
python -m pytest tests/physical_ai_data/test_stage11_readiness.py tests/physical_ai_data/test_cli.py -q
python -m pytest -q
rm -rf /tmp/stage11_h300_demo
python scripts/generate_stage8_h300_synthetic_demo.py --output-root /tmp/stage11_h300_demo --frames 5
physical-ai-package assess-h300-readiness --clean-root /tmp/stage11_h300_demo/clean/weld_workcell --raw-root /tmp/stage11_h300_demo/raw --json
rg -n "Stage 11|sample replacement readiness|assess-h300-readiness|gap register|Stage 12|脱敏 H300|不实现 production connector|不修改 Physical AI Package" README.md details.md docs/stage11 docs/superpowers/specs/2026-06-24-stage-11-h300-sample-replacement-readiness-design.md
rg -n "真实 H300 样本已|real data pilot 已完成|生产 connector 已完成|H300 现场协议已确定|DB schema 已完成|demo UI 已实现" README.md details.md docs/stage11
```

Expected:

- `git status --short` only shows intended branch changes or is clean after final commit.
- Focused and full tests pass.
- Readiness JSON reports `review_required` for Stage 8 synthetic fixture with Raw evidence.
- Positive documentation scan exits 0.
- Miscommitment scan exits 1 with no matches.
