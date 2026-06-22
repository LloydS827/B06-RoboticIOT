# Stage 7.1 Industrial Physical AI Profile Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 B06 从历史性的 Rerun/Robotic IOT 阶段叙述收束为“工业物理 AI 数据层”，并以 A01 H300 最小焊接作业窗口为 Stage 7.1 第一 profile contract。

**Architecture:** 本轮只做文档与 contract 收敛，不改 Python package、schema、importer 或默认 CLI。README 负责项目级入口，`docs/profiles/` 负责四类项目 profile，`docs/stage7/` 负责 A01 H300 最小作业窗口试点，`details.md` 负责执行记录和下一阶段计划。

**Tech Stack:** Markdown 文档、现有 `WeldWorkcellPackageImporter` clean contract、现有 pytest 默认验证。

---

## File Structure

- Create: `docs/profiles/README.md`  
  Profile 总览、阅读顺序、共同边界、数据分级。
- Create: `docs/profiles/a01_weld_workcell_job_window.md`  
  A01 H300 最小焊接作业窗口 profile contract。
- Create: `docs/profiles/a02_manipulation_skill_asset_evidence.md`  
  A02 `ManipulationSkillAsset` evidence profile contract。
- Create: `docs/profiles/b08_equipment_timeseries_observation_package.md`  
  B08 设备时序观测 profile contract。
- Create: `docs/profiles/s01_manufacturing_event_context_package.md`  
  S01 制造事件上下文 profile contract。
- Create: `docs/profiles/b06_to_a02_evidence_handoff.md`  
  B06 到 A02 evidence handoff，区分 evidence、context、attachment。
- Create: `docs/stage7/h300_weld_workcell_field_alignment.md`  
  A01 H300 字段与现有 `WeldWorkcellPackageImporter` clean contract 的对齐表。
- Modify: `docs/stage7/README.md`  
  将 Stage 7 从通用仿真小窗口收束为 A01 H300 最小作业窗口数据试点。
- Modify: `docs/stage7/sample_request_checklist.md`  
  补齐 A01 H300 第一批样本请求清单。
- Modify: `docs/stage7/raw_clean_zone_pilot.md`  
  强化 A01 H300 Raw/Clean Zone、真实/脱敏/仿真/临时 artifact 边界。
- Modify: `README.md`  
  首页重排为工业物理 AI 数据层入口，并索引四类 profile。
- Modify: `details.md`  
  记录 Stage 7.1 决策、产出物、验证和 Stage 8 下一步。

## Success Criteria

- README 第一段明确使用战略指定口径，定义 B06 是“公司工业物理 AI 的横向数据底座项目”。
- README 首页按项目定位、主链路、A01 H300 当前样板、当前可用能力、四类 profile、工程对接方式、当前边界呈现。
- `docs/profiles/` 存在四类 profile 和 B06 -> A02 handoff；B08/S01 保持独立 profile，没有被塞进机器人 workcell 字段结构。
- Stage 7 文档明确转向 A01 H300 最小焊接作业窗口数据试点，同时保留 simulated Raw/Clean fixture 作为当前可运行替代输入。
- A01 样本请求清单覆盖作业任务元数据、工件/焊缝引用、点云、相机位姿、机器人位姿、标定、路径点、PCL 输出、模型输出、人工修正、工艺参数、执行日志/异常/报警和质量结果。
- `docs/stage7/h300_weld_workcell_field_alignment.md` 明确哪些字段可进入 `job.json`、`frames.csv`、`process.csv`、`events.csv`、`review_labels.csv`，哪些只能作为 source artifact，哪些需要真实样本后再决定是否扩展 importer/package schema。
- README 和 Stage 7 文档明确真实、脱敏、仿真、临时 artifact 和不可提交数据边界。
- `python -m pytest -q` 通过。

## Task 1: Profile Contract Docs

**Files:**
- Create: `docs/profiles/README.md`
- Create: `docs/profiles/a01_weld_workcell_job_window.md`
- Create: `docs/profiles/a02_manipulation_skill_asset_evidence.md`
- Create: `docs/profiles/b08_equipment_timeseries_observation_package.md`
- Create: `docs/profiles/s01_manufacturing_event_context_package.md`
- Create: `docs/profiles/b06_to_a02_evidence_handoff.md`

- [ ] **Step 1: Create profile directory and overview**

Create `docs/profiles/README.md` with:

