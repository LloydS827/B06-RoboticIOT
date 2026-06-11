# Stage 5 Handoff Docs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Stage 2-4.4 的研发成果整理成面向项目使用者和工程/机器人团队的 Stage 5 业务接入与交付文档包。

**Architecture:** 本阶段只做文档与索引更新，不新增 importer、CLI、SDK API 或 package schema。根 README 做项目入口和快速开始，`docs/stage5/README.md` 做交付阶段总览，`docs/stage5/engineering_handoff.md` 做工程团队对接材料，`details.md` 记录阶段台账与下一步计划。

**Tech Stack:** Markdown、现有 Python/pytest 验证命令、现有 Physical AI Package CLI 与 importer contract。

---

## File Structure

- Modify: `README.md`
  - 更新为更清晰的项目入口：当前能力、快速开始、常用命令、文档导航、边界说明。
- Create: `docs/stage5/README.md`
  - Stage 5 业务接入与交付文档阶段总览。
- Create: `docs/stage5/engineering_handoff.md`
  - 给工程团队/机器人团队的接入说明、字段 contract、产出物、验收 checklist、常见错误、对接会议问题清单。
- Modify: `docs/stage4/README.md`
  - 增加 Stage 5 对接文档入口，避免 Stage 4 文档继续承担对接总览。
- Modify: `details.md`
  - 记录 Stage 5 完成事项、验证结果和下一阶段规划。

No changes planned:

- No production code.
- No test code unless a broken doc command reveals a real issue.
- No CLI/API/schema changes.
- No real customer or site data.

PR、远端合并和本地分支清理属于本轮交付流程，不属于产品文档完成定义；执行完成后仍按用户要求完成。

---

### Task 1: README Project Entry Refresh

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read current project commands and docs**

Run:

```bash
sed -n '1,220p' README.md
sed -n '1,220p' scripts/physical_ai_package.py
sed -n '1,220p' docs/stage3/README.md
sed -n '1,260p' docs/stage4/README.md
```

Confirm the README quick-start commands reference existing scripts and documented flows.

- [ ] **Step 2: Update README structure**

Edit `README.md` to include these sections, keeping existing project positioning but making it easier for a new reader:

- `## 当前可用能力`
- `## 快速开始`
- `## 常用命令`
- `## 工程团队对接`
- `## 文档目录`
- `## 当前边界`
- `## 当前状态`

Keep existing “项目定位”“核心能力方向”“总体路线规划” content unless it directly conflicts with Stage 5.

- [ ] **Step 3: Add current capability summary**

Under `## 当前可用能力`, include concise bullets for:

- Physical AI Package v0.1。
- simulation sample 生成。
- validate / summarize / candidate export。
- Rerun `.rrd` adapter。
- SDK wrapper。
- LeRobot importer。
- CSV recording fixture。
- Weld workcell importer candidate。
- training/evaluation draft export v0.2。

Make the status precise: `WeldWorkcellPackageImporter` is a business importer candidate, not a production connector.

- [ ] **Step 4: Add quick start and common commands**

Add commands that exist today:

```bash
python3 -m pip install -e ".[dev]"
python -m pytest -q
python scripts/physical_ai_package.py generate welding --output-dir artifacts/stage5/demo_weld
python scripts/physical_ai_package.py validate artifacts/stage5/demo_weld --json
python scripts/physical_ai_package.py summarize artifacts/stage5/demo_weld --json
python scripts/physical_ai_package.py export-candidates artifacts/stage5/demo_weld
python scripts/physical_ai_package.py export-training-draft artifacts/stage5/demo_weld --split eval
python scripts/physical_ai_package.py convert-rerun artifacts/stage5/demo_weld --output-rrd artifacts/stage5/demo_weld.rrd
```

If command syntax differs after inspecting the CLI, use the actual syntax.

- [ ] **Step 5: Add handoff doc links and boundaries**

Add links to:

- `docs/stage5/README.md`
- `docs/stage5/engineering_handoff.md`
- `docs/stage4/README.md`
- `docs/superpowers/specs/2026-06-11-stage-5-handoff-docs-design.md`
- `docs/superpowers/plans/2026-06-11-stage-5-handoff-docs.md`

Under current boundaries, state:

- Rerun is a replaceable adapter backend, not the primary data structure.
- Weld workcell importer is candidate/handoff contract, not production connector.
- Real site integration, permissions/audit, desensitization, MES/PLC/HMI direct integration, and native GUI acceptance remain future work.

- [ ] **Step 6: Run a command sanity check**

Run:

```bash
python scripts/physical_ai_package.py --help >/tmp/stage5_cli_help.txt
python scripts/physical_ai_package.py generate welding --output-dir /tmp/stage5_demo_weld
python scripts/physical_ai_package.py validate /tmp/stage5_demo_weld --json >/tmp/stage5_validate.json
python scripts/physical_ai_package.py summarize /tmp/stage5_demo_weld --json >/tmp/stage5_summary.json
```

