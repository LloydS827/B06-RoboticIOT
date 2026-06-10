# Stage 4.2 SDK Wrapper / External Importer Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Stage 4.2 thin SDK, explicit external importer contract, LeRobot importer contract implementation, and minimum training/evaluation draft export without changing Physical AI Package v0.1 schema.

**Architecture:** Keep existing package functions as the source of truth. Add thin modules around them: `training_export.py` writes draft artifacts from validated packages and candidates, `sdk.py` exposes stable Python entry points, `importers.py` defines the `source -> Physical AI Package` contract, and `lerobot_adapter.py` provides the first importer implementation. CLI remains a parameter parsing shell over SDK/importer calls.

**Tech Stack:** Python 3.11+, dataclasses, protocols from `typing`, existing CSV/JSON helpers, pytest, existing `uv` development environment.

---

## File Structure

- Create `src/physical_ai_data/training_export.py`: minimum training/evaluation draft export logic.
- Create `src/physical_ai_data/sdk.py`: thin Python SDK wrapper around validator, summarize, candidate export, Rerun export, and training draft export.
- Create `src/physical_ai_data/importers.py`: importer dataclasses, protocol, and `run_import`.
- Modify `src/physical_ai_data/lerobot_adapter.py`: add `LeRobotPackageImporter` and helper parsing for `ImportRequest`.
- Modify `src/physical_ai_data/cli.py`: call SDK functions for existing package operations, add `export-training-draft`, and route `import-lerobot` through `LeRobotPackageImporter`.
- Modify `src/physical_ai_data/__init__.py`: export stable SDK entry points.
- Add `tests/physical_ai_data/test_training_export.py`: training draft behavior.
- Add `tests/physical_ai_data/test_sdk.py`: public SDK entry points.
- Add `tests/physical_ai_data/test_importers.py`: generic importer contract and LeRobot importer contract.
- Modify `tests/physical_ai_data/test_cli.py`: CLI training draft command.
- Modify `tests/physical_ai_data/test_lerobot_cli.py`: ensure CLI still maps LeRobot args correctly through the contract.
- Update `README.md`, `details.md`, `docs/stage4/README.md`, and `docs/research/06-lerobot开放数据样板链路记录.md`.

## Shared Commands

Use the existing worktree:

```bash
cd "/Users/lloyd/Nutstore Files/Nutstore/CavLAB/P00-Projects/分类0-核心研发/B06-Robotic IOT 与物理数据层/.worktrees/stage-4-2-sdk-importer-boundary"
. .venv/bin/activate
```

Baseline already passed in this worktree:

```bash
python -m pytest -q
# Expected: 99 passed
```

---

### Task 1: Training/Evaluation Draft Export

**Files:**
- Create: `src/physical_ai_data/training_export.py`
- Create: `tests/physical_ai_data/test_training_export.py`

- [ ] **Step 1: Write failing tests for default output and generated samples**

Create `tests/physical_ai_data/test_training_export.py`:

```python
import csv
import json
from pathlib import Path

import pytest

from physical_ai_data.samples import generate_welding_package
from physical_ai_data.training_export import TRAINING_EVAL_EXPORT_FORMAT, export_training_eval_draft


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def test_export_training_eval_draft_creates_manifest_and_samples(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=3)

    output = export_training_eval_draft(package)

    assert output == package / "derived" / "training_eval"
    manifest = json.loads((output / "training_eval_manifest.json").read_text(encoding="utf-8"))
    rows = _rows(output / "samples.csv")
    assert manifest["export_format"] == TRAINING_EVAL_EXPORT_FORMAT
    assert manifest["source_package_root"] == str(package)
    assert manifest["samples_csv"] == "samples.csv"
    assert manifest["candidate_count"] == len(rows)
    assert rows
    assert rows[0]["sample_id"] == "sample_0000"
    assert rows[0]["split"] == "unspecified"
    assert rows[0]["label_status"] == "unlabeled"
    assert rows[0]["package_root"] == str(package)
    assert (package / "derived" / "candidates.csv").exists()
```

- [ ] **Step 2: Write failing tests for custom output, split preservation, and invalid package**

Append:

