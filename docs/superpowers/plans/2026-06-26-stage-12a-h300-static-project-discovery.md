# Stage 12A H300 Static Project Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a redacted-safe H300 static engineering project inspector so B06 can learn from the first real static project package without committing raw data or prematurely building Clean Zone conversion/realtime connectors.

**Architecture:** Implement a focused `physical_ai_data.h300_static_project` module that reads local project files, returns structured redacted summaries, and exposes a top-level SDK function plus a CLI JSON command. Keep Markdown/report generation in docs, not SDK, and keep the real `data/H300` sample local-only.

**Tech Stack:** Python standard library, Pillow for image metadata, existing argparse CLI, pytest, Markdown docs.

---

## File Map

- Modify `.gitignore`: ignore `data/` so local real/static H300 samples cannot be accidentally committed.
- Create `src/physical_ai_data/h300_static_project.py`: dataclasses, redaction helpers, file/media parsers, sensitivity findings, gap mapping, `inspect_h300_static_project(...)`.
- Modify `src/physical_ai_data/sdk.py`: import/export `H300StaticProjectReport` and `inspect_h300_static_project`.
- Modify `src/physical_ai_data/__init__.py`: top-level export.
- Modify `src/physical_ai_data/cli.py`: add `inspect-h300-static PROJECT_ROOT --json` and concise text mode.
- Create `tests/physical_ai_data/test_h300_static_project.py`: synthetic static project fixture and inspector tests.
- Modify `tests/physical_ai_data/test_sdk.py`: top-level SDK export and import-weight tests.
- Modify `tests/physical_ai_data/test_cli.py`: CLI JSON and error behavior tests.
- Create `docs/stage12a/README.md`: user-facing Stage 12A guide.
- Create `docs/stage12a/h300_static_project_structure_summary.md`: committed redacted structure summary from the local real sample.
- Modify `README.md`: route update from waiting for full real-time data to static-project-first discovery.
- Modify `details.md`: record Stage 12A implementation, verification, and next stage.
- Modify `docs/sdk/README.md`: add Stage 12A SDK/CLI entry to API and examples docs.
- Optional create `examples/sdk_h300_static_project_inspect.py` only if it adds value beyond CLI; keep it tiny if included.

## Redaction Rules

- `to_dict()` and CLI JSON must be safe to save as review attachments.
- Do not output absolute paths.
- Do not output raw local root names, raw project basenames, basename fragments, exact embedded timestamps, short program IDs such as `22222`, IPs, server/port values, operator/author/reviewer values, raw Lua code, raw JSON payloads, raw point coordinates, image content, or binary PCD content.
- Output path patterns such as `campcd_json/project_<redacted>.json`, roles, extensions, counts, sizes, image dimensions, point cloud header metadata, command counts, and risk finding categories.
- Sensitivity findings may include `finding_type`, `path_pattern`, `field`, `severity`, and `message`, but not the sensitive value itself.

## Task 1: Route Protection And Stage 12A Docs

**Files:**
- Modify: `.gitignore`
- Modify: `README.md`
- Modify: `details.md`
- Create: `docs/stage12a/README.md`
- Create: `docs/stage12a/h300_static_project_structure_summary.md`

- [ ] **Step 1: Add failing docs/protection checks**

Add or update tests only if the repo already has docs tests for `.gitignore`; otherwise use shell verification in this task. Required checks:

```bash
git check-ignore -q data/example.txt
rg -q "Stage 12A|static engineering project|静态工程包|inspect-h300-static" README.md details.md docs/stage12a
rg -n "<real-server-token>|<real-port-token>|<real-run-basename>|<real-project-basename>|<real-recipe-basename>|<real-operator-token>|<real-ip-token>" README.md details.md docs/stage12a docs/superpowers/specs/2026-06-26-stage-12a-h300-static-project-discovery-design.md
```

Expected before implementation: first command fails because `data/` is not ignored; positive docs scan fails because docs do not exist; negative scan should already have no matches after spec redaction.

- [ ] **Step 2: Update `.gitignore`**

Add:

```gitignore
# Local real/de-identified data samples
data/
```

Do not remove existing ignore rules.

- [ ] **Step 3: Update README route**

In `README.md`, revise the current Stage 12 wording:

- Keep B06 SDK-first positioning.
- State that a static H300 engineering project sample is now available locally for controlled analysis.
- State that realtime API is still pending.
- Make Stage 12A the next concrete step: static engineering project discovery and SDK onboarding.
- Keep boundaries: no production connector, DB/schema, realtime API, demo UI, or Clean Zone auto-conversion in this stage.

- [ ] **Step 4: Update details**

Append a `2026-06-26` Stage 12A planning/implementation note:

- Why route changed.
- User decision: scheme B, SDK inspection only, no SDK report-format conversion.
- Raw `data/H300` remains local-only.
- Stage 12A deliverables.

Leave final verification placeholders only if they will be filled later in the final docs update task; otherwise avoid claiming tests that have not run.

- [ ] **Step 5: Create `docs/stage12a/README.md`**

Include:

- Purpose and boundary.
- What an H300 static engineering project contains.
- How to run the planned CLI:

```bash
physical-ai-package inspect-h300-static path/to/project --json
```

- How to read output sections.
- Redaction policy.
- Relationship to Stage 12B and Stage 13.
- Non-goals.

- [ ] **Step 6: Create redacted structure summary**

Create `docs/stage12a/h300_static_project_structure_summary.md` using only redacted structure facts:

- `data/H300/<local-project-run>` placeholder only.
- No raw URL/IP/port.
- No raw project basename.
- No raw operator/author values.
- Include counts and structure types allowed by the spec.
- Include gap mapping observations without sensitive values.

- [ ] **Step 7: Run docs/protection checks**

Run:

```bash
git check-ignore -q data/example.txt
rg -q "Stage 12A|static engineering project|静态工程包|inspect-h300-static" README.md details.md docs/stage12a
rg -n "<real-server-token>|<real-port-token>|<real-run-basename>|<real-project-basename>|<real-recipe-basename>|<real-operator-token>|<real-ip-token>" README.md details.md docs/stage12a docs/superpowers/specs/2026-06-26-stage-12a-h300-static-project-discovery-design.md
```

Expected: first two exit 0; negative scan exits 1 with no matches.

- [ ] **Step 8: Commit**

```bash
git add .gitignore README.md details.md docs/stage12a
git commit -m "docs: route Stage 12A static project discovery"
```

## Task 2: H300 Static Inspector Core

**Files:**
- Create: `src/physical_ai_data/h300_static_project.py`
- Create: `tests/physical_ai_data/test_h300_static_project.py`

- [ ] **Step 1: Write synthetic fixture helper in test file**

In `tests/physical_ai_data/test_h300_static_project.py`, create helper `create_h300_static_project_fixture(root: Path) -> Path`.

It must write:

```text
project/
  campcd_json/<timestamped-project>.json
  campcd_json/<timestamped-project>_campcd.json
  <timestamped-project>_image/<timestamped-project>_part_0.jpg
  <timestamped-project>_point_cloud/<timestamped-project>_part_0.pcd
  point_cloud/<timestamped-project>.txt
  weld_seam/<recipe-json>.json
  <timestamped-run>_weld_config/<program-id>_flow.json
  <timestamped-run>_lua_script/<program-id>.lua
```

Use a tiny generated JPEG via Pillow. Include intentionally sensitive values in source files:

- an operator-like author value.
- a Windows-style internal path.
- IP-like text in flow or runtime.
- timestamped basenames.

- [ ] **Step 2: Write failing inspector summary test**

Add:

```python
def test_inspect_h300_static_project_summarizes_fixture_without_raw_values(tmp_path):
    project = create_h300_static_project_fixture(tmp_path / "project")
    report = inspect_h300_static_project(project)
    payload = report.to_dict()

    assert payload["recognized"] is True
    assert payload["root_label"] == "<local-project>"
    assert payload["summary"]["image_count"] == 1
    assert payload["summary"]["point_cloud_count"] == 1
    assert payload["summary"]["weld_seam_count"] == 2
    assert payload["summary"]["path_plan_count"] == 2
    assert payload["summary"]["lua_arc_mpl_count"] == 1
    assert payload["project_info"]["has_project_name"] is True
    serialized = json.dumps(payload)
    assert "<operator-token>" not in serialized
    assert "<date-token>" not in serialized
    assert "<time-token>" not in serialized
    assert "<program-id>" not in serialized
    assert "<timestamped-project>" not in serialized
    assert str(project) not in serialized
    assert str(tmp_path) not in serialized
    assert "<internal-windows-path>" not in serialized
    assert "<ip-token>" not in serialized
```

Expected before implementation: import/function missing.

