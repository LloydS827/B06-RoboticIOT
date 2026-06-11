# Stage 6 Real Robot Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将项目从 Stage 5 离线 handoff 文档推进到 Stage 6 真机数据接入与数据资产化准备阶段，更新项目入口、Stage 文档、真实资料索引和阶段台账。

**Architecture:** 本阶段只做文档与资料索引，不新增生产 connector、数据库 schema、CLI、SDK API 或 Physical AI Package schema。Stage 6 文档负责主叙事：AI 控制器上的 Raw Zone、Clean Zone、Physical AI Package、Rerun 回放和训练数据集准备；Stage 5 文档保留离线 handoff contract，但明确其新角色是脱敏交换、回归测试和离线验收格式。

**Tech Stack:** Markdown、现有 Python/pytest 验证命令、现有 Physical AI Package CLI、`docs/real-data/1.jpg` 与 `docs/real-data/2.jpg`。

---

## File Structure

- Already created by spec task:
  - `docs/real-data/1.jpg`
  - `docs/real-data/2.jpg`
  - `docs/superpowers/specs/2026-06-11-stage-6-real-robot-ingestion-design.md`
- Create: `docs/real-data/README.md`
  - 说明两张截图的来源、用途、解读边界和后续补充材料。
- Create: `docs/stage6/README.md`
  - Stage 6 真机数据接入与数据资产化阶段总览。
- Create: `docs/stage6/real_robot_data_asset_module.md`
  - 面向产品、工程、机器人、算法团队的新模块定位说明。
- Create: `docs/stage6/real_data_field_mapping.md`
  - 基于两张截图的字段分层、优先级、目标位置和待确认问题。
- Modify: `README.md`
  - 将 Stage 6 主线加入项目定位、当前能力、路线、文档目录、当前边界和当前状态。
- Modify: `docs/stage5/README.md`
  - 增加 Stage 6 后的角色说明：Stage 5 离线 handoff contract 是脱敏交换、回归测试和离线验收格式。
- Modify: `docs/stage5/engineering_handoff.md`
  - 在对接目标和当前边界处补充 Stage 6 真机接入主线，不让读者误以为离线目录是唯一或最终接入方式。
- Modify: `details.md`
  - 记录 Stage 6 决策、完成事项、验证结果和下一阶段计划。

No changes planned:

- No production code.
- No test code.
- No connector/server/database/schema work.
- No formal training dataset format.

PR、远端合并和本地分支清理属于本轮交付流程，不属于产品文档完成定义；执行完成后仍按用户要求完成。

---

### Task 1: Real Data Evidence Index

**Files:**
- Create: `docs/real-data/README.md`

- [ ] **Step 1: Inspect real-data assets**

Run:

```bash
ls -l docs/real-data
```

Expected: `1.jpg` and `2.jpg` exist.

- [ ] **Step 2: Create real-data README**

Create `docs/real-data/README.md` with these sections:

- `# Stage 6 真机接入准备资料`
- `## 文件说明`
- `## 当前解读`
- `## 使用边界`
- `## 后续需要补充`

Required content:

- `1.jpg` is the current system communication / integration sketch.
- `2.jpg` is the current exportable robot/welding/camera/process/task field inventory.
- These files are Stage 6 planning evidence, not production protocol documentation.
- Do not infer exact payload schema, sampling frequency, database schema, or connector implementation from these screenshots alone.
- Future materials should include SDK/TCP JSON examples, file naming rules, DB tables if used, timestamp source, units, coordinate frames, storage path, and permission/desensitization rules.

- [ ] **Step 3: Verify references**

Run:

```bash
rg "1.jpg|2.jpg|Stage 6|真机" docs/real-data/README.md docs/superpowers/specs/2026-06-11-stage-6-real-robot-ingestion-design.md
```

Expected: both image names and Stage 6 references appear.

- [ ] **Step 4: Commit**

```bash
git add docs/real-data/README.md
git commit -m "docs: index Stage 6 real data evidence"
```

---

### Task 2: Stage 6 Documentation

**Files:**
- Create: `docs/stage6/README.md`
- Create: `docs/stage6/real_robot_data_asset_module.md`
- Create: `docs/stage6/real_data_field_mapping.md`

- [ ] **Step 1: Read the approved spec and Stage 5 docs**

Run:

```bash
sed -n '1,340p' docs/superpowers/specs/2026-06-11-stage-6-real-robot-ingestion-design.md
sed -n '1,180p' docs/stage5/README.md
sed -n '1,220p' docs/stage5/engineering_handoff.md
```

Use the spec as authoritative. Do not add connector implementation promises beyond the spec.

- [ ] **Step 2: Create `docs/stage6/README.md`**

Required sections:

- `# Stage 6 真机数据接入与数据资产化`
- `## 阶段定位`
- `## 为什么不是 Stage 5.1`
- `## 推荐阅读顺序`
- `## 数据链路`
- `## 当前产出物`
- `## MVP 边界`
- `## 验收方式`
- `## 下一步`