```python
def test_export_training_eval_draft_preserves_custom_split_and_output(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=12, random_seed=4)
    output_dir = tmp_path / "exports" / "train_eval"

    output = export_training_eval_draft(package, output_dir=output_dir, split="holdout")

    assert output == output_dir
    rows = _rows(output / "samples.csv")
    assert rows
    assert {row["split"] for row in rows} == {"holdout"}


def test_export_training_eval_draft_rejects_invalid_package(tmp_path: Path):
    with pytest.raises(ValueError, match="missing_manifest"):
        export_training_eval_draft(tmp_path)
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/physical_ai_data/test_training_export.py -q
```

Expected: FAIL because `physical_ai_data.training_export` does not exist.

- [ ] **Step 4: Implement minimal training export module**

Create `src/physical_ai_data/training_export.py`:

```python
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping

from physical_ai_data.candidates import export_candidates
from physical_ai_data.package_io import read_csv_rows, read_json, write_csv_rows, write_json
from physical_ai_data.validation import MANIFEST_FILENAME, validate_package

TRAINING_EVAL_EXPORT_FORMAT = "physical-ai-training-eval-draft/v0.1"
TRAINING_EVAL_SAMPLE_COLUMNS = [
    "sample_id",
    "split",
    "frame_id",
    "timestamp_s",
    "candidate_id",
    "source_type",
    "score",
    "label_status",
    "package_root",
]


def export_training_eval_draft(
    package_root: str | Path,
    output_dir: str | Path | None = None,
    *,
    split: str = "unspecified",
) -> Path:
    root = Path(package_root)
    validation = validate_package(root)
    if not validation.ok:
        raise ValueError(_format_validation_errors(validation.errors))

    manifest = read_json(root / MANIFEST_FILENAME)
    candidates_csv = root / "derived" / "candidates.csv"
    if not candidates_csv.exists():
        candidates_csv = export_candidates(root)

    candidates = read_csv_rows(candidates_csv)
    output = Path(output_dir) if output_dir is not None else root / "derived" / "training_eval"
    sample_rows = [_sample_row(index, split, candidate, root) for index, candidate in enumerate(candidates)]
    write_csv_rows(output / "samples.csv", TRAINING_EVAL_SAMPLE_COLUMNS, sample_rows)
    write_json(output / "training_eval_manifest.json", _manifest(root, manifest, split, len(sample_rows)))
    return output


def _sample_row(index: int, split: str, candidate: Mapping[str, str], root: Path) -> dict[str, str]:
    return {
        "sample_id": f"sample_{index:04d}",
        "split": split,
        "frame_id": candidate.get("frame_id", ""),
        "timestamp_s": candidate.get("timestamp_s", ""),
        "candidate_id": candidate.get("candidate_id", ""),
        "source_type": candidate.get("source_type", ""),
        "score": candidate.get("score", ""),
        "label_status": "unlabeled",
        "package_root": str(root),
    }
```

Also add private helpers:

```python
def _manifest(root: Path, package_manifest: Mapping[str, object], split: str, candidate_count: int) -> dict[str, object]:
    return {
        "export_format": TRAINING_EVAL_EXPORT_FORMAT,
        "source_package_id": package_manifest.get("package_id", ""),
        "source_package_root": str(root),
        "schema_version": package_manifest.get("schema_version", ""),
        "scenario_type": package_manifest.get("scenario_type", ""),
        "split": split,
        "samples_csv": "samples.csv",
        "candidate_count": candidate_count,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def _format_validation_errors(errors: list[object]) -> str:
    return "; ".join(f"{error.code}: {error.message}" for error in errors)
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_training_export.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/physical_ai_data/training_export.py tests/physical_ai_data/test_training_export.py
git commit -m "feat: add training eval draft export"
```

---

### Task 2: Thin SDK Wrapper

**Files:**
- Create: `src/physical_ai_data/sdk.py`
- Modify: `src/physical_ai_data/__init__.py`
- Create: `tests/physical_ai_data/test_sdk.py`

- [ ] **Step 1: Write failing SDK tests**

Create `tests/physical_ai_data/test_sdk.py`:

```python
from pathlib import Path

from physical_ai_data import (
    convert_to_rerun,
    export_candidates_csv,
    export_training_eval_draft,
    summarize,
    validate,
)
from physical_ai_data.samples import generate_pick_sort_package


def test_sdk_exports_package_operations(tmp_path: Path):
    package = generate_pick_sort_package(tmp_path / "pick", frame_count=8, random_seed=6)
    output_rrd = tmp_path / "pick.rrd"

    validation = validate(package)
    summary = summarize(package)
    candidates = export_candidates_csv(package)
    training_eval = export_training_eval_draft(package, split="eval")
    rrd = convert_to_rerun(package, output_rrd)

    assert validation.ok
    assert summary["frame_count"] == 8
    assert candidates == package / "derived" / "candidates.csv"
    assert (training_eval / "training_eval_manifest.json").exists()
    assert rrd == output_rrd
    assert output_rrd.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/physical_ai_data/test_sdk.py -q
```

