# Stage 11.1 SDK Real-Data Onboarding Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing SDK-first data整理 path easier for engineers who receive candidate real/de-identified H300 Clean/Raw roots, without expanding into Stage 12 sample replacement, production connectors, DB, UI, or schema changes.

**Architecture:** Keep `physical_ai_data` as the public SDK surface, reuse the existing Stage 11 readiness checker, and add only thin productization helpers: stable `PipelineResult.to_dict()`, an SDK environment doctor, one real/de-identified candidate onboarding example, and one concise onboarding guide. The CLI remains a thin wrapper over SDK functions.

**Tech Stack:** Python 3.11+, stdlib `argparse`/`dataclasses`/`importlib`/`shutil`, existing `pytest`, existing `physical_ai_data` modules.

---

## File Structure

- Modify `src/physical_ai_data/sdk.py`: re-export Stage 11 readiness API and environment doctor helper.
- Modify `src/physical_ai_data/__init__.py`: expose the same public SDK additions.
- Modify `src/physical_ai_data/pipelines.py`: add `PipelineResult.to_dict()` and local serialization helpers.
- Create `src/physical_ai_data/environment.py`: inspect current SDK import path, Python executable, console entrypoint, and optional dependency availability.
- Modify `src/physical_ai_data/cli.py`: add `doctor` command and use `PipelineResult.to_dict()` for pipeline JSON.
- Create `examples/sdk_real_data_onboarding.py`: candidate Clean/Raw root onboarding template.
- Modify `tests/physical_ai_data/test_sdk.py`: public exports and subprocess import hygiene.
- Modify `tests/physical_ai_data/test_pipelines.py`: `PipelineResult.to_dict()` contract.
- Modify `tests/physical_ai_data/test_cli.py`: doctor CLI behavior and pipeline JSON reuse.
- Modify `tests/physical_ai_data/test_examples.py`: real-data onboarding example happy path and blocked path.
- Create `tests/physical_ai_data/test_environment.py`: environment report contract.
- Create `docs/sdk/real_data_onboarding.md`: one-page candidate real/de-identified data整理 guide.
- Modify `docs/sdk/README.md`, `docs/sdk/adoption_checklist.md`, `README.md`, and `details.md`: point users to Stage 11.1 onboarding and record boundaries.

## Task 1: Public SDK Surface And Pipeline Result Serialization

**Files:**
- Modify: `src/physical_ai_data/sdk.py`
- Modify: `src/physical_ai_data/__init__.py`
- Modify: `src/physical_ai_data/pipelines.py`
- Modify: `src/physical_ai_data/cli.py`
- Modify: `tests/physical_ai_data/test_sdk.py`
- Modify: `tests/physical_ai_data/test_pipelines.py`
- Modify: `tests/physical_ai_data/test_cli.py`

- [ ] **Step 1: Write failing public SDK export test**

Update `tests/physical_ai_data/test_sdk.py::test_top_level_exports_sdk_functions` to import and assert callability/type exports for:

```python
from physical_ai_data import (
    GapStatus,
    H300ReadinessReport,
    ReadinessCheck,
    assess_h300_sample_readiness,
)
```

Update expected `physical_ai_data.__all__` and `physical_ai_data.sdk.__all__` to include these names.

- [ ] **Step 2: Verify the SDK export test fails**

Run:

```bash
python -m pytest tests/physical_ai_data/test_sdk.py::test_top_level_exports_sdk_functions -q
```

Expected: FAIL because the top-level SDK does not export Stage 11 readiness names.

- [ ] **Step 3: Implement public SDK exports**

In `src/physical_ai_data/sdk.py`, import from `physical_ai_data.stage11_readiness`:

```python
from physical_ai_data.stage11_readiness import (
    GapStatus,
    H300ReadinessReport,
    ReadinessCheck,
    assess_h300_sample_readiness,
)
```

Add the four names to `__all__`.

In `src/physical_ai_data/__init__.py`, import the same names from `physical_ai_data.sdk` and add them to `__all__`.

- [ ] **Step 4: Verify public SDK export test passes**

Run:

```bash
python -m pytest tests/physical_ai_data/test_sdk.py::test_top_level_exports_sdk_functions -q
```

Expected: PASS.

- [ ] **Step 5: Write failing `PipelineResult.to_dict()` test**