- [ ] **Step 3: Write failing media/parser tests**

Cover:

- JPEG dimensions and mode.
- PCD header fields/points/data encoding.
- text point cloud column count sampled without raw coordinates in payload.
- Lua command counts.
- weld seam type/orientation distributions.
- gap mapping includes the complete spec set: G-001, G-003, G-004, G-005, G-006, G-007, G-008, G-010, G-012.

- [ ] **Step 4: Write failing invalid input test**

```python
def test_inspect_h300_static_project_rejects_missing_directory(tmp_path):
    with pytest.raises(FileNotFoundError):
        inspect_h300_static_project(tmp_path / "missing")
```

- [ ] **Step 5: Run tests and confirm failure**

Run:

```bash
python -m pytest tests/physical_ai_data/test_h300_static_project.py -q
```

Expected: FAIL because module/function do not exist.

- [ ] **Step 6: Implement dataclasses and `to_dict()`**

Create `src/physical_ai_data/h300_static_project.py`.

Suggested public objects:

```python
@dataclass(frozen=True)
class H300StaticProjectReport:
    project_root: Path
    root_label: str
    recognized: bool
    project_info: dict[str, object]
    files: list[H300StaticFile]
    images: list[H300ImageSummary]
    point_clouds: list[H300PointCloudSummary]
    text_point_clouds: list[H300TextPointCloudSummary]
    weld_seams: H300WeldSeamSummary
    path_plans: H300PathPlanSummary
    lua_program: H300LuaProgramSummary | None
    flow_config: H300FlowConfigSummary | None
    sensitivity_findings: list[H300SensitivityFinding]
    gap_mapping: list[H300GapMapping]
    summary: dict[str, object]
```

Include `to_dict()` methods that do not expose `project_root`.

- [ ] **Step 7: Implement redaction helpers**

Implement:

- `_redact_path_pattern(path: Path) -> str`
- `_redact_basename(name: str) -> str`
- `_contains_sensitive_value(text: str) -> bool`

Rules:

- Replace 6+ digit runs with `<timestamp>` and redact known program/config IDs used in basenames, including short numeric names such as `22222`.
- Replace `project_<...>` middle portions with `project_<redacted>`.
- Do not emit Windows absolute path values.
- Do not emit POSIX absolute paths, `tmp_path`, or raw project root names.
- Do not emit author/operator/reviewer values.
- Do not emit IP addresses, server ports, or raw program/config IDs.

- [ ] **Step 8: Implement parsers**

Implement minimal robust parsing:

- JSON read with `utf-8-sig`.
- Project JSON counts: top-level keys, `info` presence booleans, `pathPlan`, `extractPathPlan`, `photoPoses`.
- campcd JSON counts: `pcdWithCam`, ROI enabled, path risk findings.
- PCD header parser: read until `DATA`, parse FIELDS/WIDTH/HEIGHT/POINTS/DATA.
- Text point cloud sampler: read up to a bounded number of lines for column count; optionally count all lines only for small files or with cap.
- Lua parser: regex count command words.
- Flow parser: count `flow` list length.
- Weld seam parser: count seams and distributions.
- Image parser: Pillow open only metadata.

- [ ] **Step 9: Implement gap mapping and summary**

Map findings to fixed gap IDs from spec. Summary must include stable counts used by tests.

- [ ] **Step 10: Run focused tests**

```bash
python -m pytest tests/physical_ai_data/test_h300_static_project.py -q
```

Expected: PASS.

- [ ] **Step 11: Commit**

```bash
git add src/physical_ai_data/h300_static_project.py tests/physical_ai_data/test_h300_static_project.py
git commit -m "feat: inspect H300 static project structure"
```

## Task 3: SDK Export And CLI Command

**Files:**
- Modify: `src/physical_ai_data/sdk.py`
- Modify: `src/physical_ai_data/__init__.py`
- Modify: `src/physical_ai_data/cli.py`
- Modify: `tests/physical_ai_data/test_sdk.py`
- Modify: `tests/physical_ai_data/test_cli.py`

- [ ] **Step 1: Write failing SDK export tests**

In `tests/physical_ai_data/test_sdk.py`:

- Import `H300StaticProjectReport` and `inspect_h300_static_project` from `physical_ai_data`.
- Add them to expected `__all__` sets.
- Extend subprocess import-weight test to keep forbidding CLI, LeRobot, and Rerun roots.