Expected: FAIL because SDK entry points are not exported.

- [ ] **Step 3: Implement SDK wrapper and package exports**

Create `src/physical_ai_data/sdk.py`:

```python
from __future__ import annotations

from pathlib import Path

from physical_ai_data.candidates import export_candidates, summarize_package
from physical_ai_data.rerun_adapter import write_rrd
from physical_ai_data.schema import ValidationResult
from physical_ai_data.training_export import export_training_eval_draft as _export_training_eval_draft
from physical_ai_data.validation import validate_package


def validate(package_root: str | Path) -> ValidationResult:
    return validate_package(package_root)


def summarize(package_root: str | Path) -> dict[str, object]:
    return summarize_package(package_root)


def export_candidates_csv(
    package_root: str | Path,
    output_csv: str | Path | None = None,
    *,
    min_score: float = 0.5,
) -> Path:
    return export_candidates(package_root, output_csv=output_csv, min_score=min_score)


def convert_to_rerun(package_root: str | Path, output_rrd: str | Path) -> Path:
    return write_rrd(package_root, output_rrd)


def export_training_eval_draft(
    package_root: str | Path,
    output_dir: str | Path | None = None,
    *,
    split: str = "unspecified",
) -> Path:
    return _export_training_eval_draft(package_root, output_dir=output_dir, split=split)
```

Modify `src/physical_ai_data/__init__.py`:

```python
"""Physical AI Package utilities."""

from physical_ai_data.sdk import (
    convert_to_rerun,
    export_candidates_csv,
    export_training_eval_draft,
    summarize,
    validate,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "convert_to_rerun",
    "export_candidates_csv",
    "export_training_eval_draft",
    "summarize",
    "validate",
]
```

- [ ] **Step 4: Run focused SDK tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_sdk.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/physical_ai_data/sdk.py src/physical_ai_data/__init__.py tests/physical_ai_data/test_sdk.py
git commit -m "feat: expose thin package SDK"
```

---

### Task 3: External Importer Contract and LeRobot Implementation

**Files:**
- Create: `src/physical_ai_data/importers.py`
- Modify: `src/physical_ai_data/lerobot_adapter.py`
- Create: `tests/physical_ai_data/test_importers.py`
- Modify: `tests/physical_ai_data/test_lerobot_cli.py`

- [ ] **Step 1: Write failing generic importer contract test**

Create `tests/physical_ai_data/test_importers.py`:

```python
from pathlib import Path

import pytest

from physical_ai_data.importers import ImportRequest, ImportResult, run_import


class FakeImporter:
    source_format = "fake"

    def import_package(self, request: ImportRequest) -> ImportResult:
        return ImportResult(
            package_root=request.output_dir,
            source_format=request.source_format,
            source_id=str(request.source.get("id", "")),
            frame_count=2,
            warnings=[],
        )


def test_run_import_executes_matching_importer(tmp_path: Path):
    request = ImportRequest(
        source_format="fake",
        source={"id": "example"},
        output_dir=tmp_path / "package",
        options={"max_frames": 2},
    )

    result = run_import(FakeImporter(), request)

    assert result.package_root == tmp_path / "package"
    assert result.source_format == "fake"
    assert result.source_id == "example"
    assert result.frame_count == 2


def test_run_import_rejects_source_format_mismatch(tmp_path: Path):
    request = ImportRequest(source_format="other", source={}, output_dir=tmp_path / "package")

    with pytest.raises(ValueError, match="Importer source_format fake cannot handle other"):
        run_import(FakeImporter(), request)
