# Stage 8 H300 Synthetic Demo Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Stage 8 A01 H300 synthetic demo readiness: an independent H300-oriented synthetic fixture, lightweight capability visualization docs, a synthetic-to-real gap register, an A02 evidence handoff example, and updated project route docs.

**Architecture:** Add an independent Stage 8 fixture generator that reuses Stage 7.1 semantics without changing Stage 7 default output. Keep Clean Zone aligned to the existing `WeldWorkcellPackageImporter`; put H300-only fields in Raw source artifacts and docs. Use Markdown/Mermaid docs instead of a Web app.

**Tech Stack:** Python standard library, existing `physical_ai_data` package, pytest, Markdown docs.

---

## File Structure

- Create `src/physical_ai_data/stage8_h300_demo.py`: Stage 8 fixture generator, independent marker/allowlist, H300 source artifacts, and helper functions.
- Create `scripts/generate_stage8_h300_synthetic_demo.py`: CLI wrapper for the Stage 8 generator.
- Create `tests/physical_ai_data/test_stage8_h300_demo.py`: TDD coverage for generated artifacts, overwrite safety, script smoke, and importer chain.
- Create `docs/stage8/README.md`: Stage 8 overview, commands, outputs, and boundaries.
- Create `docs/stage8/capability_visualization_report.md`: Raw/Clean/Package/Rerun/candidates/A02 handoff visualization.
- Create `docs/stage8/h300_synthetic_to_real_gap_register.md`: actionable gap register.
- Create `docs/stage8/a02_evidence_demo_example.md`: synthetic A02 evidence handoff example.
- Modify `README.md`: Stage 8 positioning, quick start, route, outputs, docs index.
- Modify `details.md`: Stage 8 decisions, outputs, verification, next plan.
- Modify `docs/stage7/README.md`: add transition note from Stage 7.1 to Stage 8 and move real sample replacement to the next stage.

## Task 1: Stage 8 H300 Synthetic Fixture

**Files:**
- Create: `src/physical_ai_data/stage8_h300_demo.py`
- Create: `scripts/generate_stage8_h300_synthetic_demo.py`
- Create: `tests/physical_ai_data/test_stage8_h300_demo.py`

- [x] **Step 1: Write failing tests for Stage 8 fixture artifacts, safety, script smoke, and importer chain**

Add tests that call `generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")` and assert:

```python
raw_files = [
    "manifest.raw.json",
    "files/h300_job_window_story.json",
    "files/pcl_seam_candidates.json",
    "files/model_outputs.json",
    "files/manual_corrections.json",
    "files/quality_result.json",
    "files/point_clouds/window_0000.pcd",
]
for relative_path in raw_files:
    assert (result.raw_root / relative_path).is_file()

manifest = json.loads((result.raw_root / "manifest.raw.json").read_text(encoding="utf-8"))
assert manifest["stage"] == "stage8"
assert manifest["data_origin"] == "synthetic"
assert manifest["real_replacement_required"] is True
assert "point_cloud" in manifest["source_artifact_only_fields"]
assert "frames.csv" in manifest["importer_supported_fields"]
assert (result.raw_root / ".stage8_h300_synthetic_demo_generated").is_file()
assert (result.clean_root / ".stage8_h300_synthetic_demo_generated").is_file()
```

Also assert Clean Zone still contains only the existing `weld_workcell` contract files plus the Stage 8 marker:

```python
expected_clean_files = {
    ".stage8_h300_synthetic_demo_generated",
    "job.json",
    "frames.csv",
    "process.csv",
    "events.csv",
    "review_labels.csv",
    "images/front_0000.png",
}
actual_clean_files = {entry.relative_to(result.clean_root).as_posix() for entry in result.clean_root.rglob("*") if entry.is_file()}
assert actual_clean_files == expected_clean_files
for relative_path in expected_clean_files:
    assert (result.clean_root / relative_path).is_file()
```

Add safety tests before implementation:

```python
def test_generate_stage8_h300_demo_refuses_unknown_existing_raw_dir(tmp_path: Path):
    fixture_root = tmp_path / "stage8_demo"
    sentinel = fixture_root / "raw" / "keep.txt"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("real raw data\n", encoding="utf-8")

    with pytest.raises(ValueError, match="refusing to overwrite non-stage8 fixture directory"):
        generate_stage8_h300_synthetic_demo(fixture_root)

    assert sentinel.read_text(encoding="utf-8") == "real raw data\n"


def test_generate_stage8_h300_demo_refuses_unknown_files_added_to_generated_roots(tmp_path: Path):
    fixture_root = tmp_path / "stage8_demo"
    result = generate_stage8_h300_synthetic_demo(fixture_root)
    raw_sentinel = result.raw_root / "files" / "user_keep.txt"
    clean_sentinel = result.clean_root / "images" / "user_keep.png"
    raw_sentinel.write_text("user raw data\n", encoding="utf-8")
    clean_sentinel.write_bytes(b"user clean data\n")

    with pytest.raises(ValueError, match="refusing to overwrite non-stage8 fixture directory"):
        generate_stage8_h300_synthetic_demo(fixture_root)
```