Must state:

- Stage 6 mainline is real robot ingestion into AI controller.
- Offline `weld_workcell` contract remains useful, but is no longer the primary story.
- Physical AI Package remains the primary standard data asset.
- Rerun remains a replaceable replay backend.
- This stage does not implement production connectors.

- [ ] **Step 3: Create `real_robot_data_asset_module.md`**

Required sections:

- `# 真机数据资产模块定位`
- `## 从素材模块到数据资产模块`
- `## 面向对象`
- `## 模块职责`
- `## 不属于本模块的职责`
- `## 与 Physical AI Package 的关系`
- `## 与 Rerun 的关系`
- `## 与独立产品路线的关系`
- `## 第一轮产品升级建议`

Must include:

- The module manages job context, robot data, camera data, welding data, process records, events, source artifacts, replay artifacts, and training/evaluation draft outputs.
- It is not a generic IoT platform, not a data lake, and not a final training framework.
- Rerun is not the product kernel; it is a replay backend behind an adapter.
- Independent product direction is reserved as a future Robot Data Recorder / Physical AI DataHub class, after a real/desensitized scenario proves value.

- [ ] **Step 4: Create `real_data_field_mapping.md`**

Required sections:

- `# 真机字段分层与映射`
- `## 资料来源`
- `## 优先级定义`
- `## 字段映射表`
- `## 第一轮必须确认的问题`
- `## 暂不决定的问题`

The mapping table must include rows for:

- 焊接机器人模型文件
- 深度相机资料
- 机械臂资料
- 焊机资料
- 机器人控制器中机械臂运行文件 `.lua`
- 机械臂轨迹文件 `.json`
- 关节实时角度/位置/速度/扭矩
- 机械臂末端笛卡尔坐标/欧拉角
- 焊缝轨迹文件 `.json`
- 深度相机点云
- 深度相机 2D 图像
- 深度相机拍照时位姿
- 下发焊接电压/电流/速度
- 焊枪焊接时位置
- 保护气体流量/浓度/压力
- 送丝速度/出丝长度
- 焊接过程记录
- 焊接工艺记录
- 焊接异常记录
- 焊机时间戳
- 工单 ID/工件编号
- 焊缝 ID/任务 ID
- 设备 ID/型号

Use P0/P1/P2 priority definitions from the spec. Do not invent exact units or sampling rates unless already shown in the screenshot/spec.

- [ ] **Step 5: Verify Stage 6 docs**

Run:

```bash
test -f docs/stage6/README.md
test -f docs/stage6/real_robot_data_asset_module.md
test -f docs/stage6/real_data_field_mapping.md
rg "Rerun|Physical AI Package|Raw Zone|Clean Zone|weld_workcell|不新增生产 connector|真机数据资产模块" docs/stage6
```

Expected: all files exist; search terms appear in relevant Stage 6 docs.

- [ ] **Step 6: Commit**

```bash
git add docs/stage6/README.md docs/stage6/real_robot_data_asset_module.md docs/stage6/real_data_field_mapping.md
git commit -m "docs: add Stage 6 real robot ingestion docs"
```

---

### Task 3: Project Entry and Stage 5 Cross-Link Updates

**Files:**
- Modify: `README.md`
- Modify: `docs/stage5/README.md`
- Modify: `docs/stage5/engineering_handoff.md`

- [ ] **Step 1: Inspect current entry docs**

Run:

```bash
sed -n '1,260p' README.md
sed -n '1,180p' docs/stage5/README.md
sed -n '1,260p' docs/stage5/engineering_handoff.md
```

- [ ] **Step 2: Update README**

Make focused updates only:

- In project positioning / current ability sections, add Stage 6 real robot ingestion and data assetization as the current direction.
- In `## 工程团队对接`, clarify that Stage 5 offline handoff remains available, but Stage 6 mainline is AI-controller-side real data ingestion, storage, cleaning, package generation, replay, and training data preparation.
- In route planning, change Stage 6 from generic “产品化与自研边界收敛” to “真机数据接入与数据资产化试点”.
- Add Stage 6 documents to the document directory.
- In current boundaries, preserve:
  - no production connector yet;
  - no TCP/IP server / SDK bridge / DB schema yet;
  - Rerun is replaceable replay backend;
  - Physical AI Package remains primary.
- In current status, add the Stage 6 docs and real-data screenshots.

Do not remove existing Stage 2-5 history.

- [ ] **Step 3: Update Stage 5 README**

Add a short section near the top or after Stage 5 positioning:

```markdown
## Stage 6 后的定位调整

Stage 5 的离线业务导出 contract 仍用于脱敏样本交换、回归测试、离线验收和字段 contract 对照。Stage 6 开始，主线转为真机数据通过接口进入 AI 控制器，在 AI 控制器上完成存储、清洗、整理、Physical AI Package 生成、Rerun 回放和训练数据集准备。
```