```

- [ ] **Step 2: Write failing LeRobot importer contract test**

Append:

```python
def test_lerobot_package_importer_maps_request_to_loader(monkeypatch, tmp_path: Path):
    from physical_ai_data.lerobot_adapter import LeRobotEpisode, LeRobotFrame, LeRobotPackageImporter

    seen = {}

    def fake_load_lerobot_episode(**kwargs):
        seen.update(kwargs)
        return LeRobotEpisode(
            repo_id=kwargs["repo_id"],
            episode_index=kwargs["episode_index"],
            fps=10.0,
            frames=[LeRobotFrame(frame_index=0, timestamp_s=0.0, state=[1.0], action=[0.5])],
            profile="pusht",
        )

    monkeypatch.setattr("physical_ai_data.lerobot_loader.load_lerobot_episode", fake_load_lerobot_episode)
    request = ImportRequest(
        source_format="lerobot",
        source={"repo_id": "lerobot/pusht", "episode_index": 0, "root": None},
        output_dir=tmp_path / "package",
        options={"profile": "pusht", "max_frames": 1, "camera": None},
    )

    result = run_import(LeRobotPackageImporter(), request)

    assert seen == {
        "repo_id": "lerobot/pusht",
        "episode_index": 0,
        "root": None,
        "profile": "pusht",
        "max_frames": 1,
        "camera": None,
    }
    assert result.package_root == tmp_path / "package"
    assert result.source_format == "lerobot"
    assert result.source_id == "lerobot/pusht#episode=0"
    assert result.frame_count == 1
    assert (tmp_path / "package" / "physical_ai_manifest.json").exists()
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/physical_ai_data/test_importers.py -q
```

Expected: FAIL because `physical_ai_data.importers` does not exist.

- [ ] **Step 4: Implement importer contract**

Create `src/physical_ai_data/importers.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Protocol


@dataclass(frozen=True)
class ImportRequest:
    source_format: str
    source: Mapping[str, object]
    output_dir: Path
    options: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ImportResult:
    package_root: Path
    source_format: str
    source_id: str
    frame_count: int
    warnings: list[str] = field(default_factory=list)


class PackageImporter(Protocol):
    source_format: str

    def import_package(self, request: ImportRequest) -> ImportResult:
        ...


def run_import(importer: PackageImporter, request: ImportRequest) -> ImportResult:
    if importer.source_format != request.source_format:
        raise ValueError(f"Importer source_format {importer.source_format} cannot handle {request.source_format}")
    return importer.import_package(request)
```

- [ ] **Step 5: Implement `LeRobotPackageImporter`**

Modify `src/physical_ai_data/lerobot_adapter.py`:

```python
from physical_ai_data.importers import ImportRequest, ImportResult
from physical_ai_data.validation import validate_package
```

Add near public functions:

```python
class LeRobotPackageImporter:
    source_format = "lerobot"

    def import_package(self, request: ImportRequest) -> ImportResult:
        if request.source_format != self.source_format:
            raise ValueError(f"LeRobot importer cannot handle {request.source_format}")

        from physical_ai_data.lerobot_loader import load_lerobot_episode

        repo_id = _required_str(request.source, "repo_id")
        episode_index = _required_int(request.source, "episode_index")
        root = request.source.get("root")
        profile = _optional_str(request.options, "profile") or "auto"
        max_frames = _optional_int(request.options, "max_frames")
        camera = _optional_str(request.options, "camera")

        episode = load_lerobot_episode(
            repo_id=repo_id,
            episode_index=episode_index,
            root=root,
            profile=profile,
            max_frames=max_frames,
            camera=camera,
        )
        try:
            package_root = import_lerobot_episode(
                episode,
                request.output_dir,
                max_frames=max_frames,
                primary_camera=camera,
            )
        finally:
            episode.close()
        validation = validate_package(package_root)
        if not validation.ok:
            raise ValueError(_format_validation_errors(validation.errors))
        warnings = [f"{warning.code}: {warning.message}" for warning in validation.warnings]
        return ImportResult(
            package_root=package_root,
            source_format=self.source_format,
            source_id=f"{repo_id}#episode={episode_index}",
            frame_count=int(validation.summary.get("frame_count", len(episode.frames))),
            warnings=warnings,
        )
```

Add helpers:

```python
def _required_str(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} is required")
    return value