Add a test to `tests/physical_ai_data/test_pipelines.py` using the Stage 8 fixture and `run_weld_workcell_pipeline(...)`. Assert:

```python
payload = result.to_dict()
assert payload["package_root"] == str(package_root)
assert payload["validation"]["ok"] is True
assert payload["summary"]["frame_count"] == 5
assert payload["candidates_csv"] == str(package_root / "derived" / "candidates.csv")
assert payload["training_draft_dir"] == str(package_root / "derived" / "training_eval")
assert payload["rrd_path"] == str(output_rrd)
```

- [ ] **Step 6: Verify `PipelineResult.to_dict()` test fails**

Run:

```bash
python -m pytest tests/physical_ai_data/test_pipelines.py::test_pipeline_result_to_dict_matches_cli_payload_contract -q
```

Expected: FAIL with `AttributeError: 'PipelineResult' object has no attribute 'to_dict'`.

- [ ] **Step 7: Implement `PipelineResult.to_dict()`**

In `src/physical_ai_data/pipelines.py`, import `asdict` from `dataclasses` and add:

```python
    def to_dict(self) -> dict[str, object]:
        return {
            "package_root": str(self.package_root),
            "validation": {
                "ok": self.validation.ok,
                "summary": self.validation.summary,
                "errors": [asdict(error) for error in self.validation.errors],
                "warnings": [asdict(warning) for warning in self.validation.warnings],
            },
            "summary": self.summary,
            "candidates_csv": _optional_path(self.candidates_csv),
            "training_draft_dir": _optional_path(self.training_draft_dir),
            "rrd_path": _optional_path(self.rrd_path),
        }
```

Add module helper:

```python
def _optional_path(path: Path | None) -> str | None:
    return str(path) if path is not None else None
```

- [ ] **Step 8: Make CLI pipeline JSON use `PipelineResult.to_dict()`**

In `src/physical_ai_data/cli.py`, change `_pipeline_payload(result)` to:

```python
def _pipeline_payload(result: PipelineResult) -> dict[str, object]:
    return result.to_dict()
```

Keep `_optional_path` only if still used elsewhere; otherwise remove it.

- [ ] **Step 9: Add CLI payload delegation test**

Add to `tests/physical_ai_data/test_cli.py`:

```python
def test_cli_pipeline_payload_delegates_to_result_to_dict(monkeypatch, tmp_path: Path):
    from physical_ai_data import cli
    from physical_ai_data.pipelines import PipelineResult

    result = PipelineResult(
        package_root=tmp_path / "package",
        validation=ValidationResult(summary={"frame_count": 5}),
        summary={"frame_count": 5},
        candidates_csv=None,
        training_draft_dir=None,
        rrd_path=None,
    )
    sentinel = {"sentinel": object()}

    monkeypatch.setattr(PipelineResult, "to_dict", lambda self: sentinel)

    assert cli._pipeline_payload(result) is sentinel
```

Run this test once before Step 8 if executing strictly TDD:

```bash
python -m pytest tests/physical_ai_data/test_cli.py::test_cli_pipeline_payload_delegates_to_result_to_dict -q
```

Expected before Step 8: FAIL if `_pipeline_payload()` still has an independent implementation that can drift from `to_dict()`.

- [ ] **Step 10: Verify focused tests pass**

Run:

```bash
python -m pytest tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_pipelines.py tests/physical_ai_data/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 11: Commit Task 1**

```bash
git add src/physical_ai_data/sdk.py src/physical_ai_data/__init__.py src/physical_ai_data/pipelines.py src/physical_ai_data/cli.py tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_pipelines.py tests/physical_ai_data/test_cli.py
git commit -m "feat: expose readiness API and pipeline payload"
```

## Task 2: SDK Environment Doctor

**Files:**
- Create: `src/physical_ai_data/environment.py`
- Modify: `src/physical_ai_data/sdk.py`
- Modify: `src/physical_ai_data/__init__.py`
- Modify: `src/physical_ai_data/cli.py`
- Create: `tests/physical_ai_data/test_environment.py`
- Modify: `tests/physical_ai_data/test_sdk.py`
- Modify: `tests/physical_ai_data/test_cli.py`

- [ ] **Step 1: Write failing environment report test**

Create `tests/physical_ai_data/test_environment.py`:

```python
from pathlib import Path