Expected before implementation: import or `__all__` failure.

- [ ] **Step 2: Write failing CLI tests**

In `tests/physical_ai_data/test_cli.py`, import the fixture helper from `test_h300_static_project` or duplicate a tiny local helper if importing test helper is undesirable.

Add:

```python
def test_cli_inspect_h300_static_json(tmp_path):
    project = create_h300_static_project_fixture(tmp_path / "project")
    result = _run(["inspect-h300-static", str(project), "--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recognized"] is True
    assert payload["summary"]["weld_seam_count"] == 2
    assert "<operator-token>" not in result.stdout
    assert "<date-token>" not in result.stdout
    assert "<time-token>" not in result.stdout
    assert "<program-id>" not in result.stdout
    assert "<timestamped-project>" not in result.stdout
    assert str(project) not in result.stdout
    assert str(tmp_path) not in result.stdout
    assert "<internal-windows-path>" not in result.stdout
    assert "<ip-token>" not in result.stdout
```

Add missing directory test:

```python
def test_cli_inspect_h300_static_missing_directory_returns_error(tmp_path):
    result = _run(["inspect-h300-static", str(tmp_path / "missing"), "--json"])
    assert result.returncode == 1
    assert "Error:" in result.stderr
    assert str(tmp_path) not in result.stdout
```

- [ ] **Step 3: Run focused tests and confirm failure**

```bash
python -m pytest tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_cli.py -q
```

- [ ] **Step 4: Export SDK function**

Modify `src/physical_ai_data/sdk.py`:

```python
from physical_ai_data.h300_static_project import H300StaticProjectReport, inspect_h300_static_project
```

Add both names to `__all__`.

Modify `src/physical_ai_data/__init__.py` similarly.

- [ ] **Step 5: Add CLI command**

Modify `src/physical_ai_data/cli.py`:

- Import `inspect_h300_static_project` from `physical_ai_data.sdk`.
- Add parser:

```python
inspect_static = subcommands.add_parser(
    "inspect-h300-static",
    help="Inspect a local H300 static engineering project.",
)
inspect_static.add_argument("project_root", type=Path)
inspect_static.add_argument("--json", action="store_true")
inspect_static.set_defaults(func=_inspect_h300_static)
```

- Handler:

```python
def _inspect_h300_static(args: argparse.Namespace) -> int:
    report = inspect_h300_static_project(args.project_root)
    payload = report.to_dict()
    if args.json:
        _print_json(payload)
    else:
        print(f"H300 static project: recognized={report.recognized}")
        print(_format_summary(report.summary))
    return 0
```

If text mode needs different summary keys, print a few explicit fields instead of reusing package `_format_summary`.

- [ ] **Step 6: Run focused tests**

```bash
python -m pytest tests/physical_ai_data/test_h300_static_project.py tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/physical_ai_data/sdk.py src/physical_ai_data/__init__.py src/physical_ai_data/cli.py tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_cli.py
git commit -m "feat: expose H300 static project inspection"
```

## Task 4: SDK Docs, Example, And Real Sample Smoke

**Files:**
- Modify: `docs/sdk/README.md`
- Create: `examples/sdk_h300_static_project_inspect.py`
- Create/modify tests if example is added: `tests/physical_ai_data/test_examples.py`
- Modify: `details.md`

- [ ] **Step 1: Decide whether example adds value**

Include the example only if it demonstrates a Python SDK usage that CLI docs do not cover. Recommended: include a tiny example because this stage is about SDK onboarding, not just CLI.

- [ ] **Step 2: Add failing example test if creating example**

In `tests/physical_ai_data/test_examples.py`, add a subprocess test that:

- Creates synthetic fixture using helper from `test_h300_static_project`.
- Runs `examples/sdk_h300_static_project_inspect.py --project-root <fixture>`.
- Parses stdout JSON.
- Asserts redacted-safe output.

- [ ] **Step 3: Create example**

`examples/sdk_h300_static_project_inspect.py` should:

- Add local `src/` to `sys.path` like existing examples.
- Accept `--project-root`.
- Call `inspect_h300_static_project`.
- Print `report.to_dict()` JSON.
- Not implement Markdown/report conversion.

- [ ] **Step 4: Update SDK docs**

In `docs/sdk/README.md`:

- Add `inspect_h300_static_project` to public API table.
- Add `physical-ai-package inspect-h300-static PROJECT --json` to CLI mapping.
- Add example link.
- Reinforce that it is redacted-safe structure inspection, not Clean Zone conversion.