def _required_int(values: Mapping[str, object], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc


def _optional_str(values: Mapping[str, object], key: str) -> str | None:
    value = values.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _optional_int(values: Mapping[str, object], key: str) -> int | None:
    value = values.get(key)
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc


def _format_validation_errors(errors: list[object]) -> str:
    return "; ".join(f"{error.code}: {error.message}" for error in errors)
```

- [ ] **Step 6: Update LeRobot CLI test expectation**

Modify `tests/physical_ai_data/test_lerobot_cli.py` fake loader assertions if needed so they still verify:

- `repo_id`
- `episode_index`
- `root`
- `profile`
- `max_frames`
- `camera`

No real LeRobot import or network access is allowed.

- [ ] **Step 7: Run focused tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_importers.py tests/physical_ai_data/test_lerobot_cli.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/physical_ai_data/importers.py src/physical_ai_data/lerobot_adapter.py tests/physical_ai_data/test_importers.py tests/physical_ai_data/test_lerobot_cli.py
git commit -m "feat: add external importer contract"
```

---

### Task 4: CLI Boundary Updates

**Files:**
- Modify: `src/physical_ai_data/cli.py`
- Modify: `tests/physical_ai_data/test_cli.py`
- Modify: `tests/physical_ai_data/test_lerobot_cli.py`

- [ ] **Step 1: Write failing CLI training draft tests**

Append to `tests/physical_ai_data/test_cli.py`:

```python
def test_cli_export_training_draft(tmp_path: Path):
    package = tmp_path / "weld"

    generate = _run(["generate", "welding", "--output-dir", str(package), "--frames", "8", "--seed", "9"])
    assert generate.returncode == 0, generate.stderr

    export = _run(["export-training-draft", str(package), "--split", "eval"])

    assert export.returncode == 0, export.stderr
    output_dir = package / "derived" / "training_eval"
    assert str(output_dir) in export.stdout
    assert (output_dir / "training_eval_manifest.json").exists()
    assert (output_dir / "samples.csv").exists()


def test_cli_export_training_draft_custom_output(tmp_path: Path):
    package = tmp_path / "weld"
    output_dir = tmp_path / "training_export"

    generate = _run(["generate", "welding", "--output-dir", str(package), "--frames", "8"])
    assert generate.returncode == 0, generate.stderr

    export = _run(["export-training-draft", str(package), "--output-dir", str(output_dir), "--split", "holdout"])

    assert export.returncode == 0, export.stderr
    assert (output_dir / "training_eval_manifest.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/physical_ai_data/test_cli.py::test_cli_export_training_draft tests/physical_ai_data/test_cli.py::test_cli_export_training_draft_custom_output -q
```

Expected: FAIL because CLI command does not exist.

- [ ] **Step 3: Refactor CLI package operations through SDK and add command**

Modify imports in `src/physical_ai_data/cli.py` to use SDK:

```python
from physical_ai_data.sdk import (
    convert_to_rerun,
    export_candidates_csv,
    export_training_eval_draft,
    summarize,
    validate,
)
```

Add parser:

```python
    training = subcommands.add_parser("export-training-draft", help="Export a minimum training/evaluation draft from package candidates.")
    training.add_argument("package", type=Path, help="Package directory to export from.")
    training.add_argument("--output-dir", type=Path, help="Output directory. Defaults to PACKAGE/derived/training_eval.")
    training.add_argument("--split", default="unspecified", help="Split value to write into samples.csv.")
    training.set_defaults(func=_export_training_draft)
```

Update existing handlers:

- `_validate` calls `validate(args.package)`.
- `_summarize` calls `validate(args.package)` for JSON invalid path and `summarize(args.package)` for valid summaries.
- `_export_candidates` calls `export_candidates_csv(...)`.
- `_convert_rerun` calls `convert_to_rerun(...)`.

Add handler:

```python
def _export_training_draft(args: argparse.Namespace) -> int:
    output = export_training_eval_draft(args.package, output_dir=args.output_dir, split=args.split)
    print(f"Wrote training/evaluation draft: {output}")
    return 0
```

- [ ] **Step 4: Route `import-lerobot` through importer contract**

Modify `_import_lerobot`:

```python
def _import_lerobot(args: argparse.Namespace) -> int:
    from physical_ai_data.importers import ImportRequest, run_import
    from physical_ai_data.lerobot_adapter import LeRobotPackageImporter

    if args.max_frames is not None and args.max_frames <= 0:
        raise ValueError("max_frames must be positive")

    result = run_import(
        LeRobotPackageImporter(),
        ImportRequest(
            source_format="lerobot",
            source={"repo_id": args.repo_id, "episode_index": args.episode_index, "root": args.root},
            output_dir=args.output_dir,
            options={"profile": args.profile, "max_frames": args.max_frames, "camera": args.camera},
        ),
    )
    print(f"Imported LeRobot episode to Physical AI Package: {result.package_root}")
    return 0
```

This is the explicit LeRobot field mapping acceptance point:

- `--repo-id` -> `ImportRequest.source["repo_id"]`
- `--episode-index` -> `ImportRequest.source["episode_index"]`
- `--root` -> `ImportRequest.source["root"]`
- `--output-dir` -> `ImportRequest.output_dir`
- `--profile` -> `ImportRequest.options["profile"]`
- `--max-frames` -> `ImportRequest.options["max_frames"]`
- `--camera` -> `ImportRequest.options["camera"]`

- [ ] **Step 5: Run focused CLI tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_cli.py tests/physical_ai_data/test_lerobot_cli.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/physical_ai_data/cli.py tests/physical_ai_data/test_cli.py tests/physical_ai_data/test_lerobot_cli.py
git commit -m "feat: expose training draft CLI"
```

---

### Task 5: Documentation, Full Verification, and Review Prep

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `docs/stage4/README.md`
- Modify: `docs/research/06-lerobot开放数据样板链路记录.md`

- [ ] **Step 1: Update README project status and document links**

Add Stage 4.2 spec/plan links to the document directory and update current status to mention:

- Stage 4.2 adds minimum SDK wrapper.
- Stage 4.2 defines external importer contract.
- LeRobot importer now uses that contract.
- Minimum training/evaluation draft export exists.
- Viewer/Blueprint GUI acceptance remains pending.

- [ ] **Step 2: Update `details.md`**

Add a `2026-06-10` section under current completed items:

- Stage 4.2 spec and plan completed.
- Added thin SDK entry.
- Added importer contract and LeRobot importer implementation.
- Added training/evaluation draft export.
- Default tests pass.

Update next plan:

1. GUI Viewer/Blueprint acceptance when environment is available.
2. Stage 4.3: harden training/evaluation export contract.
3. Start designing non-LeRobot external importer fixture or real business importer candidate.

- [ ] **Step 3: Update Stage 4 run guide**

In `docs/stage4/README.md`, add sections:

- Python SDK quick use:

```python
from physical_ai_data import summarize, export_training_eval_draft

summary = summarize("artifacts/stage4/pusht_episode_0000")
training_eval_dir = export_training_eval_draft("artifacts/stage4/pusht_episode_0000")
```

- External importer boundary:

```python
from pathlib import Path
from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.lerobot_adapter import LeRobotPackageImporter

result = run_import(
    LeRobotPackageImporter(),
    ImportRequest(
        source_format="lerobot",
        source={"repo_id": "lerobot/pusht", "episode_index": 0, "root": None},
        output_dir=Path("artifacts/stage4/pusht_episode_0000"),
        options={"profile": "pusht", "max_frames": 120, "camera": None},
    ),
)
```

- Training draft command:

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py export-training-draft \
  artifacts/stage4/pusht_episode_0000 \
  --split eval
```

- [ ] **Step 4: Update LeRobot chain record**

In `docs/research/06-lerobot开放数据样板链路记录.md`, add a Stage 4.2 note:

- LeRobot importer is now exposed through `LeRobotPackageImporter`.
- CLI maps LeRobot arguments into `ImportRequest`.
- This does not add new real smoke evidence and does not replace Stage 4.1 results.
- Default tests still avoid LeRobot/network.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_training_export.py tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_importers.py tests/physical_ai_data/test_cli.py tests/physical_ai_data/test_lerobot_cli.py -q
```

Expected: PASS.

- [ ] **Step 6: Run full verification**

Run:

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 7: Check git diff**

Run:

```bash
git status --short
git diff --stat
```

Expected: only Stage 4.2 files changed; no `.venv`, artifacts, cache, `.rrd`, or generated package directories tracked.

- [ ] **Step 8: Commit docs and final verification state**

```bash
git add README.md details.md docs/stage4/README.md docs/research/06-lerobot开放数据样板链路记录.md
git commit -m "docs: document Stage 4.2 SDK importer boundary"
```

---

## Final Review Requirements

After all tasks:

- Run `python -m pytest -q`.
- Run `git log --oneline --decorate -n 8`.
- Dispatch a final code review subagent for the entire implementation.
- Fix any blocking review issues.
- Use `superpowers:verification-before-completion` before claiming success.
- Then proceed to branch finishing workflow: push branch, create PR, merge remotely, sync `main`, and remove the local development branch/worktree.
