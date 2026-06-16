# Stage 7 仿真优先小作业窗口数据试点设计

## 1. 背景

Stage 6 已经把项目主线从离线 handoff 推进到 AI 控制器侧真机数据接入与数据资产化。当前已明确 Raw Zone、Clean Zone、Physical AI Package、Rerun replay 和 training/evaluation draft 的关系，也明确了真机字段分层、字段优先级和待确认问题。

下一阶段原建议是进入“真实/脱敏小作业窗口数据试点”：收集 SDK/TCP JSON/文件/DB payload 示例，确认 AI 控制器上的 Raw Zone / Clean Zone 存储位置、权限和脱敏边界，选择一个最小焊接作业窗口，再用真实样本决定是否需要 connector skeleton、package schema 扩展、数据库 schema，或只需要演进 importer/清洗流程。

当前约束是：还不具备真机接入条件。因此 Stage 7 不应假装已经有现场协议，也不应继续只写大文档。更合适的方向是做一个 **仿真优先的小作业窗口试点准备层**：用确定性仿真样本模拟真实 SDK/TCP JSON/文件 payload 的样貌，明确真实样本到来后应放在哪里、如何脱敏、如何进入 Clean Zone、如何复用现有 `weld_workcell` importer 生成 Physical AI Package。

## 2. 已有基础

当前项目已经具备以下能力：

- Physical AI Package v0.1 schema、validator、summarize、candidate export、training/evaluation draft export 和 Rerun `.rrd` adapter。
- deterministic welding simulation package generator，可生成机器人焊接工站 package。
- `WeldWorkcellPackageImporter`，可把本地离线焊接工站导出目录转换成 `robot_welding_station` package。
- Stage 6 文档已定义 AI 控制器侧 Raw Zone、Clean Zone、Physical AI Package 的职责边界。
- Stage 6 字段映射已给出第一轮 P0/P1/P2 字段与待确认问题。

这些能力说明 Stage 7 不需要从零设计数据包，也不需要立即扩展 schema。Stage 7 的核心缺口是：缺少一个面向“小作业窗口”的样本收集、仿真 fixture、Raw/Clean 目录约定和决策记录机制。

## 3. 目标

Stage 7 的目标是建立一个最小、可运行、可替换真实样本的试点框架：

1. 定义最小焊接作业窗口的范围和成功标准。
2. 规定真实或脱敏样本应如何进入 `docs/real-data` 或本地 `artifacts`，以及哪些内容不能入库。
3. 新增一个仿真 Raw/Clean fixture，用来模拟真实 SDK/TCP JSON、文件同步和过程记录 payload。
4. 让仿真 Clean Zone 可以生成现有 `weld_workcell` importer 接受的离线业务目录，再复用现有链路生成 Physical AI Package。
5. 通过真实样本评审清单决定后续是否需要 connector skeleton、package schema 扩展、数据库 schema，或只需要演进 importer/清洗流程。

本阶段成功后，团队应能在没有真机的情况下跑通“Raw 样本窗口 -> Clean 工作目录 -> Physical AI Package -> validate/summarize/candidates/training draft/Rerun”的最小闭环；真实样本到来后，则替换 Raw Zone 输入并记录缺口。

职责边界上，`docs/real-data` 只记录样本请求、脱敏说明、截图索引和样本评审记录；可生成或可替换的仿真/脱敏 fixture 放在本地 `artifacts/stage7/...` 下，不把未脱敏真实数据提交入库。

## 4. 非目标

Stage 7 不做：

- 不实现生产 connector、TCP/IP server、SDK bridge、OPC UA/MES/HMI 直连。
- 不固定长期数据库 schema。
- 不扩展 Physical AI Package v0.1 schema，除非真实样本评审证明现有 schema 无法承接最小窗口。
- 不定义正式训练数据集格式。
- 不把仿真 payload 当成现场协议。
- 不提交客户敏感原始数据、真实图片、真实设备标识或无法脱敏的日志。
- 不 fork Rerun、不二次开发 Rerun、不自研 viewer。

## 5. 关键假设

- 第一轮试点选择单个焊接作业窗口，而不是完整工单生命周期。
- 作业窗口粒度建议为一次焊缝或一个焊接阶段片段，覆盖 3 到 10 秒数据即可。
- 最小窗口必须包含任务上下文、机器人 TCP 或轨迹、至少一类图像引用、焊接过程指标、事件或异常记录。
- 真实样本未到位前，用 deterministic 仿真生成 Raw/Clean fixture；真实样本到位后，优先补充样本评审记录，而不是立即写 connector。
- AI 控制器上的生产存储路径暂不写死；仓库内只记录建议目录形态和脱敏边界。

## 6. 方案比较

### 方案 A：仿真优先的小作业窗口试点

