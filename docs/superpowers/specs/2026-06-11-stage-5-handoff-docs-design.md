# Stage 5 业务接入与交付文档设计

## 1. 背景

Stage 2 到 Stage 4.4 已经完成 Physical AI 数据层的主要研发闭环：Rerun 本地技术评测、Physical AI Package v0.1、validator、candidate export、Rerun adapter、SDK wrapper、external importer contract、LeRobot importer、CSV recording fixture、training/evaluation draft export v0.2，以及第一个贴近业务的 `WeldWorkcellPackageImporter` candidate。

此时继续把下一步叫 Stage 4.5 会弱化阶段性质。现在的问题已经从“技术路线是否成立”转向“工程团队如何理解、接入、试用、验收这套系统”。因此下一阶段应进入 **Stage 5：业务接入与交付文档阶段**。

Stage 5 不是新增生产 connector，也不是直接做真实现场试点。真实机器人/工程团队接入需要线下协调、样本脱敏和接口确认；本分支应先产出可用于对接沟通的文档包，让工程团队知道需要准备什么、本系统能产生什么、如何验证接入是否成功。

## 2. 阶段目标

Stage 5 本轮目标是形成最小交付文档包：

- 更新项目根 README，让新读者能理解项目定位、当前能力、默认安装/验证方式和最小使用路径。
- 新增工程团队对接文档，说明接入前需要准备的数据、推荐导出结构、字段 contract、调用方式、产出物、验收命令和常见错误。
- 更新 `docs/stage4/README.md` 或新增 Stage 5 文档入口，避免 Stage 4 文档继续承载所有使用说明。
- 更新 `details.md`，记录 Stage 5 的阶段定位、完成事项、验证结果和下一阶段计划。
- 不引入真实业务数据、不新增 CLI、不扩展 package schema、不开始线下试点实施。

## 3. 方案比较

### 方案 A：Stage 5 交付文档包

新增 `docs/stage5/README.md` 和 `docs/stage5/engineering_handoff.md`，同时重写根 README 的当前状态与快速开始部分。

优点：直接解决用户当前问题；适合在代码仓库内完成；能为线下工程/机器人团队对接提供共同材料。缺点：不直接验证真实现场字段，需要后续线下样本补充。

### 方案 B：先进入真实小场景测试

拿真实或脱敏现场导出样本跑 `weld_workcell` importer，按结果修 contract。

优点：业务真实性最强。缺点：依赖线下协调、真实数据可用性和脱敏流程；当前分支容易被外部状态阻塞，不适合作为自主闭环任务。

### 方案 C：继续做 label schema / 产品功能

设计正式 label schema、人工复核状态、评估样本集，并扩展 package schema 或导出格式。

优点：推进产品能力。缺点：没有真实业务团队输入前容易过度设计；也会和本阶段“先让团队能对接”的目标错位。

## 4. 选定方案

采用 **方案 A：Stage 5 交付文档包**。

原因：

- 它把 Stage 2-4.4 的研发成果转化为对外可理解、可执行的材料。
- 它不依赖线下样本和团队排期，可以在本分支内完整交付、测试和合并。
- 它为后续真实小场景试点、label schema 决策和产品化路线提供对接依据。
- 它保持当前系统可用性，不破坏默认安装、测试和离线路径。

## 5. 文档产物

### 5.1 根 README 更新

README 应从“项目启动和研发路线记录”调整为更强的入口文档，新增或整理以下内容：

- 项目是什么：Physical AI 数据层，用于机器人/智能工站数据接入、整理、回放、评估和训练导出准备。
- 当前已具备什么能力：
  - Physical AI Package v0.1。
  - simulation sample 生成。
  - package validate / summarize / candidate export。
  - Rerun `.rrd` adapter。
  - SDK wrapper。
  - LeRobot importer。
  - CSV recording fixture。
  - Weld workcell importer candidate。
  - training/evaluation draft export v0.2。
- 快速开始：
  - 默认开发安装命令。
  - 全量测试命令。
  - 生成仿真 package 的最小命令。
  - validate / summarize / export-candidates / convert-rerun / export-training-draft 命令。
- 文档导航：
  - Stage 5 交付说明。
  - 工程团队对接文档。
  - Stage 4 importer 说明。
  - spec/plan 入口。
- 当前边界：
  - Rerun 是可替换 adapter backend，不是主数据结构。
  - `WeldWorkcellPackageImporter` 是业务 importer candidate，不是生产 connector。
  - 真实现场接入、权限审计、数据脱敏、MES/PLC/HMI 直连不在当前默认路径。

README 不应变成完整 API 手册；详细接入字段和对接流程放到 Stage 5 文档。

### 5.2 Stage 5 总览文档

新增：

```text
docs/stage5/README.md
```

内容包括：

- Stage 5 定位：业务接入与交付文档阶段。
- 面向对象：项目负责人、工程团队、机器人团队、算法/数据团队。
- 推荐阅读顺序。
- 当前系统能产生的交付物：
  - Physical AI Package。
  - `derived/candidates.csv`。
  - `derived/training_eval/samples.csv` 和 manifest。
  - Rerun `.rrd`。
  - validation / summary 输出。
- 最小验收流程：
  - 默认测试通过。
  - 一个 package 可 validate。
  - package 可 summarize。
  - package 可 export candidates。
  - package 可 export training draft。
  - package 可 convert Rerun `.rrd`。
- Stage 5 不做什么：不新增真实生产 connector、不做 GUI 人工验收、不扩 package schema、不接现场系统。

### 5.3 工程团队对接文档

新增：

