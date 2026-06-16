# Stage 7 Simulated Small Job Window Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 Stage 7 仿真优先小焊接作业窗口试点，让团队在没有真机接入条件时也能生成 Raw/Clean fixture，并复用现有 `weld_workcell` importer 跑通 Physical AI Package 链路。

**Architecture:** 新增一个小型、离线、确定性的 Stage 7 fixture generator。它只生成仿真 Raw Zone 和 Clean Zone 文件，不实现生产 connector；Clean Zone 输出适配现有 `WeldWorkcellPackageImporter` contract，再由既有 validate、candidate export、training draft 和 Rerun adapter 验证。文档层补充 Stage 7 入口、样本请求 checklist、Raw/Clean 边界和 README/details 台账。

**Tech Stack:** Python 3.11+、标准库 `json/csv/base64/pathlib/dataclasses`、pytest、现有 `physical_ai_data` importer/validator/exporter/Rerun adapter、Markdown。

---

## File Structure

- Create: `src/physical_ai_data/stage7_sim_window.py`
  - 负责生成 deterministic Stage 7 仿真小作业窗口 Raw/Clean fixture。
  - 对外提供 `generate_stage7_sim_weld_window(output_root: str | Path, frame_count: int = 5) -> Stage7SimWindowResult`。
  - 不连接真实设备，不读取外部协议，不新增 schema。
- Create: `scripts/generate_stage7_sim_window.py`
  - 轻量脚本入口，调用 `generate_stage7_sim_weld_window`。
  - 输出 Raw/Clean 目录路径，便于文档命令可复制。
- Create: `tests/physical_ai_data/test_stage7_sim_window.py`
  - TDD 覆盖 fixture 文件结构、Raw manifest 标记、Clean Zone contract、现有 importer 链路和脚本 smoke。
- Create: `docs/stage7/README.md`
  - Stage 7 阶段总览、定位、命令、验收方式和下一步。
- Create: `docs/stage7/sample_request_checklist.md`
  - 面向工程/机器人团队的真实或脱敏样本请求清单。
- Create: `docs/stage7/raw_clean_zone_pilot.md`
  - Raw Zone / Clean Zone 目录约定、脱敏边界和决策口径。
- Modify: `README.md`
  - 增加 Stage 7 当前主线、当前可用能力、常用命令、文档入口、当前边界、路线规划和当前状态。
- Modify: `details.md`
  - 记录 Stage 7 决策、完成事项、验证结果和下一阶段计划。

No changes planned:

- No production connector.
- No TCP/IP server, SDK bridge, OPC UA/MES/HMI direct integration, or DB schema.
- No Physical AI Package schema changes.
- No formal training dataset format.

---

### Task 1: Stage 7 Fixture Generator

**Files:**
- Create: `src/physical_ai_data/stage7_sim_window.py`
- Create: `scripts/generate_stage7_sim_window.py`
- Create: `tests/physical_ai_data/test_stage7_sim_window.py`

- [ ] **Step 1: Write failing fixture structure test**

Add `tests/physical_ai_data/test_stage7_sim_window.py` with:

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from physical_ai_data.candidates import export_candidates
from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.package_io import read_json
from physical_ai_data.rerun_adapter import write_rrd
from physical_ai_data.stage7_sim_window import generate_stage7_sim_weld_window
from physical_ai_data.training_export import export_training_eval_draft
from physical_ai_data.validation import validate_package
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter


def _json_lines(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_generate_stage7_sim_weld_window_writes_raw_and_clean_fixture(tmp_path: Path):
    result = generate_stage7_sim_weld_window(tmp_path / "stage7_window", frame_count=5)

    assert result.raw_root == tmp_path / "stage7_window" / "raw"
    assert result.clean_root == tmp_path / "stage7_window" / "clean" / "weld_workcell"
    raw_manifest = read_json(result.raw_root / "manifest.raw.json")
    assert raw_manifest["stage"] == "stage7"
    assert raw_manifest["source_type"] == "simulated"
    assert raw_manifest["not_production_protocol"] is True
    assert raw_manifest["desensitization"]["status"] == "synthetic"
    assert raw_manifest["window"]["task_id"] == "sim_task_stage7_001"
    assert raw_manifest["window"]["frame_count"] == 5
    assert raw_manifest["assumptions"]["timestamp_source"] == "sim_time_seconds"
    assert raw_manifest["assumptions"]["units"]["tcp_position"] == "m"
    assert raw_manifest["assumptions"]["coordinate_frames"]["tcp"] == "relative_to_robot_base"
    assert raw_manifest["raw_zone"]["sdk_robot_state_ref"] == "sdk/robot_state.ndjson"
    assert len(_json_lines(result.raw_root / "sdk" / "robot_state.ndjson")) == 5
    assert len(_json_lines(result.raw_root / "tcp_json" / "hmi_task_messages.ndjson")) >= 2
    assert (result.raw_root / "files" / "robot_program.lua").is_file()
    assert (result.raw_root / "files" / "robot_trajectory.json").is_file()
    assert (result.raw_root / "files" / "seam_trajectory.json").is_file()
    assert (result.raw_root / "files" / "images" / "front_0000.png").is_file()
    assert (result.raw_root / "process" / "welding_process.csv").is_file()
    assert (result.raw_root / "events" / "event_log.ndjson").is_file()

    assert (result.clean_root / "job.json").is_file()
    assert (result.clean_root / "frames.csv").is_file()
    assert (result.clean_root / "process.csv").is_file()
    assert (result.clean_root / "events.csv").is_file()
    assert (result.clean_root / "review_labels.csv").is_file()
    assert (result.clean_root / "images" / "front_0000.png").is_file()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage7_sim_window.py::test_generate_stage7_sim_weld_window_writes_raw_and_clean_fixture -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'physical_ai_data.stage7_sim_window'`.

- [ ] **Step 3: Implement minimal fixture generator**

Create `src/physical_ai_data/stage7_sim_window.py`.

Implementation requirements:

- Define:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Stage7SimWindowResult:
    root: Path
    raw_root: Path
    clean_root: Path
```

- Public API:

```python
def generate_stage7_sim_weld_window(output_root: str | Path, frame_count: int = 5) -> Stage7SimWindowResult:
    ...
```

- Reject `frame_count < 3` with `ValueError("stage7 frame_count must be at least 3")`.
- Delete only previously generated files under `output_root/raw` and `output_root/clean/weld_workcell`; do not delete arbitrary parent directories.
- Write Raw Zone files:
  - `manifest.raw.json`
  - `sdk/robot_state.ndjson`
  - `tcp_json/hmi_task_messages.ndjson`
  - `files/robot_program.lua`
  - `files/robot_trajectory.json`
  - `files/seam_trajectory.json`
  - `files/images/front_0000.png`
  - `process/welding_process.csv`
  - `events/event_log.ndjson`
- Write Clean Zone files matching existing `WeldWorkcellPackageImporter` required columns:
  - `job.json`
  - `frames.csv`
  - `process.csv`
  - `events.csv`
  - `review_labels.csv`
  - `images/front_0000.png`
- Use deterministic timestamps over 4 seconds, phases `approach`, `weld`, `cooldown`, and relative image path `images/front_0000.png` only on the first frame.
- Use synthetic IDs:
  - `task_id`: `sim_task_stage7_001`
  - `work_order_id`: `SIM-WO-STAGE7-001`
  - `station_id`: `sim_station_stage7`
  - `robot_id`: `sim_robot_001`
  - `welder_id`: `sim_welder_001`
  - `part_id`: `sim_part_001`
  - `seam_id`: `sim_seam_001`
  - `task_name`: `Stage 7 simulated weld window`
- Include Raw manifest flags:
  - `stage: stage7`
  - `source_type: simulated`
  - `not_production_protocol: true`
  - `desensitization.status: synthetic`
  - `window.task_id: sim_task_stage7_001`
  - `assumptions.timestamp_source: sim_time_seconds`
  - `assumptions.units.tcp_position: m`
  - `assumptions.units.tcp_orientation: quaternion_xyzw`
  - `assumptions.units.weld_current: A`
  - `assumptions.units.weld_voltage: V`
  - `assumptions.units.travel_speed: mm/s`
  - `assumptions.coordinate_frames.robot_base: simulated_station_frame`
  - `assumptions.coordinate_frames.tcp: relative_to_robot_base`
  - `assumptions.coordinate_frames.camera_front: simulated_fixed_camera`
  - refs for all Raw files.
- Include `task_id` in at least Raw manifest and TCP JSON task messages. Existing `WeldWorkcellPackageImporter` does not require `task_id` in `job.json`, so do not extend the importer contract just to store it there.

Keep implementation small and standard-library only. Use a tiny base64 PNG for `front_0000.png` as in existing tests.

- [ ] **Step 4: Run fixture structure test to verify it passes**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage7_sim_window.py::test_generate_stage7_sim_weld_window_writes_raw_and_clean_fixture -q
```

Expected: PASS.

- [ ] **Step 5: Write failing importer chain test**

Extend `tests/physical_ai_data/test_stage7_sim_window.py`:

```python
def test_stage7_clean_fixture_imports_to_package_and_exports_derivatives(tmp_path: Path):
    result = generate_stage7_sim_weld_window(tmp_path / "stage7_window", frame_count=5)
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
    assert validation.ok, validation.errors
    assert import_result.frame_count == 5
    manifest = read_json(package_root / "physical_ai_manifest.json")
    assert manifest["scenario_type"] == "robot_welding_station"
    assert manifest["source_dataset"]["format"] == "weld_workcell"
    candidate_csv = export_candidates(package_root)
    training_dir = export_training_eval_draft(package_root, split="eval")
    rrd_path = write_rrd(package_root, tmp_path / "stage7_window.rrd")
    assert candidate_csv.is_file()
    assert (training_dir / "training_eval_manifest.json").is_file()
    assert rrd_path.is_file()
```

- [ ] **Step 6: Run importer chain test**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage7_sim_window.py::test_stage7_clean_fixture_imports_to_package_and_exports_derivatives -q
```

Expected: PASS if the first implementation already satisfies the importer contract; otherwise fix only the generator contract mismatch.

- [ ] **Step 7: Write failing script smoke test**

Extend test file:

```python
def test_generate_stage7_sim_window_script_writes_fixture(tmp_path: Path):
    output_root = tmp_path / "script_window"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_stage7_sim_window.py",
            "--output-root",
            str(output_root),
            "--frames",
            "5",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Generated Stage 7 simulated weld window" in completed.stdout
    assert (output_root / "raw" / "manifest.raw.json").is_file()
    assert (output_root / "clean" / "weld_workcell" / "job.json").is_file()
```

- [ ] **Step 8: Run script test to verify it fails**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage7_sim_window.py::test_generate_stage7_sim_window_script_writes_fixture -q
```

Expected: FAIL because `scripts/generate_stage7_sim_window.py` does not exist.

- [ ] **Step 9: Implement script**

Create `scripts/generate_stage7_sim_window.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from physical_ai_data.stage7_sim_window import generate_stage7_sim_weld_window


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Stage 7 simulated weld job window fixture.")
    parser.add_argument("--output-root", type=Path, required=True, help="Output root for raw/ and clean/ fixture directories.")
    parser.add_argument("--frames", type=int, default=5, help="Number of simulated frames to generate.")
    args = parser.parse_args(argv)

    result = generate_stage7_sim_weld_window(args.output_root, frame_count=args.frames)
    print(f"Generated Stage 7 simulated weld window: {result.root}")
    print(f"Raw Zone: {result.raw_root}")
    print(f"Clean Zone: {result.clean_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 10: Run all Stage 7 generator tests**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage7_sim_window.py -q
```

Expected: `3 passed`.

- [ ] **Step 11: Commit**

```bash
git add src/physical_ai_data/stage7_sim_window.py scripts/generate_stage7_sim_window.py tests/physical_ai_data/test_stage7_sim_window.py
git commit -m "feat: add Stage 7 simulated weld window fixture"
```

---

### Task 2: Stage 7 Documentation

**Files:**
- Create: `docs/stage7/README.md`
- Create: `docs/stage7/sample_request_checklist.md`
- Create: `docs/stage7/raw_clean_zone_pilot.md`

- [ ] **Step 1: Read authoritative context**

Run:

```bash
sed -n '1,260p' docs/superpowers/specs/2026-06-16-stage-7-simulated-small-job-window-pilot-design.md
sed -n '1,220p' docs/stage6/README.md
sed -n '1,220p' docs/stage6/real_data_field_mapping.md
```

Use the Stage 7 spec as authoritative. Do not promise production connector work.

- [ ] **Step 2: Create Stage 7 README**

Create `docs/stage7/README.md` with sections:

- `# Stage 7 仿真优先小作业窗口数据试点`
- `## 阶段定位`
- `## 为什么从仿真做起`
- `## 最小焊接作业窗口`
- `## 推荐阅读顺序`
- `## 默认命令`
- `## 当前产出物`
- `## MVP 边界`
- `## 验收方式`
- `## 下一步`

Must include:

- Stage 7 bridges Stage 6 planning and future real/desensitized samples.
- Current no-real-machine constraint.
- Generated fixture command:

```bash
python scripts/generate_stage7_sim_window.py --output-root artifacts/stage7/sim_weld_window --frames 5
```

- Clean Zone can be imported through `WeldWorkcellPackageImporter`, not a production connector.
- Stage 7 does not implement connector/server/DB/schema changes.

- [ ] **Step 3: Create sample request checklist**

Create `docs/stage7/sample_request_checklist.md` with sections:

- `# Stage 7 真实/脱敏样本请求清单`
- `## 样本窗口`
- `## 必需样本`
- `## 必需说明`
- `## 脱敏与权限`
- `## 提交方式`
- `## 样本评审结论`

Must request:

- SDK/TCP JSON examples, 5 to 20 lines.
- File examples: trajectory JSON, seam JSON, program/lua, image/point cloud naming rule.
- DB table structure and 3 to 5 desensitized rows only if DB is used.
- Timestamp source, units, coordinate frames, storage path, read/write subject.
- Explicit statement that undesensitized real data must not be committed.

- [ ] **Step 4: Create Raw/Clean pilot doc**

Create `docs/stage7/raw_clean_zone_pilot.md` with sections:

- `# Stage 7 Raw/Clean Zone 试点约定`
- `## 目录结构`
- `## Raw Zone`
- `## Clean Zone`
- `## 从 Clean Zone 到 Physical AI Package`
- `## 后续决策表`
- `## 暂不决定的问题`

Must include the Raw and Clean directory trees from the spec and the decision table from spec section 12.

- [ ] **Step 5: Verify docs**

Run:

```bash
test -f docs/stage7/README.md
test -f docs/stage7/sample_request_checklist.md
test -f docs/stage7/raw_clean_zone_pilot.md
rg "仿真优先|Raw Zone|Clean Zone|WeldWorkcellPackageImporter|不实现生产 connector|未脱敏" docs/stage7
```

Expected: all files exist and search terms appear.

- [ ] **Step 6: Commit**

```bash
git add docs/stage7/README.md docs/stage7/sample_request_checklist.md docs/stage7/raw_clean_zone_pilot.md
git commit -m "docs: add Stage 7 pilot documentation"
```

---

### Task 3: Project Entry Updates and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `details.md`

- [ ] **Step 1: Inspect current project entry docs**

Run:

```bash
sed -n '1,260p' README.md
sed -n '1,360p' details.md
```

Keep edits surgical. Preserve Stage 6 history while adding Stage 7 status.

- [ ] **Step 2: Update README**

Modify `README.md`:

- In current mainline/project positioning, update from Stage 6 to Stage 7:
  - Stage 7 is “仿真优先小作业窗口数据试点”.
  - Real machine access is still unavailable; Stage 7 uses simulated Raw/Clean fixture to prepare for real/desensitized samples.
- In current capabilities, add Stage 7 fixture generator.
- In common commands, add:

```bash
python scripts/generate_stage7_sim_window.py --output-root artifacts/stage7/sim_weld_window --frames 5
```

- In engineering handoff / recommended reading, add Stage 7 docs before Stage 6 docs.
- In roadmap, add Stage 7 after Stage 6.
- In current boundaries, state Stage 7 does not implement production connector, DB schema, or package schema changes.
- In document directory, add the Stage 7 spec, plan, and docs.

- [ ] **Step 3: Update details**

Modify `details.md`:

- Add a new `### 2026-06-16` section under current completed items.
- Record Stage 7 key decisions:
  - choose simulated small job window pilot because real machine access is unavailable.
  - use Raw/Clean fixture, not production connector.
  - Clean Zone targets existing `weld_workcell` importer contract.
  - future real/desensitized samples determine connector/schema/DB needs.
- Record files added and final verification commands.
- Replace `## 下一步计划` with Stage 8-oriented next steps:
  - use one real/desensitized weld window to replace simulated Raw Zone.
  - review field/time/coordinate/desensitization gaps.
  - decide importer evolution vs connector skeleton vs DB/schema/package changes.
  - confirm AI controller storage/permission boundaries.

- [ ] **Step 4: Run targeted verification**

Run:

```bash
python -m pytest tests/physical_ai_data/test_stage7_sim_window.py -q
python scripts/generate_stage7_sim_window.py --output-root /tmp/stage7_sim_weld_window --frames 5
```

Expected: Stage 7 tests pass; script exits 0 and writes `/tmp/stage7_sim_weld_window/raw` and `/tmp/stage7_sim_weld_window/clean/weld_workcell`.

- [ ] **Step 5: Run package chain smoke**

Run:

```bash
python - <<'PY'
from pathlib import Path
from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.stage7_sim_window import generate_stage7_sim_weld_window
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter

root = Path("/tmp/stage7_chain")
result = generate_stage7_sim_weld_window(root / "window", frame_count=5)
package = root / "package"
run_import(
    WeldWorkcellPackageImporter(),
    ImportRequest(
        source_format="weld_workcell",
        source={"root": result.clean_root},
        output_dir=package,
        options={"copy_images": True},
    ),
)
print(package)
PY
python scripts/physical_ai_package.py validate /tmp/stage7_chain/package --json
python scripts/physical_ai_package.py summarize /tmp/stage7_chain/package --json
python scripts/physical_ai_package.py export-candidates /tmp/stage7_chain/package
python scripts/physical_ai_package.py export-training-draft /tmp/stage7_chain/package --split eval
python scripts/physical_ai_package.py convert-rerun /tmp/stage7_chain/package --output-rrd /tmp/stage7_chain/package.rrd
```

Expected: all commands exit 0; candidate CSV, training draft and `.rrd` are generated.

- [ ] **Step 6: Run full verification**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit docs and entry updates**

```bash
git add README.md details.md
git commit -m "docs: update project status for Stage 7"
```

If Task 2 docs were not already committed, include them in their own commit before this step.

---

## Final Branch Verification

Before opening a PR, run:

```bash
git status --short
python -m pytest -q
python scripts/generate_stage7_sim_window.py --output-root /tmp/stage7_final_window --frames 5
python - <<'PY'
from pathlib import Path
from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.stage7_sim_window import generate_stage7_sim_weld_window
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter

root = Path("/tmp/stage7_final_chain")
result = generate_stage7_sim_weld_window(root / "window", frame_count=5)
run_import(
    WeldWorkcellPackageImporter(),
    ImportRequest(
        source_format="weld_workcell",
        source={"root": result.clean_root},
        output_dir=root / "package",
        options={"copy_images": True},
    ),
)
print(root / "package")
PY
python scripts/physical_ai_package.py validate /tmp/stage7_final_chain/package --json
python scripts/physical_ai_package.py summarize /tmp/stage7_final_chain/package --json
python scripts/physical_ai_package.py export-candidates /tmp/stage7_final_chain/package
python scripts/physical_ai_package.py export-training-draft /tmp/stage7_final_chain/package --split eval
python scripts/physical_ai_package.py convert-rerun /tmp/stage7_final_chain/package --output-rrd /tmp/stage7_final_chain/package.rrd
```

Expected:

- Git status is clean.
- All tests pass.
- Stage 7 fixture script exits 0.
- Package chain smoke exits 0 and writes `.rrd`.