Add overwrite and Stage 7 regression tests:

```python
def test_generate_stage8_h300_demo_can_overwrite_own_generated_roots(tmp_path: Path):
    fixture_root = tmp_path / "stage8_demo"
    generate_stage8_h300_synthetic_demo(fixture_root, frame_count=5)

    result = generate_stage8_h300_synthetic_demo(fixture_root, frame_count=4)

    manifest = json.loads((result.raw_root / "manifest.raw.json").read_text(encoding="utf-8"))
    assert manifest["window"]["frame_count"] == 4


def test_stage8_does_not_change_stage7_marker(tmp_path: Path):
    stage7_result = generate_stage7_sim_weld_window(tmp_path / "stage7_window")
    stage8_result = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")

    assert (stage7_result.raw_root / ".stage7_sim_window_generated").is_file()
    assert not (stage7_result.raw_root / ".stage8_h300_synthetic_demo_generated").exists()
    assert (stage8_result.raw_root / ".stage8_h300_synthetic_demo_generated").is_file()
```

Add script smoke test before script implementation:

```python
def test_generate_stage8_h300_synthetic_demo_script_smoke(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    output_root = tmp_path / "script_demo"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_stage8_h300_synthetic_demo.py",
            "--output-root",
            str(output_root),
            "--frames",
            "5",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "Generated Stage 8 H300 synthetic demo" in result.stdout
    assert (output_root / "raw" / "files" / "h300_job_window_story.json").is_file()
```

Add importer-chain acceptance test before implementation:

```python
def test_stage8_h300_demo_runs_weld_workcell_importer_chain(tmp_path: Path):
    result = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    package_root = tmp_path / "package"

    import_result = run_import(
        WeldWorkcellPackageImporter(),
        ImportRequest(
            source_format="weld_workcell",
            source={"root": result.clean_root},
            output_dir=package_root,
            options={"copy_images": True},
        ),
    )

    validation = validate_package(package_root)
    candidates = export_candidates(package_root)
    draft = export_training_eval_draft(package_root, split="eval")
    rrd = write_rrd(package_root, tmp_path / "stage8_demo.rrd")

    assert validation.ok, validation.errors
    assert import_result.frame_count == 5
    assert candidates.is_file()
    assert (draft / "training_eval_manifest.json").is_file()
    assert rrd.is_file()
```

