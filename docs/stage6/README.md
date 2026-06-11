# Stage 6 真机数据接入与数据资产化

## 阶段定位

Stage 6 的主线是真机数据进入 AI 控制器，并在 AI 控制器侧完成接入、原始留存、清洗整理、标准化打包、回放和训练数据准备。本阶段把 Stage 5 的离线业务导入视角，推进到真实机器人作业数据接入准备。

当前重点不是新增生产 connector，而是先把真机数据链路、数据分层、字段优先级、产品模块定位和验收方式说清楚。只有在真实 SDK/TCP JSON、文件样例、数据库表、时间戳来源、字段单位和坐标系确认后，才适合进入 connector 或 schema 实现。

Physical AI Package 仍是主数据资产。Raw Zone 和 Clean Zone 负责承接现场原始数据与清洗后的中间数据，Physical AI Package 负责形成标准化、可验证、可派生的数据包。Rerun 继续作为可替换 replay backend，用于开发期回放和技术验收。

## 为什么不是 Stage 5.1

Stage 5 关注的是离线 `weld_workcell` contract：工程团队导出 `job.json`、`frames.csv`、`process.csv`、`events.csv` 等文件，再由 importer 生成 Physical AI Package。这条路径仍有用，适合脱敏样本交换、回归测试、离线验收和现场无法直连时的临时导入。

Stage 6 的问题已经不同：真实现场数据来自机器人控制器、视觉控制器、相机、焊机、HMI、保护气体、送丝机和工艺记录等多源系统。主叙事不再是“导出一个离线目录”，而是“AI 控制器如何接住真机作业数据，并把它变成可追溯、可回放、可筛选、可进入训练评估准备的数据资产”。

因此 Stage 6 是阶段升级，不是 Stage 5 的小补丁。离线 `weld_workcell` contract 保留为等价验收和调试路径，但不再是真机接入的主线叙事。

## 推荐阅读顺序

1. `docs/real-data/README.md`：先了解 Stage 6 真机准备资料和截图使用边界。
2. `docs/stage6/README.md`：理解 Stage 6 的阶段定位、数据链路和 MVP 边界。
3. `docs/stage6/real_robot_data_asset_module.md`：理解“素材模块”升级为“真机数据资产模块”的产品定位。
4. `docs/stage6/real_data_field_mapping.md`：查看第一轮字段分层、优先级和待确认问题。
5. `docs/stage5/engineering_handoff.md`：需要离线 `weld_workcell` contract、脱敏交换或回归 fixture 时再阅读。
6. `docs/superpowers/specs/2026-06-11-stage-6-real-robot-ingestion-design.md`：需要追溯 Stage 6 设计取舍时阅读。

## 数据链路

推荐的数据链路如下：

```text
现场设备与系统
  相机 / 视觉控制器 / 机械臂控制器 / HMI / 焊机 / 保护气体 / 送丝机
        ↓
AI 控制器数据接入层
  SDK / TCP-IP JSON / 文件同步 / DB 写入 / 后续可能的 OPC UA 或厂商协议
        ↓
Raw Zone
  原始 payload、原始文件、图片、点云、轨迹、lua、过程记录、异常记录
        ↓
Clean Zone
  字段标准化、时间对齐、坐标/任务/设备语义整理、质量检查
        ↓
Physical AI Package
  manifest、frames、events、labels、metrics、artifacts
        ↓
Replay / Candidate / Training Draft
  Rerun .rrd、derived/candidates.csv、derived/training_eval/
        ↓
后续训练数据集与评估数据集
```

Raw Zone 保存现场原始形态，Clean Zone 做字段、时间、坐标和语义整理，Physical AI Package 是可验证的标准数据资产。Rerun `.rrd`、候选样本和 training/evaluation draft 都应由标准 package 派生，而不是替代 package 本身。

## 当前产出物

- Stage 6 阶段总览：`docs/stage6/README.md`。
- 真机数据资产模块定位：`docs/stage6/real_robot_data_asset_module.md`。
- 真机字段分层与映射：`docs/stage6/real_data_field_mapping.md`。
- 真实准备资料索引：`docs/real-data/README.md`。
- 已批准设计说明：`docs/superpowers/specs/2026-06-11-stage-6-real-robot-ingestion-design.md`。
- 实施计划：`docs/superpowers/plans/2026-06-11-stage-6-real-robot-ingestion.md`。

## MVP 边界

本阶段做：

- 明确 AI 控制器侧真机数据接入与数据资产化主线。
- 明确 Raw Zone、Clean Zone、Physical AI Package、Rerun replay 和 training/evaluation draft 的关系。
- 整理第一轮字段分层、优先级和待确认问题。
- 把现有素材/数据模块升级为真机数据资产模块的产品定位。
- 保留离线 `weld_workcell` contract 作为脱敏交换、回归测试和离线验收格式。

本阶段不做：

- 不新增生产 connector。
- 不实现 TCP/IP server、SDK bridge、OPC UA/MES/HMI 直连或 DB schema。
- 不修改 Physical AI Package v0.1 schema。
- 不定义正式训练数据集格式。
- 不 fork Rerun，不把 Rerun 二次开发为产品内核，也不从零开发 viewer。

## 验收方式

文档层验收：

- 新读者能理解 Stage 6 主线是真机数据进入 AI 控制器。
- 工程和机器人团队能看到第一轮字段清单、优先级和待确认问题。
- 产品团队能理解“真机数据资产模块”与普通素材管理、普通 IoT 平台、数据湖和训练框架的差异。
- Rerun 的定位清楚：短中期使用核心回放能力，但保持 adapter 可替换。
- 离线 `weld_workcell` contract 的新角色清楚：脱敏交换、回归测试和离线验收，不是 Stage 6 主叙事。

系统层验收仍沿用现有默认能力：

```bash
python -m pytest -q
python scripts/physical_ai_package.py generate welding --output-dir /tmp/stage6_demo_weld
python scripts/physical_ai_package.py validate /tmp/stage6_demo_weld --json
python scripts/physical_ai_package.py summarize /tmp/stage6_demo_weld --json
python scripts/physical_ai_package.py export-candidates /tmp/stage6_demo_weld
python scripts/physical_ai_package.py export-training-draft /tmp/stage6_demo_weld --split eval
python scripts/physical_ai_package.py convert-rerun /tmp/stage6_demo_weld --output-rrd /tmp/stage6_demo_weld.rrd
```

## 下一步

下一步应进入真实或脱敏小场景数据接入试点：

- 选定一个最小焊接作业窗口。
- 获取 SDK/TCP JSON、文件同步或 DB 写入的真实样例。
- 确认时间戳来源、字段单位、坐标系、采样策略和数据保存位置。
- 用最小字段集合跑通 Raw Zone 到 Clean Zone 再到 Physical AI Package。
- 基于真实数据再判断是否需要扩展 package schema、数据库 schema 或在线接入服务。
