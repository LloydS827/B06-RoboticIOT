# Stage 10 SDK Adoption Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 B06 的 SDK-first 入口更容易被研发、平台和工程团队稳定采用，补齐 API 文档、可运行示例、错误信息 polish、adoption checklist 和 smoke 覆盖。

**Architecture:** 保持 `physical_ai_data` SDK 为主产品入口，CLI 继续作为薄封装，Stage 8 synthetic fixture 继续作为默认可运行样本。新增内容集中在 `docs/sdk/`、`examples/` 和 focused tests；生产代码只做必要错误信息 polish，不扩展 connector、DB/schema、Web 平台或 H300 现场协议。

**Tech Stack:** Python 3.11+、pytest、现有 `physical_ai_data` SDK/CLI、Stage 8 synthetic fixture、标准库 `subprocess/json/tempfile/pathlib`。

---

## File Structure

- Modify `src/physical_ai_data/pipelines.py`: polish pipeline error text while preserving existing public behavior.
- Modify `src/physical_ai_data/training_export.py`: improve invalid split error text with allowed values and contract context.
- Modify `tests/physical_ai_data/test_pipelines.py`: add red-green coverage for source path and validation path in pipeline errors.
- Modify `tests/physical_ai_data/test_training_export.py`: add red-green coverage for invalid split guidance.
- Create `examples/sdk_pipeline_stage8.py`: runnable SDK pipeline example using Stage 8 synthetic fixture.
- Create `examples/sdk_existing_package_ops.py`: runnable example for top-level SDK operations on an existing package.
- Create `examples/sdk_low_level_importer.py`: runnable low-level importer contract example.
- Create `examples/cli_json_smoke.sh`: runnable CLI smoke that validates JSON fields.
- Create `tests/physical_ai_data/test_examples.py`: subprocess smoke tests for Python examples and shell smoke.
- Modify `docs/sdk/README.md`: expand into SDK adoption guide and API reference.
- Create `docs/sdk/adoption_checklist.md`: adoption checklist for研发/平台/工程团队。
- Create `docs/sdk/demo_ui_evaluation.md`: optional demo UI evaluation, with no implementation commitment.
- Create `docs/sdk/stage8_pipeline_walkthrough.md`: notebook-style Markdown walkthrough, no Jupyter dependency.
- Modify `README.md`: add Stage 10 adoption path and examples/docs links.
- Modify `details.md`: record Stage 10 decisions, outputs, verification, and next-stage plan.

---

### Task 1: Error Message Polish

**Files:**
- Modify: `src/physical_ai_data/pipelines.py`
- Modify: `src/physical_ai_data/training_export.py`
- Test: `tests/physical_ai_data/test_pipelines.py`
- Test: `tests/physical_ai_data/test_training_export.py`

- [ ] **Step 1: Write failing tests for pipeline import error context**

Add to `tests/physical_ai_data/test_pipelines.py`:

```python
def test_run_weld_workcell_pipeline_import_error_includes_clean_root(tmp_path: Path):
    from physical_ai_data.pipelines import run_weld_workcell_pipeline

    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    (fixture.clean_root / "process.csv").unlink()

    with pytest.raises(ValueError) as exc_info:
        run_weld_workcell_pipeline(clean_root=fixture.clean_root, output_dir=tmp_path / "package")

    message = str(exc_info.value)
    assert "weld_workcell pipeline failed during import" in message
    assert str(fixture.clean_root) in message
    assert "process.csv" in message
```

- [ ] **Step 2: Write failing test for validation error path context**

Extend or add the defensive validation failure test in `tests/physical_ai_data/test_pipelines.py`:

```python
assert str(tmp_path / "package") in str(exc_info.value)
```

- [ ] **Step 3: Write failing test for invalid split guidance**

Add to `tests/physical_ai_data/test_training_export.py`:

```python
def test_export_training_eval_draft_invalid_split_mentions_contract_and_allowed_values(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=14)

    with pytest.raises(ValueError) as exc_info:
        export_training_eval_draft(package, split="dev")

    message = str(exc_info.value)
    assert "training/evaluation draft split" in message
    assert "physical-ai-training-eval-draft/v0.2" in message
    assert "unspecified, train, eval, validation, test, holdout" in message
```

- [ ] **Step 4: Run red tests and confirm failure**

Run:

```bash
python -m pytest tests/physical_ai_data/test_pipelines.py tests/physical_ai_data/test_training_export.py -q
```

Expected: the new assertions fail because messages do not yet include source/output path or draft contract context.

- [ ] **Step 5: Implement minimal message polish**

In `src/physical_ai_data/pipelines.py`, change the two `ValueError` messages only:

```python
    except Exception as exc:
        raise ValueError(
            "weld_workcell pipeline failed during import "
            f"(clean_root={Path(clean_root)}): {exc}"
        ) from exc
```

and:

```python
        raise ValueError(
            "weld_workcell pipeline produced invalid package "
            f"(package_root={package_root}): {error_details}"
        )
```

In `src/physical_ai_data/training_export.py`, update `_validate_split` only:

```python
    if split not in TRAINING_EVAL_ALLOWED_SPLITS:
        allowed = ", ".join(TRAINING_EVAL_ALLOWED_SPLITS)
        raise ValueError(
            "training/evaluation draft split must be one of "
            f"{allowed} for {TRAINING_EVAL_EXPORT_FORMAT}; got {split!r}"
        )
```

Do not add new exception classes or error registries.

- [ ] **Step 6: Run focused tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_pipelines.py tests/physical_ai_data/test_training_export.py -q
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/physical_ai_data/pipelines.py src/physical_ai_data/training_export.py tests/physical_ai_data/test_pipelines.py tests/physical_ai_data/test_training_export.py
git commit -m "test: cover SDK adoption error guidance"
```

---

### Task 2: Runnable Examples And Smoke Tests

**Files:**
- Create: `examples/sdk_pipeline_stage8.py`
- Create: `examples/sdk_existing_package_ops.py`
- Create: `examples/sdk_low_level_importer.py`
- Create: `examples/cli_json_smoke.sh`
- Create: `tests/physical_ai_data/test_examples.py`

- [ ] **Step 1: Write failing smoke tests**

Create `tests/physical_ai_data/test_examples.py` with subprocess tests:

```python
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return env