```text
docs/stage5/engineering_handoff.md
```

这是本阶段最关键文档。它应能被工程/机器人团队拿去准备对接，内容包括：

#### 对接目标

- 让工程团队导出一份最小业务数据包。
- 让数据层 importer 转成 Physical AI Package。
- 让研发/算法/数据团队能用统一 package 做复盘、候选筛选和训练评估 draft 准备。

#### 工程团队需要准备什么

- 一次作业或一小段作业窗口。
- 任务上下文：工单、工位、机器人、焊机、工件、焊缝、任务名、创建时间。
- 帧级数据：时间戳、阶段、TCP 位姿、可选图片。
- 工艺参数：电流、电压、送丝速度、气体流量、行走速度、缺陷概率或质量评分。
- 事件记录：时间戳、事件类型、等级、消息、关联对象。
- 可选人工复核：标签类型、值、置信度、复核状态、复核人。

#### 推荐导出目录

沿用 Stage 4.4 `weld_workcell` contract：

```text
source_root/
  job.json
  frames.csv
  process.csv
  events.csv
  review_labels.csv
  images/
```

并说明哪些文件必需、哪些可选。

#### 字段 contract

列出 `job.json`、`frames.csv`、`process.csv`、`events.csv`、`review_labels.csv` 字段、是否必需、含义、示例和注意事项。

字段说明必须明确：

- 时间戳使用秒，数值必须 finite。
- 图片路径必须相对 `source_root`，不能绝对路径，不能包含 `..`。
- `events.csv.object_id` 只能为空，或等于 `job.json.part_id` / `job.json.seam_id` 的具体值，例如 `part_alpha`、`seam_root`；不能填写字面量 `part_id` 或 `seam_id`。
- `review_status` 和 `reviewer` 暂时保留在 source artifact，不进入 `labels.csv`。

#### 使用方式

给出 Python importer 示例：

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

并给出 package 后续验证/导出命令或 Python 调用。

#### 系统会产生什么

import 成功后立即产生：

- `physical_ai_manifest.json`
- `frames.csv`
- `events.csv`
- `labels.csv`
- `metrics.csv`
- `artifacts/source/`
- `artifacts/images/`
- `artifacts/trajectories/tcp_path.csv`

运行后续导出或转换命令后产生：

- `derived/candidates.csv`
- `derived/training_eval/`
- `.rrd`

#### 对接验收 checklist

至少包含：

- 源目录文件齐全。
- CSV header 符合 contract。
- 图片路径合法。
- import 成功。
- validate 无 error。
- summarize 能读出 frame/event/label/metric count。
- candidate export 成功。
- training draft export 成功。
- Rerun `.rrd` 写出成功。
- 记录所有字段缺口和现场系统无法提供的字段。

#### 常见错误

列出当前 importer 已测试的错误：

- 缺文件。
- 缺 job 字段。
- 缺 CSV 列。
- malformed CSV row。
- 非 finite 数值。
- 空 frames。
- 图片绝对路径、`..`、symlink escape、missing image。
- 未知 event object id。
- output_dir 与 source.root 相同。

#### 下一步对接会议建议

列出需要工程团队确认的问题：

- 实际数据源来自 HMI、机器人控制器、焊机、视觉系统还是上位机。
- 时间戳来源和同步方式。
- 图片/视频帧如何导出。
- 工艺参数采样频率。
- 事件和报警日志字段。
- 缺陷/质量评分来源。
- 数据脱敏和客户现场边界。

### 5.4 Stage 4 文档调整

`docs/stage4/README.md` 已承载 LeRobot、CSV fixture、Weld Workcell importer 细节。Stage 5 不应大幅重写 Stage 4 文档，只需增加一个提示：

- 若准备与工程团队对接，请优先阅读 Stage 5 engineering handoff。

### 5.5 details 更新

`details.md` 需要追加 2026-06-11 Stage 5 记录：

- 阶段命名从 Stage 4.x 切换到 Stage 5。
- 本轮完成的文档产物。
- 验证命令。
- 后续任务。

## 6. 非目标

Stage 5 本轮不做：

- 不新增 importer、CLI、SDK API 或 package schema 字段。
- 不接真实机器人、PLC、OPC UA、MES、HMI 或数据库。
- 不提交真实客户/现场数据。
- 不做 native Rerun GUI/Blueprint 人工验收。
- 不实现正式 label schema 或人工复核工作流。
- 不把 Rerun 变成主数据结构。
- 不把 `WeldWorkcellPackageImporter` 宣称为生产 connector。

## 7. 验证策略

本阶段主要是文档变更，但仍需保持项目可用性：

- `python -m pytest -q` 必须通过。
- 文档中的文件路径应真实存在或明确为示例路径。
- README 的快速开始命令必须对应现有 CLI。
- 工程对接文档中的字段 contract 必须与 `WeldWorkcellPackageImporter` 测试和 Stage 4.4 文档一致。
- 新增 docs 目录应被 README 索引。

## 8. 完成定义

Stage 5 本轮完成时应具备：

- 根 README 能让新读者快速理解项目、安装、运行测试、跑最小 package 流程。
- `docs/stage5/README.md` 能解释 Stage 5 的交付定位和验收流程。
- `docs/stage5/engineering_handoff.md` 能作为工程/机器人团队对接材料。
- `docs/stage4/README.md` 指向 Stage 5 对接文档。
- `details.md` 记录 Stage 5 完成事项、验证结果和下一阶段规划。
- 全量测试通过。

PR、远端合并和本地分支清理属于交付流程，本轮仍按项目维护约定执行。