```markdown
# B06 Project Data Profiles

## 定位

B06 profile 是项目间的数据 contract，不是一次性完整 schema 实现。

## 阅读顺序

1. A01 `weld_workcell_job_window`
2. B06 -> A02 evidence handoff
3. A02 `manipulation_skill_asset_evidence`
4. B08 `equipment_timeseries_observation_package`
5. S01 `manufacturing_event_context_package`

## 共同边界

- 不提交未脱敏真实数据。
- 不把 profile 等同于生产 connector。
- 不把 B08/S01 强行映射到机器人作业结构。
```

- [ ] **Step 2: Create A01 profile**

Create `docs/profiles/a01_weld_workcell_job_window.md` covering:

- profile id: `weld_workcell_job_window`
- owning project: A01 智能焊接工站 / H300
- minimum window: one `job_window_id`, one work order/task, one part, one seam, 3-10 seconds, phases such as approach/weld/cooldown
- required information groups:
  - job/task metadata
  - workpiece/seam references
  - point cloud and PCL outputs
  - camera pose and calibration
  - robot pose and path points
  - process parameters
  - model outputs
  - human corrections/review
  - execution logs/exceptions
  - quality result
- B06 mapping:
  - Raw Zone keeps source payload and file references
  - Clean Zone aligns to `weld_workcell`
  - Physical AI Package enables replay/candidates/training draft
- explicit non-goals: no production connector, no DB schema, no full H300 protocol.

- [ ] **Step 3: Create A02 profile**

Create `docs/profiles/a02_manipulation_skill_asset_evidence.md` covering:

- profile id: `manipulation_skill_asset_evidence`
- owning project: A02 机器人技能大师
- relationship to A02 `ManipulationSkillAsset`
- evidence groups:
  - confirmed trajectory/TCP/path points
  - pose/context/skill intent
  - quality label
  - expert review
  - transfer/evaluation clues
  - failure boundary
- clarify that raw H300 source data is not automatically a skill asset.

- [ ] **Step 4: Create B08 profile**

Create `docs/profiles/b08_equipment_timeseries_observation_package.md` covering:

- profile id: `equipment_timeseries_observation_package`
- equipment/sensor/stage/cycle/window/quality/model-evaluation/candidate-signal groups
- B06 relationship: shared data governance, candidate windows, replayable evidence references
- explicit separation from robot workcell package.

- [ ] **Step 5: Create S01 profile**

Create `docs/profiles/s01_manufacturing_event_context_package.md` covering:

- profile id: `manufacturing_event_context_package`
- manufacturing object/status/event/impact/task/permission/result/review groups
- how S01 reads B06 outputs as event evidence, summary, candidate link, or quality result reference
- explicit separation from low-level robot trajectory and equipment time-series packages.

- [ ] **Step 6: Create B06 -> A02 handoff doc**

Create `docs/profiles/b06_to_a02_evidence_handoff.md` with a table:

| B06/A01 field group | Handoff category | A02 use |
| --- | --- | --- |
| confirmed TCP trajectory/path points | evidence | candidate trajectory for `ManipulationSkillAsset` |
| human correction/expert review | evidence | review record and confidence |
| quality result | evidence | outcome label |
| point cloud/image/raw logs | attachment | source evidence, not core skill fields |
| work order/customer/device identity | blocked or context after desensitization | not skill content |
| unconfirmed model output | context | hypothesis only |

Include “handoff acceptance checklist”:

- data is desensitized or onsite-only
- trajectory/context has source refs
- quality label has reviewer or source
- failure boundary is described
- attachments remain references unless allowed to copy

- [ ] **Step 7: Self-review**

Run:

```bash
rg -n "weld_workcell_job_window|manipulation_skill_asset_evidence|equipment_timeseries_observation_package|manufacturing_event_context_package|ManipulationSkillAsset|不可提交|生产 connector" docs/profiles
```

Expected: all key profile IDs and boundaries appear.

- [ ] **Step 8: Commit**

```bash
git add docs/profiles
git commit -m "docs: add industrial physical ai profile contracts"
```

## Task 2: Stage 7 A01 H300 Docs

**Files:**
- Modify: `docs/stage7/README.md`
- Modify: `docs/stage7/sample_request_checklist.md`
- Modify: `docs/stage7/raw_clean_zone_pilot.md`
- Create: `docs/stage7/h300_weld_workcell_field_alignment.md`

