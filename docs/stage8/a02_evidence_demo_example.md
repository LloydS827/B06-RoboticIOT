# B06 -> A02 evidence handoff synthetic example

## 定位

本文件只展示 Stage 8 H300 synthetic 作业窗口如何形成 A02 evidence handoff 示例。它不定义 A02 schema，不提供 converter，也不把 synthetic evidence 当作真实技能资产输入。

```yaml
handoff_name: stage8_h300_synthetic_a02_evidence_demo
synthetic_demo_only: true
source_package: artifacts/stage8/h300_synthetic_demo/package
source_raw_zone: artifacts/stage8/h300_synthetic_demo/raw
source_clean_zone: artifacts/stage8/h300_synthetic_demo/clean/weld_workcell
real_replacement_required: true
```

真实或脱敏 H300 样本到来后，需要替换 source refs、审查来源、质量口径和附件引用，再由 A01/A02 共同确认哪些内容可进入 A02 evidence handoff。

## evidence

| Evidence item | Stage 8 synthetic source | Why it may help A02 | Real-data replacement check |
| --- | --- | --- | --- |
| 人工确认轨迹片段 | `clean/weld_workcell/frames.csv`、`files/robot_trajectory.json` | 给 A02 提供 approach -> weld -> cooldown 的 TCP path evidence 候选 | 确认真实 TCP 时间戳、坐标系、工具中心点和采样频率 |
| 人工修正路径点 | `files/manual_corrections.json` | 展示 endpoint correction、修正原因和审查状态 | 替换为真实审查工具输出，匿名化 reviewer，确认修正点单位 |
| 质量标签 | `clean/weld_workcell/review_labels.csv`、`files/quality_result.json` | 说明该窗口可作为质量 outcome evidence 候选 | 确认质量检测来源、缺陷定义、复核结论和标签口径 |
| 失败边界 | `events.csv` 中 `manual_review_required`，以及 `quality_result.json` 的 endpoint risk | 帮助 A02 区分可模仿路径和需要人工介入的边界 | 确认真实报警/异常码、严重级别和是否可公开 |
| 专家审查摘要 | `review_labels.csv.reviewer = synthetic_stage8` | 展示 evidence handoff 需要审查状态，不代表真实人员身份 | 替换为角色化或匿名化 reviewer，并保留审计要求 |

## context

| Context item | Stage 8 synthetic source | Current role | Real-data replacement check |
| --- | --- | --- | --- |
| 工件/焊缝语义 | `h300_job_window_story.json`、`job.json` | 解释 part、seam、station、robot 和 welder 的关系 | 替换为脱敏工单和焊缝定义，确认主键层级 |
| 工艺参数 | `process.csv` | 提供焊接电流、电压、送丝、气流、速度和缺陷概率摘要 | 确认真实单位、采样频率、缺失值和设备来源 |
| 模型输出摘要 | `model_outputs.json` | 记录 seam localization 和 quality prediction 的 synthetic 结果 | 替换真实模型名、版本、输入引用、置信度和路径建议 |
| 坐标系假设 | `pcl_seam_candidates.json`、`seam_trajectory.json` | 说明当前只使用 `synthetic_h300_robot_base` | 替换真实 base/tool/camera/workpiece frame 和标定版本 |
| 时间线 | `frames.csv`、`events.csv` | 对齐 approach、weld、manual review、cooldown | 确认控制器/HMI/相机/焊机多时钟同步方式 |

## attachment_reference

| Attachment reference | Stage 8 synthetic source | Handoff meaning | Real-data replacement check |
| --- | --- | --- | --- |
| Front image | `raw/files/images/front_0000.png`、`clean/weld_workcell/images/front_0000.png` | 给 A02 审查界面或 replay 提供图像引用 | 替换为脱敏图像或 onsite-only hash/path |
| Point cloud | `raw/files/point_clouds/window_0000.pcd` | 给 PCL seam candidate 和空间复盘提供附件引用 | 替换为脱敏点云，确认坐标系、标定版本和可提交边界 |
| PCL candidate | `raw/files/pcl_seam_candidates.json` | 说明 seam candidate 来源和置信度 | 替换真实 PCL 输出，确认 candidate ID 与点云引用 |
| Source artifacts | `manifest.raw.json`、`h300_job_window_story.json`、`model_outputs.json`、`manual_corrections.json`、`quality_result.json` | 保留 Raw Zone 上游证据链 | 确认哪些文件可提交、哪些只能保留在控制器或现场环境 |
| Rerun replay | `artifacts/stage8/h300_synthetic_demo/package.rrd` | 开发期回放引用，不是主数据结构 | 真实样本 replay 默认本地生成，确认不可提交内容 |

## blocked

| Blocked item | Why blocked in Stage 8 | Default next step |
| --- | --- | --- |
| 未脱敏客户、工单、人员和设备身份 | synthetic 示例没有真实身份字段，也不应猜测现场命名 | 等待 A01/现场侧提供脱敏规则和样本 |
| 内网路径、账号、密钥和权限配置 | Stage 8 只使用仓库内相对路径或本地 artifact 路径 | 在真实控制器部署前由工程侧提供权限矩阵 |
| 未脱敏图像和点云 | 可能包含现场、工件、客户或设备敏感信息 | 先确认脱敏、裁剪、hash 或 onsite-only 策略 |
| 真实报警码和质量检测报告原文 | 可能含设备、工艺或客户敏感信息 | 提供脱敏字段字典和最小样本后再进入 gap review |
| A02 正式技能资产落库 | Stage 8 只做 evidence handoff 示例，不负责 A02 资产生命周期 | 由 A02 owner 基于真实 evidence 另行评审 |

## 最小交付口径

Stage 8 可以交给 A02 的只是 synthetic evidence handoff 示例：它说明 B06 能交付哪些证据、上下文和附件引用，也明确哪些真实信息当前 blocked。它不能替代真实专家审查，也不能替代 A02 对技能资产、训练样本或上线边界的正式验收。
