# H300 synthetic-to-real gap register

## 使用方式

这个 `gap register` 面向 Stage 8 之后的真实/脱敏 H300 样本替换评审。每一行都应在拿到样本后被关闭、拆分或升级为工程任务。Stage 8 当前只提供 synthetic fixture，不把 Raw Zone payload 当作现场协议，也不扩大 Clean Zone contract。

| Gap ID | Field/sample group | Stage 8 status | Current landing | Needed real/de-identified sample | Expansion trigger | Default next step |
| --- | --- | --- | --- | --- | --- | --- |
| G-001 | 真实 `job_window_id`、`task_id`、工单主键 | synthetic | `manifest.raw.json`、`h300_job_window_story.json`、`clean/weld_workcell/job.json` | 至少 1 个脱敏 H300 作业窗口，包含工单、任务、窗口主键的字段名、示例值和脱敏规则 | 真实系统存在多级工单、批次、返工或复检主键，且 Clean Zone 当前字段无法表达 | 由 A01/现场侧提供字段字典和一条脱敏样本，先映射到现有 `job.json`，不足再开 importer 扩展任务 |
| G-002 | 机器人 TCP/joint/state 采样频率与时间戳来源 | synthetic / importer_supported | `raw/sdk/robot_state.ndjson`、`clean/weld_workcell/frames.csv` | 控制器导出的 TCP、joint、state 原始片段，包含采样频率、时钟源、时区或单调时间说明 | 真实采样非等间隔、存在多时钟对齐或 joint 状态必须进入 package | 先记录真实时间戳口径和单位，验证 `frames.csv` 是否可承接最小 TCP pose |
| G-003 | 点云文件、PCL 输出、坐标系和标定版本 | source_artifact_only / missing_real_sample | `files/point_clouds/window_0000.pcd`、`pcl_seam_candidates.json` | 脱敏点云样本、PCL seam candidate 输出、坐标系名称、标定版本和生成工具版本 | A02 或 A01 需要把点云/PCL 作为可筛选字段，而不仅是附件引用 | 先以 attachment_reference 保留，评审是否需要 Clean Zone 新列或 package artifact metadata 扩展 |
| G-004 | 相机内外参、手眼标定和图像脱敏边界 | missing_real_sample | `front_0000.png` 仅作 synthetic image ref；Clean Zone 只有 `image_path` | 脱敏图像、相机内参、外参、手眼标定文件、敏感区域处理说明 | 真实图像需要按相机、标定版本或隐私级别检索 | 先确认图像是否可提交脱敏样本；不可提交时记录 onsite-only 路径和 hash 摘要 |
| G-005 | 模型输出版本、置信度、路径建议和质量预测 | source_artifact_only | `files/model_outputs.json` | 真实模型输出样例，包含模型名、版本、输入引用、输出坐标系、置信度、path suggestion 和 quality prediction | 模型输出需要参与候选样本筛选或训练/评测 draft | 先作为 Raw source artifact 旁路保留，评审是否映射到 labels、metrics 或候选导出列 |
| G-006 | 人工修正来源、审查工具、reviewer 和状态 | synthetic / partially importer_supported | `files/manual_corrections.json`、`clean/weld_workcell/review_labels.csv` | 脱敏人工审查记录，包含审查工具、reviewer 角色、状态流转、修正点和原因 | 真实 reviewer、版本、状态流转需要审计或进入 A02 evidence | 先把可公开字段落入 `review_labels.csv`，敏感身份只记录角色或匿名 ID |
| G-007 | 工艺参数单位、频率、缺失值和设备来源 | importer_supported / synthetic | `process/welding_process.csv`、`clean/weld_workcell/process.csv` | 焊机或 HMI 导出的电流、电压、送丝、气流、速度样本，包含单位、采样频率和缺失值规则 | 真实参数超出现有列，或需要多设备来源、质量码、插值策略 | 先对齐现有 `process.csv` 列；无法表达的字段放入 gap 子表，不立即扩 schema |
| G-008 | 异常、报警和执行日志字段 | importer_supported / synthetic | `events/event_log.ndjson`、`clean/weld_workcell/events.csv` | 真实报警/事件片段，包含事件码、严重级别、设备来源、清除时间和消息脱敏规则 | 事件码需要结构化查询，或事件生命周期不止单条消息 | 先映射最小 `events.csv`，补充报警码字典和 severity 对照表 |
| G-009 | 质量结果来源、检测口径、复核结论和 A02 evidence 可用性 | source_artifact_only / partially importer_supported | `files/quality_result.json`、`review_labels.csv` | 质量检测报告或脱敏结果，包含检测来源、缺陷定义、复核人角色、通过/失败口径 | 质量结果要成为 A02 技能 evidence 或训练标签的正式来源 | 先由 A01/A02 共同确认 evidence 可用口径，再决定是否提升为 Clean Zone 字段 |
| G-010 | AI 控制器 Raw/Clean/Package/rrd/candidates/draft 存储位置和权限 | missing_real_sample / future_decision | Stage 8 示例默认在 `artifacts/stage8/h300_synthetic_demo/` 或 `/tmp` | AI 控制器目录规范、用户权限、磁盘配额、保留周期、不可提交路径和审计要求 | 需要在控制器上长期运行、归档或跨团队读取 | 先形成离线目录约定；真实部署前由工程侧提供路径和权限矩阵 |
| G-011 | HMI/TCP JSON 消息结构和任务状态机 | source_artifact_only | `tcp_json/hmi_task_messages.ndjson` | 脱敏 HMI/TCP JSON 片段，包含 message type、状态机、错误码、重试或暂停语义 | 状态机需要驱动 Clean Zone 事件切片或 package lifecycle | 先作为 Raw Zone source artifact 评审，确认是否只映射成 `events.csv` |
| G-012 | 坐标系命名、工具中心点、工件 frame 与单位约定 | synthetic / future_decision | `pcl_seam_candidates.json`、`seam_trajectory.json`、`frames.csv` | 机器人 base、tool、camera、workpiece、seam 坐标系说明，包含单位和标定版本 | 多坐标系转换需要可复盘、可审计或影响路径 evidence | 先写入样本说明和 source refs；真实数据证明必要后再评审 package metadata 扩展 |

## 默认关闭规则

- 若真实/脱敏样本能落入现有 Clean Zone contract，优先只更新映射说明和测试 fixture，不新增抽象。
- 若字段只用于追溯或审查，优先保留为 Raw Zone source artifact 或 attachment_reference。
- 若字段影响候选筛选、训练/评测 draft、A02 evidence handoff 或审计复盘，再考虑 importer 或 package metadata 扩展。
- 若缺口涉及客户、工单、人员、设备身份、内网路径、未脱敏图像/点云或权限配置，默认归入 blocked，直到脱敏和访问边界被确认。