Keep Stage 5 docs valid for offline handoff.

- [ ] **Step 4: Update engineering handoff**

Add short notes to:

- `## 对接目标`: clarify this doc is the offline handoff format, not the only or final real-machine ingestion route.
- `## 当前边界`: link to Stage 6 docs for online/near-online ingestion planning.

Do not rewrite the field contract tables unless necessary.

- [ ] **Step 5: Verify links and positioning**

Run:

```bash
rg "Stage 6|真机数据接入|真机数据资产模块|docs/stage6|docs/real-data|可替换" README.md docs/stage5
test -f docs/stage6/README.md
test -f docs/stage6/real_robot_data_asset_module.md
test -f docs/stage6/real_data_field_mapping.md
test -f docs/real-data/README.md
```

Expected: Stage 6 links and positioning appear; files exist.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/stage5/README.md docs/stage5/engineering_handoff.md
git commit -m "docs: update project entry for Stage 6"
```

---

### Task 4: Details, Final Verification, and Branch Readiness

**Files:**
- Modify: `details.md`

- [ ] **Step 1: Inspect current details tail**

Run:

```bash
tail -n 120 details.md
```

- [ ] **Step 2: Update details**

Add a new `### 2026-06-11` entry after the Stage 5 entry or extend the existing same-date section with Stage 6 bullets. Required content:

- Stage 6 is now defined as 真机数据接入与数据资产化试点.
- Stage 6 decisions:
  - 真机接入优先；
  - 现有素材/数据模块升级为真机数据资产模块；
  - 独立产品路线预留；
  - Rerun remains replaceable replay backend, not forked/not primary product kernel/not self-built viewer in this stage.
- Added `docs/real-data/1.jpg`, `docs/real-data/2.jpg`, and `docs/real-data/README.md`.
- Added Stage 6 docs and plan/spec paths.
- Stage 6 does not add production connector, DB schema, TCP/IP server, SDK bridge, package schema changes, or formal training dataset format.
- Verification results from this branch.

Update `## 下一步计划` to Stage 7 or next cycle:

1. collect real SDK/TCP JSON/file/DB payload examples;
2. confirm AI controller Raw Zone / Clean Zone storage location and permissions;
3. choose one minimal welding job window;
4. define timestamp source, units, coordinate frames, sampling rates;
5. decide whether code needs connector skeleton, package schema extension, or only importer evolution.

- [ ] **Step 3: Run final docs sanity**

Run:

```bash
rg "Stage 6|真机数据接入|真机数据资产模块|Rerun|Raw Zone|Clean Zone|生产 connector|docs/stage6|docs/real-data" README.md details.md docs/stage5 docs/stage6 docs/real-data docs/superpowers/specs/2026-06-11-stage-6-real-robot-ingestion-design.md docs/superpowers/plans/2026-06-11-stage-6-real-robot-ingestion.md
```

Expected: references appear consistently; no missing-file errors.

- [ ] **Step 4: Run CLI verification**

Run:

```bash
rm -rf /tmp/stage6_demo_weld /tmp/stage6_demo_weld.rrd /tmp/stage6_validate.json /tmp/stage6_summary.json
python scripts/physical_ai_package.py generate welding --output-dir /tmp/stage6_demo_weld
python scripts/physical_ai_package.py validate /tmp/stage6_demo_weld --json >/tmp/stage6_validate.json
python scripts/physical_ai_package.py summarize /tmp/stage6_demo_weld --json >/tmp/stage6_summary.json
python scripts/physical_ai_package.py export-candidates /tmp/stage6_demo_weld
python scripts/physical_ai_package.py export-training-draft /tmp/stage6_demo_weld --split eval
python scripts/physical_ai_package.py convert-rerun /tmp/stage6_demo_weld --output-rrd /tmp/stage6_demo_weld.rrd
ls -l /tmp/stage6_demo_weld.rrd /tmp/stage6_demo_weld/derived/candidates.csv /tmp/stage6_demo_weld/derived/training_eval/samples.csv
```

Expected: every command exits 0 and the three output files exist.

- [ ] **Step 5: Run full tests**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add details.md
git commit -m "docs: record Stage 6 ingestion planning status"
```

---

## Final Review and Merge Preparation

After all tasks:

- Run `git status --short --branch`.
- Run `git diff --check HEAD`.
- Re-run the CLI verification chain from Task 4 if any docs command changed.
- Re-run `python -m pytest -q`.
- Request final review covering:
  - Stage 6 positioning;
  - README and Stage 5/6 consistency;
  - Rerun boundary;
  - no accidental production connector/schema promises;
  - links to `docs/real-data` and `docs/stage6`.
- Push branch, create PR, merge remotely, pull main, remove worktree, delete local/remote branch, and verify main still passes tests.