from physical_ai_data.environment import inspect_sdk_environment


def test_inspect_sdk_environment_reports_current_package_path():
    report = inspect_sdk_environment()
    payload = report.to_dict()

    assert payload["package_version"] == "0.1.0"
    assert Path(payload["package_file"]).exists()
    assert payload["package_path_exists"] is True
    assert payload["python_executable"]
    assert "optional_dependencies" in payload
    assert "rerun" in payload["optional_dependencies"]
    assert "lerobot" in payload["optional_dependencies"]
    assert payload["ok"] is True
```

Also add negative/unit tests using monkeypatch:

```python
def test_inspect_sdk_environment_errors_when_package_file_is_missing(monkeypatch):
    import physical_ai_data
    import physical_ai_data.environment as environment

    monkeypatch.setattr(physical_ai_data, "__file__", "/tmp/b06_missing_sdk/__init__.py")

    report = environment.inspect_sdk_environment()

    assert report.ok is False
    assert report.to_dict()["errors"]


def test_inspect_sdk_environment_warns_when_console_entrypoint_is_missing(monkeypatch):
    import physical_ai_data.environment as environment

    monkeypatch.setattr(environment.shutil, "which", lambda name: None)

    report = environment.inspect_sdk_environment()

    assert report.ok is True
    assert any("physical-ai-package" in warning for warning in report.warnings)


def test_inspect_sdk_environment_warns_when_optional_dependencies_are_missing(monkeypatch):
    import physical_ai_data.environment as environment

    real_find_spec = environment.importlib.util.find_spec

    def fake_find_spec(name):
        if name in {"rerun", "lerobot"}:
            return None
        return real_find_spec(name)

    monkeypatch.setattr(environment.importlib.util, "find_spec", fake_find_spec)

    report = environment.inspect_sdk_environment()
    payload = report.to_dict()

    assert report.ok is True
    assert payload["optional_dependencies"]["rerun"]["installed"] is False
    assert payload["optional_dependencies"]["lerobot"]["installed"] is False
    assert any("rerun" in warning for warning in report.warnings)
    assert any("lerobot" in warning for warning in report.warnings)