def test_sdk_pipeline_stage8_example_runs(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "examples/sdk_pipeline_stage8.py",
            "--output-root",
            str(tmp_path / "stage8_sdk_example"),
            "--frames",
            "5",
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["validation_ok"] is True
    assert payload["summary"]["frame_count"] == 5
    assert Path(payload["package_root"]).is_dir()
    assert Path(payload["candidates_csv"]).is_file()
    assert Path(payload["training_draft_dir"]).is_dir()
    assert Path(payload["rrd_path"]).is_file()


def test_sdk_existing_package_ops_example_runs(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "examples/sdk_existing_package_ops.py",
            "--output-root",
            str(tmp_path / "existing_ops"),
            "--frames",
            "8",
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["validation_ok"] is True
    assert payload["summary"]["frame_count"] == 8
    assert Path(payload["candidates_csv"]).is_file()
    assert Path(payload["training_draft_dir"]).is_dir()
    assert Path(payload["rrd_path"]).is_file()


def test_sdk_low_level_importer_example_runs(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "examples/sdk_low_level_importer.py",
            "--output-root",
            str(tmp_path / "low_level"),
            "--frames",
            "5",
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["source_format"] == "weld_workcell"
    assert payload["frame_count"] == 5
    assert Path(payload["package_root"]).is_dir()


def test_cli_json_smoke_example_runs(tmp_path: Path):
    result = subprocess.run(
        [
            "bash",
            "examples/cli_json_smoke.sh",
            str(tmp_path / "cli_json"),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["validation"]["ok"] is True
    assert payload["summary"]["frame_count"] == 5
    assert Path(payload["package_root"]).is_dir()
```

- [ ] **Step 2: Run red tests and confirm missing files**

Run:

```bash
python -m pytest tests/physical_ai_data/test_examples.py -q
```

Expected: fails because the examples do not exist yet.

- [ ] **Step 3: Create `examples/sdk_pipeline_stage8.py`**

The script must:

- Parse `--output-root` defaulting to `/tmp/b06_stage10_sdk_pipeline`.
- Parse `--frames` defaulting to `5`.
- Generate Stage 8 synthetic fixture.
- Run `run_weld_workcell_pipeline(..., training_split="eval", output_rrd=...)`.
- Print JSON to stdout with keys `package_root`, `validation_ok`, `summary`, `candidates_csv`, `training_draft_dir`, `rrd_path`.

Implementation outline:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from physical_ai_data.pipelines import run_weld_workcell_pipeline
from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Stage 8 SDK pipeline example.")
    parser.add_argument("--output-root", type=Path, default=Path("/tmp/b06_stage10_sdk_pipeline"))
    parser.add_argument("--frames", type=int, default=5)
    args = parser.parse_args()

    fixture = generate_stage8_h300_synthetic_demo(args.output_root / "fixture", frame_count=args.frames)
    result = run_weld_workcell_pipeline(
        clean_root=fixture.clean_root,
        output_dir=args.output_root / "package",
        training_split="eval",
        output_rrd=args.output_root / "package.rrd",
    )
    print(json.dumps({
        "package_root": str(result.package_root),
        "validation_ok": result.validation.ok,
        "summary": result.summary,
        "candidates_csv": str(result.candidates_csv) if result.candidates_csv else None,
        "training_draft_dir": str(result.training_draft_dir) if result.training_draft_dir else None,
        "rrd_path": str(result.rrd_path) if result.rrd_path else None,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Create `examples/sdk_existing_package_ops.py`**

The script must:

- Generate a deterministic welding package with `generate_welding_package`.
- Call top-level SDK functions: `validate`, `summarize`, `export_candidates_csv`, `export_training_eval_draft`, `convert_to_rerun`.
- Print JSON with the same style of path fields.

- [ ] **Step 5: Create `examples/sdk_low_level_importer.py`**

The script must:

- Generate Stage 8 fixture.
- Use `ImportRequest`, `run_import`, and `WeldWorkcellPackageImporter`.
- Print JSON with `package_root`, `source_format`, `source_id`, `frame_count`, `warnings`.

- [ ] **Step 6: Create `examples/cli_json_smoke.sh`**

The script must:

- Use `set -euo pipefail`.
- Accept an optional output root argument, default `/tmp/b06_stage10_cli_json_smoke`.
- Generate Stage 8 fixture using:

```bash
python scripts/generate_stage8_h300_synthetic_demo.py --output-root "$OUTPUT_ROOT/fixture" --frames 5
```

- Run:

```bash
python scripts/physical_ai_package.py run-weld-workcell \
  --clean-root "$OUTPUT_ROOT/fixture/clean/weld_workcell" \
  --output-dir "$OUTPUT_ROOT/package" \
  --training-split eval \
  --output-rrd "$OUTPUT_ROOT/package.rrd" \
  --json
```

- Pipe the JSON through a Python one-liner that asserts:
  - `payload["validation"]["ok"] is True`
  - `payload["summary"]["frame_count"] == 5`
  - `payload["package_root"]`
- Print the validated JSON payload to stdout.

- [ ] **Step 7: Run focused example tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_examples.py -q
```

Expected: all example tests pass.

- [ ] **Step 8: Commit**

```bash
git add examples tests/physical_ai_data/test_examples.py
git commit -m "test: add runnable SDK adoption examples"
```

---

### Task 3: SDK Adoption Documentation

**Files:**
- Modify: `docs/sdk/README.md`
- Create: `docs/sdk/adoption_checklist.md`
- Create: `docs/sdk/demo_ui_evaluation.md`
- Create: `docs/sdk/stage8_pipeline_walkthrough.md`

- [ ] **Step 1: Inventory public SDK APIs before editing**

Read these files and list the public surfaces in your notes before editing:

```bash
sed -n '1,220p' src/physical_ai_data/__init__.py
sed -n '1,260p' src/physical_ai_data/sdk.py
sed -n '1,260p' src/physical_ai_data/pipelines.py
sed -n '1,220p' src/physical_ai_data/importers.py
sed -n '1,120p' src/physical_ai_data/weld_workcell_importer.py
```

Public surfaces to cover:

- Top-level SDK: `validate`, `summarize`, `export_candidates_csv`, `export_training_eval_draft`, `convert_to_rerun`.
- Pipeline helper: `run_weld_workcell_pipeline`, `PipelineResult`.
- Importer contract: `ImportRequest`, `ImportResult`, `run_import`, `WeldWorkcellPackageImporter`.
- Demo helper as non-top-level API: `generate_stage8_h300_synthetic_demo`.

- [ ] **Step 2: Expand `docs/sdk/README.md`**

Keep the existing SDK-first positioning, then add sections:

- `安装与运行前提`: `python -m pip install -e ".[dev]"` and run commands from repo root.
- `公共 API 总览`: table with API, input state, output, file side effects.
- `返回对象`: fields for `ValidationResult`, `PipelineResult`, `ImportRequest`, `ImportResult`.
- `Pipeline helper`: defaults, optional output controls, skip behavior.
- `低层 importer contract`: when to use it instead of pipeline helper.
- `错误排查`: missing Clean Zone files, invalid package, invalid split, image path issues.
- `CLI 到 SDK 的映射`: CLI command to SDK function/helper.
- `Examples`: links to `examples/*.py`, `examples/cli_json_smoke.sh`, and `stage8_pipeline_walkthrough.md`.
- `边界`: no production connector, DB/schema, Web app, H300 protocol.

- [ ] **Step 3: Create `docs/sdk/adoption_checklist.md`**

Include:

- Environment setup.
- Synthetic demo path.
- Clean Zone replacement path.
- Minimal acceptance commands.
- Output checklist: manifest, summary, candidates, training draft, `.rrd`.
- Data sensitivity and non-commit boundaries.
- When to return to Stage 8 gap register.

- [ ] **Step 4: Create `docs/sdk/demo_ui_evaluation.md`**

Include:

- Why no UI is implemented in Stage 10.
- Candidate users and display surfaces.
- Minimal UI shape if future trigger is met.
- Trigger conditions: one de-identified H300 sample, stable SDK examples, clear review need.
- Explicit non-goals: no platform, no auth, no DB, no connector.

- [ ] **Step 5: Create `docs/sdk/stage8_pipeline_walkthrough.md`**

Make it notebook-style Markdown:

- Step 1 install.
- Step 2 generate Stage 8 fixture.
- Step 3 run SDK pipeline Python snippet.
- Step 4 inspect summary and output paths.
- Step 5 run CLI JSON smoke.
- Step 6 read gap register before real/de-identified replacement.

Do not require Jupyter or new dependencies.

- [ ] **Step 6: Run docs keyword scan**

Run:

```bash
rg -n "run_weld_workcell_pipeline|PipelineResult|ImportRequest|examples/sdk_pipeline_stage8.py|adoption checklist|demo UI|production connector|DB schema|H300" docs/sdk
```

Expected: exit 0 and shows coverage in the new/updated SDK docs. Treat this as a human coverage check, not a wording lock; equivalent English/Chinese wording is acceptable if the public API, examples, adoption checklist, demo UI evaluation, and boundary statements are covered.

- [ ] **Step 7: Commit**

```bash
git add docs/sdk/README.md docs/sdk/adoption_checklist.md docs/sdk/demo_ui_evaluation.md docs/sdk/stage8_pipeline_walkthrough.md
git commit -m "docs: harden SDK adoption guide"
```

---

### Task 4: Project Docs And Final Verification

**Files:**
- Modify: `README.md`
- Modify: `details.md`

- [ ] **Step 1: Update README**

Add Stage 10 adoption path near the project usage area:

- Install with `python -m pip install -e ".[dev]"`.
- Generate Stage 8 synthetic fixture.
- Run SDK pipeline or `physical-ai-package run-weld-workcell`.
- Try examples from `examples/`.
- Use `docs/sdk/adoption_checklist.md` before replacing Clean Zone data.
- Use Stage 8 gap register before real/de-identified H300 replacement.

Also add links to:

- `docs/sdk/README.md`
- `docs/sdk/adoption_checklist.md`
- `docs/sdk/stage8_pipeline_walkthrough.md`
- `docs/sdk/demo_ui_evaluation.md`
- `examples/sdk_pipeline_stage8.py`

Keep the boundary clear: no production connector, DB/schema, complete Web platform, or H300 field protocol.

- [ ] **Step 2: Update details**

Append a `2026-06-23` Stage 10 subsection after the Stage 9 notes:

- Stage 10 decision: SDK adoption hardening.
- Outputs: spec, plan, examples, SDK docs, adoption checklist, demo UI evaluation, error polish, smoke tests.
- Verification commands should be listed as pending; do not fill pass/fail results yet.
- Next plan: Stage 11 H300 sample replacement readiness only after real/de-identified sample is available.

Update `下一步计划`:

1. Real/de-identified H300 sample replacement via Stage 8 gap register.
2. Optional demo UI only after sample/adoption triggers.
3. Avoid production connector/DB/schema/full Web platform until sample-driven gaps justify them.

- [ ] **Step 3: Run focused verification**

Run:

```bash
python -m pytest tests/physical_ai_data/test_pipelines.py tests/physical_ai_data/test_training_export.py tests/physical_ai_data/test_examples.py tests/physical_ai_data/test_cli.py tests/physical_ai_data/test_sdk.py -q
```

Expected: all selected tests pass.

- [ ] **Step 4: Run examples manually**

Run:

```bash
python examples/sdk_pipeline_stage8.py --output-root /tmp/b06_stage10_sdk_pipeline_verify --frames 5
python examples/sdk_existing_package_ops.py --output-root /tmp/b06_stage10_existing_ops_verify --frames 8
python examples/sdk_low_level_importer.py --output-root /tmp/b06_stage10_low_level_verify --frames 5
bash examples/cli_json_smoke.sh /tmp/b06_stage10_cli_json_verify
```

Expected: each command exits 0 and prints valid JSON with expected frame counts.

- [ ] **Step 5: Run full test suite**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 6: Run boundary scan**

Run:

```bash
rg -n "production connector|DB schema|完整 Web 平台|H300 现场协议|真实 H300 协议|真实数据试点" README.md details.md docs/sdk docs/superpowers/specs/2026-06-23-stage-10-sdk-adoption-hardening-design.md docs/superpowers/plans/2026-06-23-stage-10-sdk-adoption-hardening.md
```

Expected: any matches are boundary or non-goal statements, not claims that these capabilities are implemented.

- [ ] **Step 7: Backfill `details.md` verification results**

After Steps 3-6 have actually run, update the Stage 10 `details.md` subsection with the exact commands and observed results:

- focused verification command and pass count.
- manual example commands and success status.
- full `python -m pytest -q` pass count.
- boundary scan result, noting that matches are non-goal/boundary statements.

Do not invent results. If a command failed and was fixed, record the final passing command and keep any useful limitation note concise.

- [ ] **Step 8: Commit**

```bash
git add README.md details.md
git commit -m "docs: record Stage 10 SDK adoption hardening"
```

---

## Final Integration

- [ ] Re-run `git status --short` and ensure only intended files changed.
- [ ] If any verification command failed, fix before PR.
- [ ] Push branch `codex/stage-10-sdk-adoption-hardening`.
- [ ] Create PR against `main`.
- [ ] Merge PR remotely after checks are acceptable.
- [ ] Switch back to `main`, pull merged changes, delete local branch.
- [ ] Summarize Stage 10 and propose Stage 11 only as sample-driven H300 replacement readiness.
