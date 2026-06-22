# H300 Weld Workcell Field Alignment

## 目的与边界

本文用于把 A01 H300 最小焊接作业窗口字段对齐到现有 `weld_workcell` Clean Zone contract。当前没有真机接入，Stage 7 simulated fixture 仍是默认可运行替代输入；真实或脱敏样本到来后，先做字段落点和 gap 评审，再决定是否演进 importer、connector 或 schema。

本文只定义 Clean Zone offline importer contract 的字段落点。`WeldWorkcellPackageImporter` 不是生产 connector，不承担 SDK、TCP、DB、OPC UA、HMI 或 MES 在线接入职责。

## 现有输入 contract

`WeldWorkcellPackageImporter` 当前从 Clean Zone 读取以下文件：

- `job.json`：作业窗口上下文、工单/任务/工件/焊缝 ID、设备引用、时间范围和 source artifact。
- `frames.csv`：按时间排列的机器人位姿、相机位姿/标定引用、图像引用和点云引用。
- `process.csv`：焊接电流、电压、速度、送丝、气体、工艺参数和质量结果。
- `events.csv`：执行事件、阶段切换、异常、报警和外部日志摘要。
- `review_labels.csv`：模型输出、人工修正、人工复核标签和质量评审标签。
- `images/`：相对路径引用的图像文件；点云、PCL 输出和模型输出可先作为 source artifact 引用。

## H300 到 Clean Contract 对齐表

| H300 字段或样本 | Clean Zone 落点 | 说明 |
| --- | --- | --- |
| `job_window_id` | `job.json` | H300 最小窗口主键；真实样本后确认命名规则。 |
| `work_order_id` | `job.json` | 工单或脱敏工单 ID。 |
| `task_id` | `job.json` | 作业任务 ID，可同时保留任务阶段。 |
| `part_id` | `job.json` | 工件引用。 |
| `seam_id` | `job.json` | 焊缝引用，焊缝几何可通过 source artifact 指向原始文件。 |
| 3-10 秒窗口 | `job.json` | 记录 start/end time、时间戳来源和单位。 |
| 点云引用 | `frames.csv` | 使用相对路径；真实点云先留在受控存储或 source artifact。 |
| 图像引用 | `frames.csv`、`images/` | 小体量脱敏图片可进入 images；未脱敏真实图片不可提交。 |
| 机器人位姿 | `frames.csv` | TCP 或关节位姿，统一时间单位为秒。 |
| 相机位姿/标定 | `frames.csv`、source artifact | 位姿可按帧记录，标定文件先作为 source artifact 引用。 |
| 路径点 | `frames.csv`、source artifact | 关键路径点可落帧表，完整 trajectory 保留 source artifact。 |
| PCL 输出 | `review_labels.csv`、source artifact | 焊缝候选、坡口/边界识别或点云特征先保留引用。 |
| 模型输出 | `review_labels.csv`、source artifact | 记录模型版本、输入引用、输出和置信度。 |
| 人工修正 | `review_labels.csv` | 记录修正类型、修正值、原因和脱敏复核人标识。 |
| 工艺参数 | `process.csv` | 电流、电压、速度、送丝、气体、摆动、压力等。 |
| 执行事件/异常/报警 | `events.csv` | 阶段切换、执行日志、异常代码、报警和人工处理记录。 |
| 质量结果 | `process.csv`、`review_labels.csv` | 数值过程质量落 `process.csv`；人工质量评审落 `review_labels.csv`。 |

## Gap Decision Table

| Gap | 默认决策 | 何时再决策 |
| --- | --- | --- |
| H300 真实字段名未知 | 先用 simulated fixture 字段和 profile 名称占位 | 拿到真实或脱敏样本后映射。 |
| 点云/PCL 输出格式未知 | 先作为 source artifact 引用 | 真实样本证明需要按帧结构化时再扩展清洗流程。 |
| 相机标定结构未知 | 先在 source artifact 中保留文件引用和版本 | 标定文件稳定后再决定是否写入 `frames.csv` 固定列。 |
| 模型输出字段未知 | 先落 `review_labels.csv` 摘要和 source artifact | 模型版本、置信度和输出类型稳定后再细化列。 |
| 人工修正来源未知 | 先按 review label 记录 | 现场复核工具稳定后再决定清洗格式。 |
| 质量结果来源未知 | 先区分过程质量和人工质量评审 | 真实质检口径稳定后再决定落 `process.csv` 或 `review_labels.csv`。 |
| 需要在线接入 | 暂不实现生产 connector | 只有真实样本证明 SDK/TCP/DB 稳定且必要时再立项。 |
| 现有 contract 无法表达关键实体 | 暂不改 Physical AI Package schema | 真实样本证明无法通过 source artifact 表达时再写扩展 spec。 |

## 当前结论

A01 H300 的第一轮工作应保持在 Raw/Clean/importer 链路内：`job.json` 承载窗口上下文，`frames.csv` 承载时序位姿和图像/点云引用，`process.csv` 承载工艺参数和过程质量，`events.csv` 承载执行事件/异常/报警，`review_labels.csv` 承载模型输出、人工修正和质量评审。真实样本后再决策，不把 simulated payload 当成现场协议，也不提交未脱敏真实数据。