- [ ] **Step 1: Update Stage 7 README title and positioning**

Change the title to:

```markdown
# Stage 7.1 A01 H300 最小焊接作业窗口数据试点
```

The opening must say:

- Stage 7.1 承接 Stage 7 simulated Raw/Clean fixture。
- 当前没有真机接入条件，所以 simulated fixture 仍是默认可运行路径。
- 本阶段第一样板是 A01 H300 最小作业窗口。
- `WeldWorkcellPackageImporter` 是 Clean Zone offline importer contract，不是 production connector。

- [ ] **Step 2: Update minimum window section**

Ensure the minimum H300 window includes:

- `job_window_id`
- `work_order_id`
- `task_id`
- `part_id`
- `seam_id`
- 3-10 seconds window
- point cloud/image references
- robot pose
- camera pose/calibration
- process parameters
- model output
- human correction
- execution event/exception
- quality result

- [ ] **Step 3: Add profile and field alignment reading order**

Add links to:

- `../profiles/a01_weld_workcell_job_window.md`
- `../profiles/b06_to_a02_evidence_handoff.md`
- `h300_weld_workcell_field_alignment.md`

- [ ] **Step 4: Rewrite sample request checklist for A01 H300**

Update `docs/stage7/sample_request_checklist.md` so “必需样本” includes:

- 作业任务元数据
- 工件/焊缝引用
- 点云
- 相机位姿
- 机器人位姿
- 标定参数
- 路径点
- PCL 输出
- 模型输出
- 人工修正
- 工艺参数
- 执行日志/异常/报警
- 质量结果

Keep the existing脱敏与权限 and submission guidance, but update wording from generic Stage 7 to A01 H300.

- [ ] **Step 5: Update Raw/Clean Zone pilot**

Modify `docs/stage7/raw_clean_zone_pilot.md` to:

- mention A01 H300 in the title/opening
- make Raw Zone examples H300-oriented
- clarify true/desensitized/synthetic/temporary/non-committable data classes
- keep current clean contract files unchanged

- [ ] **Step 6: Create H300 field alignment doc**

Create `docs/stage7/h300_weld_workcell_field_alignment.md` with sections:

- purpose and boundary
- existing `WeldWorkcellPackageImporter` input contract
- H300 -> clean contract table:

| H300 group | Clean contract target | Current handling |
| --- | --- | --- |
| work order/task/job window | `job.json` | direct/minimal metadata |
| part/seam | `job.json`, source artifacts | direct ids, geometry as source artifact |
| TCP pose | `frames.csv` | direct |
| camera image reference | `frames.csv.image_path` | direct reference/copy policy |
| point cloud | source artifact for now | no package schema change this round |
| process parameters | `process.csv` | mapped to metrics |
| execution events/exceptions | `events.csv` | direct |
| human correction/review | `review_labels.csv`, source artifact | labels plus source retention |
| PCL/model outputs | source artifact/context | decide after sample review |
| quality result | `review_labels.csv` or source artifact | labels if frame/window-level |

- gap decision table:
  - importer evolution
  - cleaning script
  - connector skeleton
  - package schema extension
  - DB/schema

- [ ] **Step 7: Self-review**

Run:

```bash
rg -n "H300|A01|job_window_id|PCL|模型输出|人工修正|质量结果|WeldWorkcellPackageImporter|不是生产 connector|未脱敏真实数据" docs/stage7
```

Expected: terms appear in relevant docs.

- [ ] **Step 8: Commit**

```bash
git add docs/stage7
git commit -m "docs: align stage 7 with a01 h300 pilot"
```

## Task 3: README and Details Alignment

**Files:**
- Modify: `README.md`
- Modify: `details.md`

- [ ] **Step 1: Rewrite README opening**

Replace the current first definition with:

```markdown
# 工业物理 AI 数据层

B06 是公司工业物理 AI 的横向数据底座项目，目标是在机器人、智能工站、设备时序和系统级协同项目中统一作业数据包、Raw/Clean Zone、回放、训练/评测导出、数据治理和审计边界，使真实物理过程可观察、可复盘、可训练、可追溯。当前第一优先级是支撑 A01 智能焊接工站形成 H300 最小作业窗口数据闭环，并将其中可用证据交给 A02 技能资产底座。
```

- [ ] **Step 2: Reorder README front page**

The top half of README should include sections in this order:

1. 项目定位
2. 主链路
3. 当前第一样板
4. 当前可用能力
5. 四类项目 profile
6. 工程对接方式
7. 当前边界
8. 快速开始 / 常用命令

Keep historical route planning and document directory after the front page.

In the 主链路 section, use a shared upstream chain followed by profile-specific consumption. Do not write a single line implying all four projects consume the same training/evaluation draft:

```text
Raw Zone
-> Clean Zone
-> Physical AI Package
-> Rerun 回放
-> candidate sample export
-> training/evaluation draft
   - A01: job-window evidence / field-alignment references
   - A02: ManipulationSkillAsset evidence handoff
   - B08: timeseries observation candidates / result references
   - S01: manufacturing event context / evidence references
```

- [ ] **Step 3: Add profile links**

Add links to:

- `docs/profiles/README.md`
- `docs/profiles/a01_weld_workcell_job_window.md`
- `docs/profiles/a02_manipulation_skill_asset_evidence.md`
- `docs/profiles/b08_equipment_timeseries_observation_package.md`
- `docs/profiles/s01_manufacturing_event_context_package.md`
- `docs/profiles/b06_to_a02_evidence_handoff.md`

- [ ] **Step 4: Update README Stage 7 route and outputs**

Change Stage 7 references from generic “仿真优先小作业窗口” to “Stage 7.1 A01 H300 最小焊接作业窗口数据试点” while preserving that simulated Raw/Clean fixture remains the runnable path.

Do not claim real H300 data exists.

- [ ] **Step 5: Update details**

Append a `2026-06-22` section under 当前完成事项 with:

- strategic repositioning to 工业物理 AI 数据层
- Stage 7.1 decision
- profile docs
- A01 H300 sample request and field alignment
- B06 -> A02 handoff
- verification result placeholder to be filled after final verification

Update 下一步计划 to Stage 8:

1. 用真实/脱敏 A01 H300 最小窗口替换 simulated Raw Zone。
2. 评审字段、时间戳、坐标系、权限、脱敏和 AI 控制器存储位置。
3. 决定 importer/清洗流程、connector skeleton、DB/schema 或 package schema 是否需要变化。
4. 将可确认 evidence 交给 A02 做 `ManipulationSkillAsset` 候选证据。

- [ ] **Step 6: Self-review**

Run:

```bash
rg -n "工业物理 AI 数据层|A01|H300|A02|B08|S01|weld_workcell_job_window|不是通用 IoT|生产 connector|真实/脱敏|仿真" README.md details.md
```

Expected: README and details reflect the new positioning and boundaries.

- [ ] **Step 7: Commit**

```bash
git add README.md details.md
git commit -m "docs: reposition b06 as industrial physical ai data layer"
```

## Task 4: Final Verification and Consistency Pass

**Files:**
- Verify all changed docs.

- [ ] **Step 1: Inspect git status**

Run:

```bash
git status --short --branch
```

Expected: branch is `codex/stage-7-1-strategy-profile-alignment`; only intended docs changed or no uncommitted changes after prior task commits.

- [ ] **Step 2: Check strategic terms**

Run:

```bash
rg -n "工业物理 AI 数据层|Raw Zone|Clean Zone|Physical AI Package|weld_workcell_job_window|manipulation_skill_asset_evidence|equipment_timeseries_observation_package|manufacturing_event_context_package|H300|ManipulationSkillAsset" README.md details.md docs/profiles docs/stage7
```

Expected: key strategic and profile terms are present.

- [ ] **Step 3: Check no accidental real-data language**

Run:

```bash
rg -n "已接入真实|生产 connector 已实现|正式 DB schema|MES.*直连已完成|PLC.*直连已完成" README.md details.md docs/profiles docs/stage7
```

Expected: no matches.

- [ ] **Step 4: Run default tests**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 5: Final doc review**

Manually inspect:

```bash
sed -n '1,220p' README.md
sed -n '1,220p' docs/stage7/README.md
sed -n '1,220p' docs/profiles/README.md
```

Expected:

- README front page is not dominated by historical Rerun narrative.
- Stage 7 is A01 H300-first but honest about simulated fixture.
- Profiles read as contracts, not implemented schemas.

- [ ] **Step 6: Commit final fixes if needed**

If any consistency fixes are needed:

```bash
git add README.md details.md docs/profiles docs/stage7
git commit -m "docs: polish stage 7 1 alignment"
```

If no changes are needed, do not create an empty commit.