- [x] **Step 2: Run tests to verify RED**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage8_h300_demo.py -q
```

Expected: FAIL because `physical_ai_data.stage8_h300_demo` and script do not exist.

- [x] **Step 3: Implement minimal Stage 8 generator**

Create `src/physical_ai_data/stage8_h300_demo.py` with:

- `Stage8H300SyntheticDemoResult(root, raw_root, clean_root)`.
- `generate_stage8_h300_synthetic_demo(output_root: str | Path, frame_count: int = 5)`.
- Independent marker `.stage8_h300_synthetic_demo_generated`.
- Independent Raw/Clean allowlists.
- Stage 8 constants such as `TASK_ID = "synthetic_h300_task_001"`, `WORK_ORDER_ID = "SYN-H300-WO-001"`, `JOB_WINDOW_ID = "synthetic_h300_window_001"`.
- Raw artifacts listed in the spec.
- Clean Zone files matching existing `WeldWorkcellPackageImporter` columns.

The implementation may copy small helper patterns from `stage7_sim_window.py`, but must not modify Stage 7 default output.

- [x] **Step 4: Implement script wrapper**

Create `scripts/generate_stage8_h300_synthetic_demo.py`:

```python
#!/usr/bin/env python3
"""Generate a deterministic Stage 8 H300 synthetic demo fixture."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic Stage 8 H300 synthetic demo fixture.")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=5)
    args = parser.parse_args(argv)
    result = generate_stage8_h300_synthetic_demo(args.output_root, frame_count=args.frames)
    print("Generated Stage 8 H300 synthetic demo")
    print(f"Root: {result.root}")
    print(f"Raw: {result.raw_root}")
    print(f"Clean: {result.clean_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 5: Run tests to verify GREEN**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage8_h300_demo.py -q
```

Expected: PASS.

- [x] **Step 6: Run Stage 7 regression tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage7_sim_window.py tests/physical_ai_data/test_stage8_h300_demo.py -q
```

Expected: PASS.

- [x] **Step 7: Commit Task 1**

```bash
git add src/physical_ai_data/stage8_h300_demo.py scripts/generate_stage8_h300_synthetic_demo.py tests/physical_ai_data/test_stage8_h300_demo.py
git commit -m "feat: add Stage 8 H300 synthetic demo fixture"
```

## Task 2: Stage 8 Capability Docs

**Files:**
- Create: `docs/stage8/README.md`
- Create: `docs/stage8/capability_visualization_report.md`
- Create: `docs/stage8/h300_synthetic_to_real_gap_register.md`
- Create: `docs/stage8/a02_evidence_demo_example.md`

- [x] **Step 1: Create Stage 8 README**

Document:

- Stage 8 positioning: A01 H300 synthetic demo readiness, not real data pilot.
- Default generation command:

```bash
python scripts/generate_stage8_h300_synthetic_demo.py --output-root artifacts/stage8/h300_synthetic_demo --frames 5
```

- Minimal Clean Zone -> Package Python example:

```bash
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter

run_import(
    WeldWorkcellPackageImporter(),
    ImportRequest(
        source_format="weld_workcell",
        source={"root": Path("artifacts/stage8/h300_synthetic_demo/clean/weld_workcell")},
        output_dir=Path("artifacts/stage8/h300_synthetic_demo/package"),
        options={"copy_images": True},
    ),
)
PY
```

- Follow-on commands:

```bash
python scripts/physical_ai_package.py validate artifacts/stage8/h300_synthetic_demo/package --json
python scripts/physical_ai_package.py summarize artifacts/stage8/h300_synthetic_demo/package --json
python scripts/physical_ai_package.py export-candidates artifacts/stage8/h300_synthetic_demo/package
python scripts/physical_ai_package.py export-training-draft artifacts/stage8/h300_synthetic_demo/package --split eval
python scripts/physical_ai_package.py convert-rerun artifacts/stage8/h300_synthetic_demo/package --output-rrd artifacts/stage8/h300_synthetic_demo/package.rrd
```

- Boundaries: synthetic only, not production connector, no DB/schema/package schema changes.

- [x] **Step 2: Create visualization report**

Include:

- Mermaid data-link diagram.
- H300 synthetic timeline table.
- Field landing table: Raw artifact, Clean contract, Package output, A02 handoff category.
- Raw/Clean/Package file tree.
- Status board: current capability / needs real data / explicitly not doing.

- [x] **Step 3: Create gap register**

Use a Markdown table with columns:

```text
Gap ID | Field/sample group | Stage 8 status | Current landing | Needed real/de-identified sample | Expansion trigger | Default next step
```

Cover at least: job/task ids, robot state timing, point cloud/PCL, camera calibration, model outputs, manual corrections, process params, events/alarms, quality result, AI controller storage/permissions.

- [x] **Step 4: Create A02 evidence handoff example**

Include `synthetic_demo_only: true`, and sections/tables for:

- evidence,
- context,
- attachment_reference,
- blocked.

Avoid defining an A02 schema or automatic converter.

- [x] **Step 5: Run documentation scans**

Run:

```bash
rg -n "Stage 8|synthetic|gap register|A02 evidence handoff|Raw Zone|Clean Zone" docs/stage8
```

Expected: exit 0 with hits in all Stage 8 docs.

Run the Task 2 false-claim scan against `docs/stage8`.

Expected: exit 1, no hits. Do not write the full sensitive phrase list into this plan, because the final recursive `rg` scan includes plan files and would otherwise match the checklist text itself.

- [x] **Step 6: Commit Task 2**

```bash
git add docs/stage8
git commit -m "docs: add Stage 8 capability and readiness package"
```

## Task 3: Project Entry Docs and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `docs/stage7/README.md`
- Modify: `docs/superpowers/plans/2026-06-22-stage-8-h300-synthetic-demo-readiness.md`

- [x] **Step 1: Update README**

Update project-level entry points:

- Current first sample becomes Stage 8 A01 H300 synthetic demo readiness.
- Current capabilities include Stage 8 H300 synthetic demo fixture and readiness docs.
- Engineering handoff points to `docs/stage8/README.md` and keeps Stage 7.1 as historical baseline.
- Quick start adds Stage 8 command.
- Route adds Stage 8 and shifts real/de-identified sample replacement to Stage 9 or post-Stage 8 review.
- Docs index adds Stage 8 spec, plan, and docs.

- [x] **Step 2: Update details**

Add a 2026-06-22 Stage 8 section recording:

- decision not to call it real data pilot,
- new fixture, docs, gap register, A02 evidence example,
- no connector/DB/schema/package schema changes,
- verification commands and results after they are run.

Update next-step plan to real/de-identified H300 sample replacement and gap register closure.

- [x] **Step 3: Update Stage 7 README transition**

Add or revise “下一步” to say:

- Stage 7.1 remains baseline for A01 H300 Clean Zone contract and default historical fixture.
- Stage 8 is the second synthetic H300-oriented demo/readiness package while real samples are unavailable.
- Real/de-identified sample replacement is the next stage after Stage 8.

- [x] **Step 4: Run full Stage 8 chain smoke**

Run:

```bash
rm -rf /tmp/stage8_h300_demo /tmp/stage8_h300_package /tmp/stage8_h300_package.rrd
python scripts/generate_stage8_h300_synthetic_demo.py --output-root /tmp/stage8_h300_demo --frames 5
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter

run_import(
    WeldWorkcellPackageImporter(),
    ImportRequest(
        source_format="weld_workcell",
        source={"root": Path("/tmp/stage8_h300_demo/clean/weld_workcell")},
        output_dir=Path("/tmp/stage8_h300_package"),
        options={"copy_images": True},
    ),
)
PY
python scripts/physical_ai_package.py validate /tmp/stage8_h300_package --json
python scripts/physical_ai_package.py summarize /tmp/stage8_h300_package --json
python scripts/physical_ai_package.py export-candidates /tmp/stage8_h300_package
python scripts/physical_ai_package.py export-training-draft /tmp/stage8_h300_package --split eval
python scripts/physical_ai_package.py convert-rerun /tmp/stage8_h300_package --output-rrd /tmp/stage8_h300_package.rrd
```

Expected: every command exits 0; package validates with `ok: true`; candidates, training draft, and `.rrd` are created.

Result:

- `rm -rf /tmp/stage8_h300_demo /tmp/stage8_h300_package /tmp/stage8_h300_package.rrd`: exit 0.
- `python scripts/generate_stage8_h300_synthetic_demo.py --output-root /tmp/stage8_h300_demo --frames 5`: exit 0.
- `PYTHONPATH=src python - <<'PY' ... run_import(...) ... PY`: exit 0.
- `python scripts/physical_ai_package.py validate /tmp/stage8_h300_package --json`: exit 0 with `ok: true`, `frame_count: 5`, `event_count: 2`, `label_count: 1`, `metric_count: 30`, `artifact_ref_count: 7`.
- `python scripts/physical_ai_package.py summarize /tmp/stage8_h300_package --json`: exit 0.
- `python scripts/physical_ai_package.py export-candidates /tmp/stage8_h300_package`: exit 0; wrote `/tmp/stage8_h300_package/derived/candidates.csv`.
- `python scripts/physical_ai_package.py export-training-draft /tmp/stage8_h300_package --split eval`: exit 0; wrote `/tmp/stage8_h300_package/derived/training_eval`.
- `python scripts/physical_ai_package.py convert-rerun /tmp/stage8_h300_package --output-rrd /tmp/stage8_h300_package.rrd`: exit 0; wrote `/tmp/stage8_h300_package.rrd`.

- [x] **Step 5: Run targeted and full tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage8_h300_demo.py -q
python -m pytest -q
```

Expected: targeted tests pass; full suite passes.

Result:

- `python -m pytest tests/physical_ai_data/test_stage8_h300_demo.py -q`: `7 passed in 0.62s`.
- `python -m pytest -q`: `187 passed in 3.00s`.

- [x] **Step 6: Run final keyword and false-claim scans**

Run:

```bash
rg -n "Stage 8|H300 synthetic|synthetic-to-real|gap register|A02 evidence handoff|generate_stage8_h300_synthetic_demo" README.md details.md docs/stage7 docs/stage8 docs/superpowers/specs/2026-06-22-stage-8-h300-synthetic-demo-readiness-design.md docs/superpowers/plans/2026-06-22-stage-8-h300-synthetic-demo-readiness.md
```

Expected: exit 0 with hits across README, details, Stage 8 docs, spec, and plan.

Run the Stage 8 false-claim scan against the same Stage 8 scope. The forbidden phrase list comes from this task's acceptance criteria and should stay outside this plan body to avoid self-matching.

Expected: exit 1, no hits.

Result:

- Initial full historical recursive false-claim scan hit an old scan command in the Stage 7.1 plan, not a Stage 8 real-data claim.
- Stage 8 scoped keyword scan: exit 0 with hits across README, details, Stage 7/8 docs, Stage 8 spec, and Stage 8 plan.
- Stage 8 scoped false-claim scan: exit 1, no hits.

- [x] **Step 7: Commit Task 3**

```bash
git add README.md details.md docs/stage7/README.md docs/superpowers/plans/2026-06-22-stage-8-h300-synthetic-demo-readiness.md
git commit -m "docs: update project route for Stage 8 readiness"
```
