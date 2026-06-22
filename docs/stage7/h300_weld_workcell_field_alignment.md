# H300 Weld Workcell Field Alignment

## 目的与边界

本文用于把 A01 H300 最小焊接作业窗口字段对齐到现有 `weld_workcell` Clean Zone contract。当前没有真机接入，Stage 7 simulated fixture 仍是默认可运行替代输入；真实或脱敏样本到来后，先做字段落点和 gap 评审，再决定是否演进 importer、connector 或 schema。

本文只定义 Clean Zone offline importer contract 的字段落点。`WeldWorkcellPackageImporter` 不是生产 connector，不承担 SDK、TCP、DB、OPC UA、HMI 或 MES 在线接入职责。

## 现有输入 contract

`WeldWorkcellPackageImporter` 当前只结构化读取现有 `weld_workcell` contract 中的有限字段。H300 新字段可以先随 source artifact 保留，但不能被理解为已经进入 importer 的结构化字段。

当前结构化输入如下：

- `job.json` 必需字段：`work_order_id`、`station_id`、`robot_id`、`welder_id`、`part_id`、`seam_id`、`task_name`、`created_at`。
- `frames.csv` 必需列：`timestamp_s`、`phase`、`tcp_x`、`tcp_y`、`tcp_z`、`tcp_qx`、`tcp_qy`、`tcp_qz`、`tcp_qw`、`image_path`。
- `process.csv` 必需列：`timestamp_s`、`weld_current_a`、`weld_voltage_v`、`wire_feed_mpm`、`gas_flow_lpm`、`travel_speed_mm_s`、`defect_probability`。
- `events.csv` 必需列：`timestamp_s`、`event_type`、`severity`、`message`、`object_id`。
- `review_labels.csv` 可选列：`timestamp_s`、`label_type`、`value`、`confidence`。
- `images/`：只通过 `frames.csv.image_path` 引用图片；当前 importer 不读取点云、相机位姿/标定、PCL 文件或模型输出文件。

## H300 到 Clean Contract 对齐表

| H300 字段或样本 | 当前落点 | 当前处理 |
| --- | --- | --- |
| `work_order_id` | `job.json.work_order_id` | 已结构化读取。 |
| `part_id` | `job.json.part_id` | 已结构化读取。 |
| `seam_id` | `job.json.seam_id` | 已结构化读取；焊缝几何暂留 source artifact。 |
| H300 工位/设备引用 | `job.json.station_id`、`robot_id`、`welder_id` | 已结构化读取到现有设备字段。 |
| 任务名称/阶段 | `job.json.task_name`、`frames.csv.phase` | `task_id` 暂不结构化读取，可留 source artifact。 |
| 机器人 TCP 位姿 | `frames.csv` 必需 TCP 列 | 已结构化读取；完整 trajectory 作为 source artifact。 |
| 图像引用 | `frames.csv.image_path`、`images/` | 已支持相对路径引用和可选复制。 |
| 工艺参数 | `process.csv` 现有必需列 | 已映射为 package metrics；H300 额外工艺参数暂留 source artifact。 |
| 执行事件/异常/报警 | `events.csv` | 已结构化读取现有事件列。 |
| 人工复核标签 | `review_labels.csv` | 已结构化读取 label 类型、值和置信度；复核人/状态暂留 source artifact。 |
| `job_window_id` | source artifact | 当前不在 `job.json` 必需字段中；真实样本后决定是否结构化。 |
| `task_id` | source artifact | 当前不在 `job.json` 必需字段中；真实样本后决定是否结构化。 |
| 点云引用 | source artifact | 当前 importer 不读取 `point_cloud_ref`；真实样本后决定是否扩展清洗流程或 package schema。 |
| 相机位姿/标定 | source artifact | 当前 importer 不读取相机位姿或标定文件；先保留引用和版本。 |
| 路径点/规划路径/修正路径 | `frames.csv` TCP 摘要 + source artifact | 当前只结构化读取每帧 TCP；完整路径文件先保留。 |
| PCL 输出 | source artifact | 当前不结构化读取；可在评审记录中摘要，不写成已支持列。 |
| 模型输出 | source artifact 或 `review_labels.csv` 摘要 | 只有人工确认后的摘要可进入 label；完整模型输出暂留 source artifact。 |
| 质量结果 | `process.csv.defect_probability` 或 `review_labels.csv` | 过程质量概率和人工标签可结构化；完整质检报告暂留 source artifact。 |

## Gap Decision Table

| Gap | 默认决策 | 何时再决策 |
| --- | --- | --- |
| H300 真实字段名未知 | 先用 simulated fixture 字段和 profile 名称占位 | 拿到真实或脱敏样本后映射。 |
| `job_window_id`、`task_id` 是否需要结构化 | 先留 source artifact | 真实样本证明它们是跨包追溯主键时再扩展 importer。 |
| 点云/PCL 输出格式未知 | 先作为 source artifact 引用 | 真实样本证明需要按帧结构化时再扩展清洗流程。 |
| 相机标定结构未知 | 先在 source artifact 中保留文件引用和版本 | 标定文件稳定后再决定是否新增清洗字段或 package artifact 约定。 |
| 模型输出字段未知 | 先保留 source artifact，必要时写人工确认后的 label 摘要 | 模型版本、置信度和输出类型稳定后再细化列。 |
| 人工修正来源未知 | 先按 review label 记录 | 现场复核工具稳定后再决定清洗格式。 |
| 质量结果来源未知 | 先区分过程质量和人工质量评审 | 真实质检口径稳定后再决定落 `process.csv` 或 `review_labels.csv`。 |
| 需要在线接入 | 暂不实现生产 connector | 只有真实样本证明 SDK/TCP/DB 稳定且必要时再立项。 |
| 现有 contract 无法表达关键实体 | 暂不改 Physical AI Package schema | 真实样本证明无法通过 source artifact 表达时再写扩展 spec。 |

## 当前结论

A01 H300 的第一轮工作应保持在 Raw/Clean/importer 链路内，但要区分当前已结构化读取的 clean contract 和暂存的 H300 扩展语义：`job.json`、`frames.csv`、`process.csv`、`events.csv`、`review_labels.csv` 先满足现有 importer 必需字段；`job_window_id`、点云、相机标定、PCL、模型输出和完整路径文件先作为 source artifact 或评审摘要保留。真实样本后再决策，不把 simulated payload 当成现场协议，也不提交未脱敏真实数据。