```

- [ ] **Step 2: Verify environment test fails**

Run:

```bash
python -m pytest tests/physical_ai_data/test_environment.py -q
```

Expected: FAIL because `physical_ai_data.environment` does not exist.

- [ ] **Step 3: Implement `environment.py`**

Create `src/physical_ai_data/environment.py` with:

- `OptionalDependencyStatus(name, installed, import_error=None)`
- `SdkEnvironmentReport(package_version, package_file, package_path_exists, python_executable, cwd, console_entrypoint, console_entrypoint_exists, optional_dependencies, warnings, errors)`
- `ok` property: `len(errors) == 0`
- `to_dict()`
- `inspect_sdk_environment()`

Failure policy:

- Error: current `physical_ai_data.__file__` is missing or does not exist. This catches stale editable installs pointing at deleted worktrees.
- Warning: `physical-ai-package` console entrypoint cannot be resolved or resolved path does not exist.
- Warning only: optional `rerun` or `lerobot` import fails.

Use `sys.executable`, `Path.cwd()`, `shutil.which("physical-ai-package")`, and `importlib.util.find_spec(...)`.

- [ ] **Step 4: Export doctor helper from SDK**

In `src/physical_ai_data/sdk.py` and `src/physical_ai_data/__init__.py`, export:

```python
from physical_ai_data.environment import SdkEnvironmentReport, inspect_sdk_environment
```

Add both names to `__all__`.

Update `tests/physical_ai_data/test_sdk.py` expected exports.

- [ ] **Step 5: Write failing CLI doctor tests**

Add to `tests/physical_ai_data/test_cli.py`:

```python
def test_cli_doctor_json_reports_environment():
    result = _run(["doctor", "--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["package_path_exists"] is True
    assert payload["python_executable"]


def test_cli_doctor_text_reports_import_path():
    result = _run(["doctor"])
    assert result.returncode == 0, result.stderr
    assert "SDK environment" in result.stdout
    assert "package_file:" in result.stdout
```

Add a unit test for non-zero doctor exit when report has errors:

```python
def test_cli_doctor_returns_nonzero_when_environment_report_has_errors(monkeypatch, capsys):
    from physical_ai_data import cli
    from physical_ai_data.environment import SdkEnvironmentReport

    report = SdkEnvironmentReport(
        package_version="0.1.0",
        package_file="/tmp/missing/__init__.py",
        package_path_exists=False,
        python_executable="/usr/bin/python",
        cwd="/tmp",
        console_entrypoint=None,
        console_entrypoint_exists=False,
        optional_dependencies=[],
        warnings=[],
        errors=["package path does not exist"],
    )

    monkeypatch.setattr(cli, "inspect_sdk_environment", lambda: report)

    result = cli.main(["doctor", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert result == 1
    assert payload["ok"] is False
    assert payload["errors"]
```

- [ ] **Step 6: Verify CLI doctor tests fail**

Run:

```bash
python -m pytest tests/physical_ai_data/test_cli.py::test_cli_doctor_json_reports_environment tests/physical_ai_data/test_cli.py::test_cli_doctor_text_reports_import_path -q
```

Expected: FAIL because `doctor` command does not exist.

- [ ] **Step 7: Implement CLI `doctor` command**

In `src/physical_ai_data/cli.py`:

- Import `inspect_sdk_environment`.
- Add subparser:

```python
doctor = subcommands.add_parser("doctor", help="Inspect the installed SDK environment.")
doctor.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
doctor.set_defaults(func=_doctor)
```

- Add `_doctor(args)`:

```python
def _doctor(args: argparse.Namespace) -> int:
    report = inspect_sdk_environment()
    if args.json:
        _print_json(report.to_dict())
    else:
        _print_environment_text(report)
    return 0 if report.ok else 1
```

- Add `_print_environment_text(report)`.

- [ ] **Step 8: Verify doctor tests pass**

Run:

```bash
python -m pytest tests/physical_ai_data/test_environment.py tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit Task 2**

```bash
git add src/physical_ai_data/environment.py src/physical_ai_data/sdk.py src/physical_ai_data/__init__.py src/physical_ai_data/cli.py tests/physical_ai_data/test_environment.py tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_cli.py
git commit -m "feat: add SDK environment doctor"
```

## Task 3: Candidate Real/De-Identified Data Onboarding Example

**Files:**
- Create: `examples/sdk_real_data_onboarding.py`
- Modify: `tests/physical_ai_data/test_examples.py`

- [ ] **Step 1: Write failing happy-path example test**

In `tests/physical_ai_data/test_examples.py`, add a test that:

1. Generates a Stage 8 fixture.
2. Runs `examples/sdk_real_data_onboarding.py` with `--clean-root`, `--raw-root`, `--output-root`, `--training-split eval`, and `--output-rrd`.
3. Asserts exit 0.
4. Parses JSON stdout and asserts:

```python
payload["readiness"]["overall_status"] == "review_required"
payload["pipeline"]["validation"]["ok"] is True
payload["pipeline"]["summary"]["frame_count"] == 5
Path(payload["pipeline"]["package_root"]).is_dir()
Path(payload["pipeline"]["candidates_csv"]).is_file()
Path(payload["pipeline"]["training_draft_dir"]).is_dir()
Path(payload["pipeline"]["rrd_path"]).is_file()
payload["next_steps"]
```

- [ ] **Step 2: Verify happy-path test fails**

Run:

```bash
python -m pytest tests/physical_ai_data/test_examples.py::test_sdk_real_data_onboarding_example_runs_stage8_candidate -q
```

Expected: FAIL because the example does not exist.

- [ ] **Step 3: Write failing blocked-path example test**

Add a test that removes `process.csv` from the generated Clean Zone, runs the example, and asserts:

```python
assert result.returncode == 2
payload = json.loads(result.stdout)
assert payload["readiness"]["overall_status"] == "blocked"
assert payload["pipeline"] is None
assert not (output_root / "package").exists()
```

- [ ] **Step 4: Verify blocked-path test fails for the right behavior**

Run:

```bash
python -m pytest tests/physical_ai_data/test_examples.py::test_sdk_real_data_onboarding_example_blocks_invalid_clean_zone -q
```

Expected: FAIL because the example has not implemented blocked exit `2` and pipeline suppression yet. If the failure is only “file missing,” create a minimal temporary script skeleton with argument parsing and rerun until the blocked behavior itself is the missing feature, then remove the skeleton before implementing for real.

- [ ] **Step 5: Implement `examples/sdk_real_data_onboarding.py`**

Script behavior:

- Add repo `src/` to `sys.path`, matching existing examples.
- Arguments:
  - `--clean-root` required `Path`
  - `--raw-root` optional `Path`
  - `--output-root` required `Path`
  - `--training-split` default `eval`
  - `--output-rrd` optional `Path`
  - `--no-copy-images`
- Call `assess_h300_sample_readiness`.
- If `overall_status == "blocked"`, print JSON:

```python
{
    "readiness": report.to_dict(),
    "pipeline": None,
    "next_steps": [...]
}
```

and return `2`.

- Otherwise call `run_weld_workcell_pipeline(...)` with `output_dir=output_root / "package"`, `copy_images=not args.no_copy_images`, `training_split=args.training_split`, and `output_rrd=args.output_rrd`.
- Print JSON with `readiness`, `pipeline=result.to_dict()`, and concise `next_steps`.

The success payload must expose the full output index: existing `package_root`, `candidates_csv`, `training_draft_dir`, and `rrd_path`.

- [ ] **Step 6: Verify example tests pass**

Run:

```bash
python -m pytest tests/physical_ai_data/test_examples.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit Task 3**

```bash
git add examples/sdk_real_data_onboarding.py tests/physical_ai_data/test_examples.py
git commit -m "feat: add candidate H300 onboarding example"
```

## Task 4: Onboarding Documentation And Project Status

**Files:**
- Create: `docs/sdk/real_data_onboarding.md`
- Modify: `docs/sdk/README.md`
- Modify: `docs/sdk/adoption_checklist.md`
- Modify: `README.md`
- Modify: `details.md`

- [ ] **Step 1: Create real-data onboarding guide**

Create `docs/sdk/real_data_onboarding.md` with sections:

- 定位：候选真实/脱敏 Clean Zone 模板，不代表仓库已有真实样本。
- 1. 环境检查：`physical-ai-package doctor --json` and how to interpret stale editable path warnings/errors.
- 2. 输入准备：`job.json`、`frames.csv`、`process.csv`、`events.csv`、可选 `review_labels.csv`、可选 Raw root。
- 3. Readiness：SDK and CLI command.
- 4. Pipeline smoke：CLI and `examples/sdk_real_data_onboarding.py`.
- 5. 输出索引：package manifest, validation, summary, candidates, training draft, `.rrd`.
- 6. 失败分流：environment, Clean Zone contract, Raw evidence, de-identification/permission, Stage 8 gap register.
- 边界：不做 connector/DB/UI/schema/H300 protocol/Stage 12 sample replacement.

- [ ] **Step 2: Update SDK README**

In `docs/sdk/README.md`:

- Add `assess_h300_sample_readiness` and `inspect_sdk_environment` to public API table.
- Add `PipelineResult.to_dict()` to returned object section.
- Add `physical-ai-package doctor --json` to CLI mapping.
- Add `examples/sdk_real_data_onboarding.py` and `docs/sdk/real_data_onboarding.md` to Examples.
- Keep Stage 8 synthetic baseline wording intact.

- [ ] **Step 3: Update adoption checklist**

In `docs/sdk/adoption_checklist.md`:

- Add an environment check section before synthetic demo.
- Add a candidate real/de-identified Clean Zone replacement section pointing to `docs/sdk/real_data_onboarding.md`.
- State that `readiness overall_status=blocked` means fix Clean Zone before pipeline smoke.

- [ ] **Step 4: Update README**

In `README.md`:

- In “如何使用本项目” and Stage 10 adoption path, insert `doctor` and real-data onboarding guide.
- In current capabilities, mention Stage 11.1 SDK onboarding hardening.
- Preserve clear boundary that no real data pilot, connector, DB, UI, H300 protocol, or schema change has been completed.

- [ ] **Step 5: Update details**

In `details.md`, add `2026-06-25` Stage 11.1 entry with:

- Scope and decision.
- Files added/modified.
- Do not write placeholder verification text. If final verification has not run yet, omit the verification subsection and add it only in Task 5 Step 8.
- Next plan remains Stage 12 only after at least one de-identified H300 minimum job-window sample is available.

- [ ] **Step 6: Run documentation scans**

Run:

```bash
rg -n "Stage 11.1|real-data onboarding|candidate real/de-identified|doctor|sdk_real_data_onboarding|assess_h300_sample_readiness|PipelineResult.to_dict" README.md details.md docs/sdk docs/superpowers/specs/2026-06-25-stage-11-1-sdk-real-data-onboarding-hardening-design.md
```

Expected: exit 0 with relevant hits.

Run:

```bash
rg -n "真实 H300 样本已|real data pilot 已完成|real data pilot completed|生产 connector 已完成|production connector completed|H300 现场协议已确定|DB schema 已完成|DB schema completed|demo UI 已实现" README.md details.md docs/sdk
```

Expected: exit 1 with no matches.

Run:

```bash
rg -n "TBD|to be filled|待补|placeholder" README.md details.md docs/sdk
```

Expected: exit 1 with no matches.

- [ ] **Step 7: Commit Task 4**

```bash
git add docs/sdk/real_data_onboarding.md docs/sdk/README.md docs/sdk/adoption_checklist.md README.md details.md
git commit -m "docs: add SDK real-data onboarding guide"
```

## Task 5: Final Verification And Review

**Files:**
- No planned source edits unless verification reveals a defect.

- [ ] **Step 1: Run focused verification**

```bash
python -m pytest tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_environment.py tests/physical_ai_data/test_pipelines.py tests/physical_ai_data/test_cli.py tests/physical_ai_data/test_examples.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 3: Run manual doctor smoke**

```bash
physical-ai-package doctor --json
```

Expected: exit 0, JSON `ok: true`, package file exists, Python executable present.

- [ ] **Step 4: Run manual onboarding smoke**

```bash
python scripts/generate_stage8_h300_synthetic_demo.py --output-root /tmp/stage11_1_h300_candidate --frames 5
python examples/sdk_real_data_onboarding.py \
  --clean-root /tmp/stage11_1_h300_candidate/clean/weld_workcell \
  --raw-root /tmp/stage11_1_h300_candidate/raw \
  --output-root /tmp/stage11_1_h300_candidate_onboarding \
  --training-split eval \
  --output-rrd /tmp/stage11_1_h300_candidate_onboarding/package.rrd
```

Expected: exit 0, JSON readiness `overall_status: review_required`, pipeline validation `ok: true`, and the JSON output index includes existing `package_root`, `candidates_csv`, `training_draft_dir`, and `rrd_path`.

- [ ] **Step 5: Re-run documentation scans**

Use the two `rg` commands from Task 4 Step 6.
Also run the placeholder scan from Task 4 Step 6.

- [ ] **Step 6: Request code review**

Dispatch a reviewer with:

- Spec path.
- Plan path.
- Changed files.
- Verification output.
- Explicit risk focus: public SDK imports, doctor failure policy, onboarding example exit codes, no Stage 12/connector/DB/UI/schema overreach.

- [ ] **Step 7: Fix review findings if any**

If review finds issues, apply targeted fixes, re-run affected focused tests and review again.

- [ ] **Step 8: Update final verification lines in `details.md` if needed**

Patch `details.md` with final verification counts, smoke outputs, and review result after all commands have actually run. Do not leave placeholder text such as `TBD`, `to be filled`, `待补`, or `placeholder`. Run docs scans again and commit:

```bash
git add details.md
git commit -m "docs: record Stage 11.1 final verification"
```

- [ ] **Step 9: Push branch and create PR**

```bash
git status --short --branch
git push -u origin codex/sdk-real-data-onboarding-hardening
gh pr create --base main --head codex/sdk-real-data-onboarding-hardening --title "Stage 11.1 SDK real-data onboarding hardening" --body-file <prepared-body>
```

Expected: PR created. This is a human-visible finalization step, not a substitute for the verification and review gates above.

- [ ] **Step 10: Merge remote PR and clean local branch**

After PR is merged remotely:

```bash
git -C "<repo-root>" pull --ff-only origin main
git -C "<repo-root>" worktree remove .worktrees/sdk-real-data-onboarding-hardening
git -C "<repo-root>" branch -d codex/sdk-real-data-onboarding-hardening
git -C "<repo-root>" push origin --delete codex/sdk-real-data-onboarding-hardening
```

Expected: root `main` clean and synced, feature worktree/local branch/remote branch removed.