用现有焊接仿真能力生成一个 Raw Zone 样本窗口和 Clean Zone 业务目录。Raw Zone 模拟 SDK/TCP JSON、文件同步、过程记录和事件 payload；Clean Zone 收敛成现有 `weld_workcell` importer contract。文档记录真实样本收集要求、脱敏规则和后续决策表。

优点：不依赖真机；可以验证 Stage 6 的 Raw/Clean/Package 关系；不会过早固化协议；能保持默认项目可运行。缺点：仿真样本不能替代真实协议细节，后续仍需真实样本校准。

### 方案 B：直接设计 connector skeleton

提前建立 SDK/TCP JSON/DB connector skeleton，给后续真机接入预留代码结构。

优点：看起来更接近工程接入。缺点：目前没有真实 payload、错误模型、部署约束和权限边界，容易产生伪接口；也可能把团队引向过早的 connector 抽象。

### 方案 C：只继续补充 Stage 7 文档

只写样本收集说明、权限说明和下一步计划，不新增仿真 fixture 或脚本。

优点：风险最低。缺点：无法验证 Raw/Clean/Package 的最小闭环，容易停留在规划层，不能为真实样本到来后的落地提供足够抓手。

## 7. 选定方案

采用 **方案 A：仿真优先的小作业窗口试点**。

理由：

- 它最贴近“真机条件未具备，可从仿真做起”的现实约束。
- 它不会继续扩大文档规模，而是补一个可运行的最小数据窗口。
- 它能检验 Stage 6 的 Raw Zone / Clean Zone / Physical AI Package 分层是否清晰。
- 它复用现有 `WeldWorkcellPackageImporter`，避免提前发明 connector 或 schema。
- 它为后续真实/脱敏样本接入留下明确评审口径。

## 8. 最小作业窗口定义

Stage 7 的最小焊接作业窗口定义为：

- 一个 `work_order_id`、一个 `part_id`、一个 `seam_id`、一个 `task_id`。
- 时间范围建议 3 到 10 秒，覆盖 approach、weld、cooldown 或等价阶段。
- 至少 3 帧机器人 TCP 位姿。
- 至少 1 张 2D 图像引用；点云可选。
- 至少 1 条焊接过程指标记录，包含电流、电压、速度、送丝或气体中的若干项。
- 至少 1 条事件或异常记录。
- 必须记录时间戳来源、字段单位假设、坐标系假设和脱敏状态。

这个窗口不是完整生产作业，也不是训练数据集。它只是用于验证 Raw -> Clean -> Package 的最小样本单元。

## 9. Raw Zone 试点约定

仓库中可提交的 Raw Zone 只能是仿真或已脱敏样本。真实敏感数据默认不入库。

建议仿真 Raw Zone 目录形态：

```text
artifacts/stage7/sim_weld_window/raw/
  manifest.raw.json
  sdk/
    robot_state.ndjson
  tcp_json/
    hmi_task_messages.ndjson
  files/
    robot_program.lua
    robot_trajectory.json
    seam_trajectory.json
    images/front_0000.png
  process/
    welding_process.csv
  events/
    event_log.ndjson
```

其中：

- `manifest.raw.json` 记录样本来源、生成方式、脱敏状态、窗口时间范围和字段假设。
- `sdk/robot_state.ndjson` 模拟 SDK 或机器人控制器状态流。
- `tcp_json/hmi_task_messages.ndjson` 模拟 HMI 或调度中台 JSON 消息。
- `files/` 模拟文件同步来的程序、轨迹、图像或点云。
- `process/welding_process.csv` 模拟焊机、送丝、气体和工艺过程记录。
- `events/event_log.ndjson` 模拟报警、异常、阶段切换或人工复核事件。

这些文件是 Raw Zone 仿真 fixture，不是生产协议。

## 10. Clean Zone 试点约定

Clean Zone 负责把 Raw Zone 统一成现有 `weld_workcell` importer contract：

```text
artifacts/stage7/sim_weld_window/clean/weld_workcell/
  job.json
  frames.csv
  process.csv
  events.csv
  review_labels.csv
  images/front_0000.png
```

Clean Zone 最小职责：

- 统一任务上下文：`work_order_id`、`station_id`、`robot_id`、`welder_id`、`part_id`、`seam_id`、`task_name`、`created_at`。
- 统一时间单位为秒。
- 将机器人 TCP 位姿写入 `frames.csv`。
- 将焊接电流、电压、送丝、气体、行走速度和缺陷概率写入 `process.csv`。
- 将阶段切换、异常或人工标记写入 `events.csv` 或 `review_labels.csv`。
- 保留图片为相对路径，避免绝对路径污染 package。

Stage 7 不新增 package schema；Clean Zone 应优先适配现有 importer contract。

## 11. 样本收集与脱敏边界