Expected: all commands exit 0. If a README command is wrong, fix README to match actual CLI.

- [ ] **Step 7: Commit Task 1**

```bash
git add README.md
git commit -m "docs: refresh README for Stage 5 handoff"
```

---

### Task 2: Stage 5 Overview and Engineering Handoff Docs

**Files:**
- Create: `docs/stage5/README.md`
- Create: `docs/stage5/engineering_handoff.md`

- [ ] **Step 1: Create Stage 5 overview**

Create `docs/stage5/README.md` with:

- Title: `# Stage 5 业务接入与交付文档`
- Stage 5 positioning: transition from technical feasibility to business handoff.
- Audience:
  - 项目负责人。
  - 工程团队。
  - 机器人团队。
  - 算法/数据团队。
- Recommended reading order:
  - root README。
  - `engineering_handoff.md`。
  - `docs/stage4/README.md`。
  - specs/plans as needed。
- System outputs:
  - Physical AI Package。
  - validation summary。
  - `derived/candidates.csv`。
  - training/evaluation draft。
  - Rerun `.rrd`。
- Minimal acceptance flow:
  - tests pass。
  - package validates。
  - summary reads counts。
  - candidates export。
  - training draft export。
  - Rerun conversion。
- Stage 5 non-goals:
  - no real production connector。
  - no native GUI acceptance。
  - no schema expansion。
  - no real customer data。

- [ ] **Step 2: Create engineering handoff document**

Create `docs/stage5/engineering_handoff.md` with these sections:

- `## 对接目标`
- `## 工程团队需要准备什么`
- `## 推荐导出目录`
- `## 字段 Contract`
- `## Python 调用方式`
- `## 系统产出物`
- `## 验收 Checklist`
- `## 常见错误`
- `## 对接会议问题清单`
- `## 当前边界`

- [ ] **Step 3: Document source directory contract**

In `engineering_handoff.md`, document:

```text
source_root/
  job.json
  frames.csv
  process.csv
  events.csv
  review_labels.csv
  images/
```

State:

- `job.json`、`frames.csv`、`process.csv`、`events.csv` required.
- `review_labels.csv` optional.
- `images/` optional, but any non-empty `frames.csv.image_path` must point to an existing relative file.

- [ ] **Step 4: Document field contract**

Use tables for each file:

- `job.json`: `work_order_id`, `station_id`, `robot_id`, `welder_id`, `part_id`, `seam_id`, `task_name`, `created_at`.
- `frames.csv`: `timestamp_s`, `phase`, `tcp_x`, `tcp_y`, `tcp_z`, `tcp_qx`, `tcp_qy`, `tcp_qz`, `tcp_qw`, `image_path`.
- `process.csv`: `timestamp_s`, `weld_current_a`, `weld_voltage_v`, `wire_feed_mpm`, `gas_flow_lpm`, `travel_speed_mm_s`, `defect_probability`.
- `events.csv`: `timestamp_s`, `event_type`, `severity`, `message`, `object_id`.
- `review_labels.csv`: `timestamp_s`, `label_type`, `value`, `confidence`, optional `review_status`, optional `reviewer`.

Important exact wording:

- `events.csv.object_id` must be empty or equal to the concrete value of `job.json.part_id` / `job.json.seam_id`; examples: `part_alpha`, `seam_root`; do not write literal `part_id` or `seam_id`.
- timestamps are seconds.
- numeric fields must be finite numbers.
- image paths must be relative to `source_root`, no absolute paths, no `..`, no symlink escape.
- `review_status` and `reviewer` stay in `artifacts/source/review_labels.csv`; they do not enter `labels.csv`.

- [ ] **Step 5: Document usage and outputs**

Add Python example:

```python
from pathlib import Path

from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter

result = run_import(
    WeldWorkcellPackageImporter(),
    ImportRequest(
        source_format="weld_workcell",
        source={"root": Path("fixtures/weld_workcell_export")},
        output_dir=Path("artifacts/stage5/weld_workcell_package"),
        options={"copy_images": True},
    ),
)
```

Split outputs into:

- Import immediately creates package tables and `artifacts/`.
- Follow-up commands create `derived/candidates.csv`, `derived/training_eval/`, and `.rrd`.

Add exact follow-up command snippets:

```bash
python scripts/physical_ai_package.py validate artifacts/stage5/weld_workcell_package --json
python scripts/physical_ai_package.py summarize artifacts/stage5/weld_workcell_package --json
python scripts/physical_ai_package.py export-candidates artifacts/stage5/weld_workcell_package
python scripts/physical_ai_package.py export-training-draft artifacts/stage5/weld_workcell_package --split eval
python scripts/physical_ai_package.py convert-rerun artifacts/stage5/weld_workcell_package --output-rrd artifacts/stage5/weld_workcell_package.rrd
```

- [ ] **Step 6: Document checklist, errors, and meeting questions**

Checklist must cover:

- source files present.
- headers match contract.
- image paths legal.
- import succeeds.
- validate succeeds.
- summarize returns expected counts.
- candidate export succeeds.
- training draft export succeeds.
- Rerun `.rrd` writes successfully.
- missing fields are recorded for follow-up.

Common errors must include:

- missing file.
- missing job field.
- missing CSV column.
- malformed row.
- non-finite numeric.
- empty frames.
- invalid image path.
- symlink escape.
- unknown event object id.
- output_dir same as source.root.

Meeting questions must cover:

- data source ownership.
- timestamp source/synchronization.
- image/video export path.
- process sampling frequency.
- event/alarm fields.
- defect/quality score source.
- desensitization/customer boundary.

- [ ] **Step 7: Run field-contract consistency check**

Run:

```bash
rg "object_id|weld_current_a|review_status|output_dir must not|image_path" docs/stage5 docs/stage4 tests/physical_ai_data/test_weld_workcell_importer.py src/physical_ai_data/weld_workcell_importer.py
```

Expected: Stage 5 docs agree with Stage 4.4 docs and importer tests. Fix wording if any mismatch appears.

- [ ] **Step 8: Commit Task 2**

```bash
git add docs/stage5/README.md docs/stage5/engineering_handoff.md
git commit -m "docs: add Stage 5 engineering handoff"
```

---

### Task 3: Cross-Link Stage 4 and Update Details

**Files:**
- Modify: `docs/stage4/README.md`
- Modify: `details.md`

- [ ] **Step 1: Add Stage 5 link to Stage 4 docs**

In `docs/stage4/README.md`, near the Weld Workcell importer candidate section or before known limitations, add a short note:

```markdown
## Stage 5 工程对接入口

如果准备与工程团队或机器人团队对接真实/脱敏业务导出，请优先阅读 [Stage 5 业务接入与交付文档](../stage5/README.md) 和 [工程团队对接说明](../stage5/engineering_handoff.md)。Stage 4 文档保留 importer 与开放数据样板链路细节，Stage 5 文档负责对接流程、字段准备、验收 checklist 和线下沟通问题清单。
```

- [ ] **Step 2: Update details**

In `details.md`, add a `### 2026-06-11` entry or append under current date:

- Stage 5 renamed from possible Stage 4.5 to a new stage.
- Added Stage 5 spec and plan.
- Added root README handoff-oriented quick start.
- Added `docs/stage5/README.md`.
- Added `docs/stage5/engineering_handoff.md`.
- Stage 5 does not add new product code; it prepares engineering handoff and business integration.
- Record final verification commands after they are run.

Update `## 下一步计划` to:

1. Use Stage 5 handoff docs with engineering/robotics team to collect a real or desensitized sample.
2. Calibrate `weld_workcell` contract against that sample.
3. Decide label schema / review status boundary from real data.
4. Keep GUI Viewer/Blueprint acceptance as environment-dependent follow-up.

- [ ] **Step 3: Run docs path/link sanity**

Run:

```bash
test -f docs/stage5/README.md
test -f docs/stage5/engineering_handoff.md
test -f docs/superpowers/specs/2026-06-11-stage-5-handoff-docs-design.md
test -f docs/superpowers/plans/2026-06-11-stage-5-handoff-docs.md
rg "docs/stage5|stage5|engineering_handoff" README.md docs/stage4/README.md details.md docs/stage5
```

Expected: all referenced files exist and links appear in root/stage docs.

- [ ] **Step 4: Run focused command verification**

Run:

```bash
python scripts/physical_ai_package.py generate welding --output-dir /tmp/stage5_demo_weld
python scripts/physical_ai_package.py validate /tmp/stage5_demo_weld --json >/tmp/stage5_validate.json
python scripts/physical_ai_package.py summarize /tmp/stage5_demo_weld --json >/tmp/stage5_summary.json
python scripts/physical_ai_package.py export-candidates /tmp/stage5_demo_weld
python scripts/physical_ai_package.py export-training-draft /tmp/stage5_demo_weld --split eval
python scripts/physical_ai_package.py convert-rerun /tmp/stage5_demo_weld --output-rrd /tmp/stage5_demo_weld.rrd
```

Expected: all commands exit 0.

- [ ] **Step 5: Run full tests**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 6: Record verification results in details**

Update `details.md` with exact output summary from Step 4 and Step 5.

- [ ] **Step 7: Commit Task 3**

```bash
git add docs/stage4/README.md details.md
git commit -m "docs: record Stage 5 handoff status"
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

- [ ] Push and create PR:

```bash
git push -u origin codex/stage-5-handoff-docs
gh pr create --fill
```

- [ ] After remote merge is confirmed, run cleanup from the parent/main worktree:

```bash
git pull --ff-only
git worktree remove .worktrees/stage-5-handoff-docs
git branch -d codex/stage-5-handoff-docs
```

If the PR is squash-merged and `git branch -d` refuses because individual commits are not merged, verify `main` contains the PR merge commit first, then use `git branch -D codex/stage-5-handoff-docs`.
