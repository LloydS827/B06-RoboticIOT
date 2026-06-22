# Stage 7.1 A01 H300 Raw/Clean Zone 试点约定

## 目录结构

Stage 7.1 面向 A01 H300 最小焊接作业窗口，当前使用 simulated Raw/Clean fixture 作为无真机接入条件下的默认可运行替代输入。仓库中可提交的 Raw Zone 只能是仿真或已脱敏样本；未脱敏真实数据不得提交。

建议 H300-oriented simulated Raw Zone 目录形态：

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
    pcl_seam_candidates.json
    model_outputs.json
    images/front_0000.png
    point_clouds/window_0000.pcd
  process/
    welding_process.csv
  events/
    event_log.ndjson
```

Clean Zone 负责收敛到现有 `weld_workcell` importer contract：

```text
artifacts/stage7/sim_weld_window/clean/weld_workcell/
  job.json
  frames.csv
  process.csv
  events.csv
  review_labels.csv
  images/front_0000.png
```

Clean Zone 文件列表保持 `job.json`、`frames.csv`、`process.csv`、`events.csv`、`review_labels.csv` 和 images。当前 `WeldWorkcellPackageImporter` 只结构化读取现有必需字段；H300 新字段可以先随 source artifact 或评审摘要保留，真实样本评审后再决定是否扩展 contract。

## Raw Zone

Raw Zone 保存原始形态或近似原始形态的样本。本阶段的默认 Raw Zone 是 H300-oriented 仿真 fixture，不是现场协议，也不代表生产 connector 输出。

- `manifest.raw.json`：记录样本来源、生成方式、窗口范围、脱敏状态、时间戳来源、字段单位和坐标系假设。
- `sdk/robot_state.ndjson`：模拟 SDK 或机器人控制器状态流。
- `tcp_json/hmi_task_messages.ndjson`：模拟 HMI 或调度系统的 JSON 消息。
- `files/robot_program.lua`：模拟机器人程序文件。
- `files/robot_trajectory.json`：模拟机器人轨迹文件。
- `files/seam_trajectory.json`：模拟焊缝轨迹文件。
- `files/pcl_seam_candidates.json`：模拟 PCL 输出、焊缝候选或点云特征。
- `files/model_outputs.json`：模拟模型输出、置信度、路径建议或质量预测。
- `files/images/front_0000.png`：模拟图像文件引用。
- `files/point_clouds/window_0000.pcd`：模拟点云文件引用。
- `process/welding_process.csv`：模拟焊机、送丝、气体和工艺过程记录。
- `events/event_log.ndjson`：模拟报警、异常、阶段切换或人工复核事件。

Raw Zone 的重点是保留来源语义和样本边界。真实样本到来后，应先替换 Raw Zone 输入并补充评审记录，而不是直接实现生产接入。

## Clean Zone

Clean Zone 负责把 Raw Zone 统一成现有 `weld_workcell` importer contract。它不改变 Physical AI Package schema，也不承担生产接入职责。

Clean Zone 最小职责分为两层。第一层是当前 importer 已结构化读取的字段：

- 统一现有任务上下文：`work_order_id`、`station_id`、`robot_id`、`welder_id`、`part_id`、`seam_id`、`task_name`、`created_at`。
- 统一时间单位为秒。
- 将机器人 TCP 位姿和图像相对路径写入 `frames.csv`。
- 将焊接电流、电压、送丝、气体、行走速度和缺陷概率写入 `process.csv`。
- 将执行事件、阶段切换、异常或报警写入 `events.csv`。
- 将人工复核标签写入 `review_labels.csv`。
- 图片使用相对路径，避免绝对路径污染 package。

第二层是 H300 目标字段的暂存和评审边界：

- `job_window_id`、`task_id`、完整 H300 payload、完整 trajectory、点云、相机位姿/标定、PCL 输出、模型输出和完整质检报告先作为 source artifact 或评审摘要保留。
- 当前 importer 不读取点云、相机位姿/标定、PCL 文件或模型输出文件；这些字段不应被写成已结构化支持。
- 真实/脱敏样本到位后，再决定是否需要清洗脚本、importer 扩展、package schema 扩展或 connector skeleton。

## 数据边界

- 真实样本：只能进入现场或受控存储，除非完成脱敏和权限确认。
- 脱敏样本：可以提交结构样例、字段说明和小体量替代文件，但必须移除客户、人员、设备序列号、现场路径和敏感画面。
- 仿真样本：可以作为当前默认可运行 fixture，用于验证 Raw/Clean/importer 链路。
- 临时 artifact：生成在 `artifacts/stage7/...`，默认不要求提交，必要时只提交可复现说明。
- 不可提交数据边界：未脱敏真实数据、真实大文件、真实图片背景、真实点云、完整数据库导出、现场密钥、账号、内网地址和未经授权的日志。

## 从 Clean Zone 到 Physical AI Package

Stage 7 的 Clean Zone 可以通过 `WeldWorkcellPackageImporter` 导入 Physical AI Package。这个路径用于离线试点、回归验证和真实/脱敏样本到来前的链路准备，不是生产 connector。

导入后，生成的 package 应继续复用现有能力进行验证、摘要、候选样本导出、training/evaluation draft 和 Rerun `.rrd` 转换。Stage 7 不实现生产 connector、TCP/IP server、SDK bridge、DB ingestion 或 package schema 变更。

## 后续决策表

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

## 暂不决定的问题

- 不决定生产 connector 的协议实现、错误模型、重连策略和部署方式。
- 不决定 TCP/IP server、SDK bridge、OPC UA/MES/HMI 直连实现。
- 不决定长期 DB schema。
- 不决定 Physical AI Package v0.1 schema 扩展。
- 不决定正式训练数据集格式。
- 不决定采样频率、插值策略或 payload 字段类型。
- 不把仿真 payload 当成现场协议。
- 不提交未脱敏真实数据。
