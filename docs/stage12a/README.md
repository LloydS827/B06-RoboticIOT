# Stage 12A H300 Static Engineering Project Discovery

Stage 12A 的目的，是在 H300 realtime API 到位前，先把本地静态工程包作为第一类 source artifact 做只读 discovery。它回答的是“这个目录里有什么、哪些结构值得后续映射、哪些内容必须继续 local-only”，而不是直接把它变成生产接入链路。

## 边界

Stage 12A 只做 SDK-first inspection 和脱敏结构记录：

- 读取本地 `data/H300/<local-project-run>` 这类受控目录。
- 输出可保存为评审附件的 redacted-safe JSON。
- 记录工程资产数量、文件角色、字段类别、敏感风险类型和 gap mapping 线索。
- 不复制图片、点云、Lua、工程 JSON 或其他原始内容。

Stage 12A 不做 production connector、DB/schema、realtime API、demo UI、Physical AI Package v0.1 schema 修改，也不把 H300 静态工程包自动转换成 `weld_workcell` Clean Zone。

## 静态工程包包含什么

当前观察到的 H300 静态工程包是一组工程模板资产，而不是实时过程采样。它通常包含：

- 工程主 JSON：工程信息、标定、相机、拍照位姿、路径规划、工艺过程、机器人和 runtime 结构。
- 相机/点云索引 JSON：图像、PCD 点云、相机位姿引用和 ROI。
- 图片：RGB JPEG，用于视觉建模或焊缝提取上下文。
- 点云：binary PCD 分片和可能存在的裸 xyz 文本点云。
- 焊缝 recipe：焊缝条目、类型、方向、焊接类型和几何摘要。
- 规划数据：`pathPlan` 和 `extractPathPlan`。
- 程序文件：Lua/ABB RAPID 风格的运动、焊接动作和目标点定义。
- Flow config：工艺或执行流程步骤。

这些资产可以为 Stage 8/11 gap register、A02 evidence handoff 和后续 realtime API 字段要求提供依据，但默认仍属于 Raw/source artifact。

## 计划 CLI

计划入口：

```bash
physical-ai-package inspect-h300-static path/to/project --json
```

其中 `path/to/project` 应指向本地受控 H300 静态工程包目录，例如 `data/H300/<local-project-run>`。CLI 的 JSON 输出应只包含脱敏路径模式、角色、扩展名、数量、媒体元数据、指令计数、风险 finding 类型和 gap mapping，不包含绝对路径、真实工程名、真实 basename、IP、port、operator/author/reviewer 值或原始文件内容。

## 输出解释

预期 JSON 输出按以下方向组织：

- `recognized`：目录是否像一个可识别的 H300 static engineering project。
- `project_info`：工程主 JSON 的 top-level keys、关键结构是否存在和相关 count。
- `files`：脱敏路径模式、扩展名、大小和角色猜测。
- `images`：图片数量、宽高和模式，不包含图片内容。
- `point_clouds`：PCD header 摘要，如 fields、points 和 data encoding，不读取 binary 点体。
- `text_point_clouds`：裸 xyz 文本点云的列数和行数口径，不输出坐标。
- `weld_seams`：焊缝 count 和类型分布。
- `path_plans`：规划条目 count。
- `lua_program`：`MoveAbsJ`、`MoveL`、`ArcMPL`、`Stop`、target/data 定义等计数。
- `flow_config`：flow step count 和基础类型摘要。
- `sensitivity_findings`：风险类型、字段名或脱敏路径模式，不包含敏感值。
- `gap_mapping`：Stage 8/11 gap register 的初步映射。

## Redaction Policy

Stage 12A 的默认输出必须可提交、可评审、可转发给内部工程评审，不依赖额外人工清理。规则如下：

- 不输出绝对路径或真实工程目录名。
- 不输出真实 URL、IP、port、设备地址或服务地址。
- 不输出真实工程 basename、工单号、时间戳片段或程序编号。
- 不输出 operator、author、reviewer、person-like 字段值。
- 不输出原始 Lua、工程 JSON payload、图片内容、点云坐标或 binary PCD 内容。
- 对可疑字段宁可标记为 review finding，也不误判为安全字段。
- 原始 `data/H300` 目录保持 local-only，并由 `.gitignore` 防止误提交。

## 与 Stage 12B / Stage 13 的关系

Stage 12A 输出结构 discovery 和脱敏摘要。

Stage 12B 可以基于这些结果判断是否需要 H300 static project to Clean Zone draft readiness，或只保留人工 mapping checklist。Stage 12B 的重点是决策哪些字段能进入 `weld_workcell` Clean Zone draft，哪些继续作为 Raw/source artifact。

Stage 13 等 realtime API 样例可用后，再补动态信息要求，包括时间戳、实时状态、事件、报警、过程参数、采样频率和 API payload 边界。Stage 13 不应重新定义静态工程包已澄清的全部字段，而应复用 Stage 12A/12B 的结构结论。

## 非目标

- 不提交 `data/H300` 原始工程数据、图片、点云、Lua、工程 JSON 或未脱敏内容。
- 不把报告格式转换做成 SDK 产品能力。
- 不实现 realtime API、production connector、TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连、DB ingestion 或长期 DB schema。
- 不建设 demo UI。
- 不自动把 H300 静态工程包转换成 `weld_workcell` Clean Zone。
- 不修改 Physical AI Package v0.1 schema。
- 不把本阶段观察到的静态结构声明为最终 H300 现场协议。