- [ ] **Step 5: Run example/docs focused tests**

```bash
python -m pytest tests/physical_ai_data/test_examples.py tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_cli.py -q
```

- [ ] **Step 6: Real local sample smoke**

From an environment where local real data is accessible, run the CLI against the local-only project path without recording the path in committed docs:

```bash
python scripts/physical_ai_package.py inspect-h300-static "data/H300/<local-project-run>" --json
```

Do not commit stdout. Record only redacted facts in `details.md`, such as recognized true, image count, PCD count, seam count, Lua command counts, sensitivity finding categories.

- [ ] **Step 7: Update details final Stage 12A status**

Record:

- Implementation summary.
- Focused test results.
- Full test results if run.
- Real sample smoke redacted summary.
- Boundaries preserved.
- Next stage plan.

- [ ] **Step 8: Commit**

```bash
git add docs/sdk/README.md examples/sdk_h300_static_project_inspect.py tests/physical_ai_data/test_examples.py details.md
git commit -m "docs: add H300 static inspection SDK guidance"
```

If no example is added, omit example/test paths and use commit message:

```bash
git add docs/sdk/README.md details.md
git commit -m "docs: add H300 static inspection SDK guidance"
```

## Task 5: Final Verification And Review Prep

**Files:**
- Potentially modify: `details.md` if final test timings/counts differ.

- [ ] **Step 1: Run focused verification**

```bash
python -m pytest tests/physical_ai_data/test_h300_static_project.py tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_cli.py tests/physical_ai_data/test_examples.py -q
```

Record exact pass count and time.

- [ ] **Step 2: Run full suite**

```bash
python -m pytest -q
```

Record exact pass count and time.

- [ ] **Step 3: Run doctor smoke**

```bash
python scripts/physical_ai_package.py doctor --json
```

Expected: exit 0 and `ok: true` in this worktree.

- [ ] **Step 4: Run synthetic CLI smoke**

Use a temporary synthetic fixture generated by tests or example helper, then:

```bash
python scripts/physical_ai_package.py inspect-h300-static <tmp-synthetic-project> --json
```

Expected: exit 0, `recognized: true`, redacted output.

- [ ] **Step 5: Run local real sample smoke**

If local `data/H300/<local-project-run>` is available, run CLI against it. Expected:

- exit 0
- `recognized: true`
- counts match redacted summary
- output contains no known sensitive values, raw basenames, absolute paths, short program IDs, IPs, ports, or operator/author values

If not available inside the worktree, use the main workspace absolute path and do not commit any output.

- [ ] **Step 6: Run docs scans**

Positive scan:

```bash
rg -q "Stage 12A|static engineering project|静态工程包|inspect-h300-static|inspect_h300_static_project|redacted-safe|H300StaticProjectReport" README.md details.md docs/stage12a docs/sdk docs/superpowers/specs/2026-06-26-stage-12a-h300-static-project-discovery-design.md
```

Negative scan:

```bash
rg -n "<real-server-token>|<real-port-token>|<real-run-basename>|<real-project-basename>|<real-recipe-basename>|<real-operator-token>|<real-ip-token>|<real-internal-path-token>" README.md details.md docs/stage12a docs/sdk docs/superpowers/specs
```

Expected: positive scan exit 0; negative scan exit 1 with no matches.

- [ ] **Step 7: Update details if needed**

If verification counts/timings changed from Task 4, update `details.md` and commit:

```bash
git add details.md
git commit -m "docs: record Stage 12A final verification"
```

- [ ] **Step 8: Final code review**

Dispatch final reviewer with:

- Spec path.
- Plan path.
- Summary of commits.
- Verification output.
- Focus areas: redaction, no raw data, no Clean Zone auto-conversion, SDK import weight, CLI JSON.

Address any findings before PR.

## Final Branch Flow

After final review approval:

1. Push branch:

```bash
git push -u origin codex/stage-12a-h300-static-discovery
```

2. Create PR:

```bash
gh pr create --base main --head codex/stage-12a-h300-static-discovery --title "Stage 12A H300 static project discovery" --body "<summary and verification>"
```

3. Merge remotely after PR is clean.
4. Pull `main` in the root workspace.
5. Remove worktree and local branch.
6. Confirm `data/` remains untracked/ignored and raw data was not committed.