真实或脱敏样本到来前，Stage 7 文档应给工程团队一份样本请求清单：

- SDK/TCP JSON 示例：至少 5 到 20 条，保留字段结构，脱敏工单、设备、人员和客户信息。
- 文件样例：轨迹 JSON、焊缝 JSON、程序文件、图片/点云命名规则；真实图片如含敏感现场信息应不入库或只给脱敏缩略图。
- DB 样例：如果现场使用 DB 写入，先提供表结构和 3 到 5 行脱敏样例，不急于设计正式 DB schema。
- 时间戳说明：每个数据源的时间戳来源、单位、时区或单调时钟规则。
- 坐标系说明：机器人 base、TCP、相机、工件、焊缝之间的关系。
- 权限说明：Raw Zone、Clean Zone、Package、Rerun `.rrd` 和 training draft 在 AI 控制器上的读写主体。

仓库只提交脱敏后的结构性样例和评审记录；未脱敏的真实数据留在现场或受控存储中。

## 12. 后续决策口径

真实或脱敏样本评审后，按以下口径决定下一步：

| 观察结果 | 下一步 |
| --- | --- |
| 样本只需字段清洗和文件整理即可进入现有 `weld_workcell` contract | 演进 importer/清洗流程，不做 connector skeleton |
| 样本来源稳定为本地文件同步或周期性导出 | 先做 file-based importer 或清洗脚本 |
| 样本来源稳定为 TCP JSON 且需要在线/准在线接收 | 再考虑 TCP connector skeleton |
| 样本来源稳定为 SDK 且 SDK 生命周期、错误模型清楚 | 再考虑 SDK bridge |
| 现场必须使用 DB 写入且表结构稳定 | 再设计最小 DB schema 或 DB ingestion adapter |
| 现有 Physical AI Package 无法表达关键实体或时序 | 提出 package schema 扩展 spec |
| 主要缺口是权限、脱敏或保留策略 | 优先补数据治理文档和 AI 控制器部署边界 |

Stage 7 的默认判断是：先演进 Raw/Clean/importer 链路，只有真实样本证明必要时才新增 connector 或 schema。

## 13. 交付物

Stage 7 应交付：

- `docs/superpowers/specs/2026-06-16-stage-7-simulated-small-job-window-pilot-design.md`
- `docs/superpowers/plans/2026-06-16-stage-7-simulated-small-job-window-pilot.md`
- `docs/stage7/README.md`
- `docs/stage7/sample_request_checklist.md`
- `docs/stage7/raw_clean_zone_pilot.md`
- 一个可生成仿真小作业窗口 Raw/Clean fixture 的脚本。
- 对应测试，验证 fixture 可以通过现有 `WeldWorkcellPackageImporter` 生成 package，并继续进入 validate、candidate export、training draft 和 Rerun adapter。
- 更新 `README.md` 与 `details.md`，说明 Stage 7 的定位、完成事项和下一阶段计划。

## 14. 验收标准

- 新读者能从 README 看到 Stage 7 当前主线：真机未到位前的仿真优先小作业窗口试点。
- 工程团队能从 Stage 7 文档知道真实/脱敏样本应提供什么、哪些不能入库、哪些信息必须说明。
- 仿真 Raw/Clean fixture 可由命令生成，并且输出 Clean Zone 的 `weld_workcell` 目录。
- 生成的 Clean Zone 可通过现有 `WeldWorkcellPackageImporter` 转成 Physical AI Package。
- 生成 package 可通过 validate、summarize、export-candidates、export-training-draft 和 convert-rerun。
- 针对性测试覆盖 fixture 生成与 importer 链路，最终再运行全量测试。
- 全量测试仍通过。

## 15. 风险与缓解

- 风险：仿真 payload 被误认为真实协议。缓解：在脚本输出、文档和 manifest 中明确标记 `simulated` 和 `not_production_protocol`。
- 风险：Stage 7 过度设计为 connector 平台。缓解：只做 fixture generator 和文档，不新增在线服务。
- 风险：真实样本到来后现有 schema 不够。缓解：保留评审决策表，基于真实缺口另起 schema 扩展 spec。
- 风险：真实数据脱敏边界不清。缓解：样本请求 checklist 明确“未脱敏不入库”，并把权限/脱敏作为 Stage 8 的优先项之一。

## 16. 下一阶段建议

Stage 7 完成后，下一阶段建议进入 **Stage 8：真实/脱敏样本替换与缺口评审**。

Stage 8 不应默认写生产 connector，而应先用 1 个真实或脱敏焊接作业窗口替换 Stage 7 的仿真 Raw Zone，记录字段缺口、时间对齐缺口、权限/脱敏缺口和 package 表达缺口。只有当缺口稳定且不可由 importer/清洗流程解决时，才进入 connector skeleton、DB schema 或 package schema 扩展。
