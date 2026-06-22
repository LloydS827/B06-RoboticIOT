# 工业物理 AI 数据层

B06 是公司工业物理 AI 的横向数据底座项目，目标是在机器人、智能工站、设备时序和系统级协同项目中统一作业数据包、Raw/Clean Zone、回放、训练/评测导出、数据治理和审计边界，使真实物理过程可观察、可复盘、可训练、可追溯。当前第一优先级是支撑 A01 智能焊接工站形成 H300 最小作业窗口数据闭环，并将其中可用证据交给 A02 技能资产底座。

## 项目定位

B06 不定位为通用 IoT 平台，也不定位为生产 connector 项目。它的职责是把真实、脱敏或仿真的工业物理过程数据整理成可追溯的数据资产，支撑 A01 智能焊接工站、A02 机器人技能大师、B08 设备时序样板和 S01 系统级事件闭环。

Rerun 在本项目中是可替换 replay backend 和开发期观察工具，不是主数据结构。Physical AI Package、Raw/Clean Zone、profile contract、候选样本和证据 handoff 才是 B06 的主要交付边界。

## 主链路

共享上游链路统一处理数据接入、清洗、打包、回放和候选导出；不同项目按各自 profile 消费证据、候选样本或结果引用：

```text
Raw Zone
-> Clean Zone
-> Physical AI Package
-> Rerun 回放
-> candidate sample export
-> training/evaluation draft
   - A01: job-window evidence / field-alignment references
   - A02: ManipulationSkillAsset evidence handoff
   - B08: timeseries observation candidates / result references
   - S01: manufacturing event context / evidence references
```

这里的 `training/evaluation draft` 是 draft sample index，不是正式训练框架格式，也不代表四类项目都消费同一种训练/评测数据。

## 当前第一样板

当前第一样板是 **Stage 7.1 A01 H300 最小焊接作业窗口数据试点**。本阶段目标是围绕一个 H300 最小作业窗口对齐 `job_window_id`、工单/任务、工件/焊缝、点云、相机位姿、机器人位姿、标定、路径点、工艺参数、模型输出、人工修正、执行事件和质量结果。

当前没有真机接入条件，也不声称仓库已有真实 H300 数据。因此 simulated Raw/Clean fixture 仍是当前默认可运行路径，用于在无真机条件下验证 Raw Zone、Clean Zone、`weld_workcell` importer、Physical AI Package、回放、候选样本和 draft export 链路。真实/脱敏 H300 样本到位后，再替换 simulated Raw Zone 并评审字段缺口。

## 当前可用能力

- **Physical AI Package v0.1**：当前主数据包结构，用于承载任务上下文、设备、工件、坐标系、帧、事件、标签、指标和 artifact 引用。
- **Raw/Clean Zone 约定**：用于区分来源 payload、清洗后 contract、可回放 package、临时 artifact 和不可提交数据。
- **Stage 7.1 simulated Raw/Clean fixture**：可生成 A01 H300 最小焊接作业窗口替代样本，并让 Clean Zone 对齐现有 `weld_workcell` importer contract。
- **Weld workcell importer candidate**：`WeldWorkcellPackageImporter` 可承接本地机器人焊接工站业务导出目录，是 Clean Zone offline importer contract 和 handoff contract，不是生产 connector。
- **validate / summarize / candidate export**：可对 package 做开发期校验、概要汇总，并导出 `derived/candidates.csv` 候选样本。
- **Rerun `.rrd` adapter**：可把 Physical AI Package 转换为 Rerun `.rrd`，用于开发期回放和观察。
- **Training/evaluation draft export v0.2**：可导出 `physical-ai-training-eval-draft/v0.2`，作为后续标注、评估和正式训练格式转换前的 draft sample index。
- **SDK wrapper / importer contract**：提供 Python 调用层和外部 importer contract，封装 validate、summarize、candidate export、Rerun convert 和 draft export。
- **LeRobot / CSV / simulation fixture**：用于离线验证数据包结构、importer contract 和开放数据承接能力。

## 四类项目 profile

- [Profile 总览](docs/profiles/README.md)
- [A01 H300 最小焊接作业窗口 profile](docs/profiles/a01_weld_workcell_job_window.md)
- [A02 ManipulationSkillAsset evidence profile](docs/profiles/a02_manipulation_skill_asset_evidence.md)
- [B08 设备时序观测 profile](docs/profiles/b08_equipment_timeseries_observation_package.md)
- [S01 制造事件上下文 profile](docs/profiles/s01_manufacturing_event_context_package.md)
- [B06 -> A02 evidence handoff](docs/profiles/b06_to_a02_evidence_handoff.md)

## 工程对接方式

工程/机器人团队当前优先提供离线目录、脱敏样本、字段说明和验收 checklist，而不是直接建设生产 connector。A01 H300 对接优先阅读：

- [Stage 7.1 A01 H300 最小焊接作业窗口数据试点](docs/stage7/README.md)
- [A01 H300 真实/脱敏样本请求清单](docs/stage7/sample_request_checklist.md)
- [A01 H300 Raw/Clean Zone 试点约定](docs/stage7/raw_clean_zone_pilot.md)
- [H300 字段与 weld_workcell Clean contract 对齐](docs/stage7/h300_weld_workcell_field_alignment.md)
- [Stage 5 工程团队对接文档](docs/stage5/engineering_handoff.md)

Stage 5 的离线 handoff 仍可用于脱敏样本交换、回归测试、离线验收和现场无法直连时的临时导入。Stage 6 的真机数据资产模块文档仍作为后续真实数据进入 AI 控制器后的接入、存储、清洗和治理边界参考。

## 当前边界

- B06 不是通用 IoT 平台，不负责普通设备联网、现场网络接入或通用工业协议平台化。
- 当前不做生产 connector，不实现 TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连或 DB ingestion。
- 当前不新增长期 DB schema，不修改 Physical AI Package v0.1 schema，不把 simulated fixture 定义为 H300 现场协议。
- 真实数据来自现场或真机原始数据，不应直接提交仓库。
- 脱敏数据需要确认客户、工单、人员、路径、图像和点云等敏感信息处理结果；未确认前默认按本地 artifact 或 onsite-only 处理。
- 仿真数据是仓库内默认可提交、可运行、可复现的样本。
- 临时 artifact 包括本地生成的 package、`.rrd`、candidates、training draft、Raw/Clean 输出，应放在 `artifacts/` 或 `/tmp`，默认不提交。
- 不可提交数据包括客户现场原始文件、未脱敏图像/点云、账号密钥、内部网络地址、权限配置和商业敏感字段。

## 快速开始

默认开发安装和验证：

```bash
python3 -m pip install -e ".[dev]"
python -m pytest -q
```

生成当前默认可运行的 Stage 7.1 simulated Raw/Clean fixture：

```bash
python scripts/generate_stage7_sim_window.py --output-root artifacts/stage7/sim_weld_window --frames 5
```

生成一个离线演示用机器人焊接工站 package：

```bash
python scripts/physical_ai_package.py generate welding --output-dir artifacts/stage5/demo_weld
```

## 常用命令

以下命令以 `artifacts/stage5/demo_weld` 为输入目录，覆盖当前离线默认链路：

```bash
python scripts/physical_ai_package.py validate artifacts/stage5/demo_weld --json
python scripts/physical_ai_package.py summarize artifacts/stage5/demo_weld --json
python scripts/physical_ai_package.py export-candidates artifacts/stage5/demo_weld
python scripts/physical_ai_package.py export-training-draft artifacts/stage5/demo_weld --split eval
python scripts/physical_ai_package.py convert-rerun artifacts/stage5/demo_weld --output-rrd artifacts/stage5/demo_weld.rrd
```

LeRobot 真实开放数据导入仍使用 Stage 4 文档中的 `uv` 可选环境和 `import-lerobot` 命令。

## 总体路线规划

本项目采用“先借力验证，再外围封装，最后形成自有数据层”的路线推进。Rerun.io 在当前阶段优先作为实验底座和参考架构，而不是一开始就作为不可替换的产品内核。

### 阶段 0：项目启动与资料沉淀

目标是建立项目基线，沉淀启动文档、调研目录、执行记录和协作规范。当前阶段已完成仓库初始化、README、details、docs 目录和第一批 Rerun.io 调研文档。

### 阶段 1：Rerun.io 深度调研

目标是拆解 Rerun.io 的产品定位、数据模型、SDK、Viewer、存储格式、Catalog、查询、训练导出、扩展机制、许可证和商业边界，明确哪些能力值得借鉴、复用、封装、二次开发或自研替代。

### 阶段 2：Rerun.io 本地技术评测

目标是用 Rerun 跑通最小多模态实验，验证图像、点云、机器人位姿、轨迹、日志、事件、工艺参数和模型输出的记录、回放、查询和导出能力。该阶段重点回答“Rerun 能不能支撑我们第一批样板场景”。

### 阶段 3：Simulation-first 数据包链路

目标是在不接入真机的前提下，用机器人焊接工站和机械臂抓取/分拣两个仿真样例，跑通 Physical AI Package schema、validator、候选导出、Rerun adapter 和 CLI。真实机器人或智能工站的一次作业闭环顺延到后续样板场景阶段。

### 阶段 4：LeRobot 开放数据样板链路

目标是在不接入真机、不训练模型的前提下，将 LeRobot 开放机器人操作数据导入 Physical AI Package，形成 import adapter、CLI、profile 映射、多相机 Rerun adapter 支持和 PushT/ALOHA 样板验收命令。这样既能复用 Rerun 作为回放后端，又能验证 Physical AI 数据包对真实社区数据的承接能力。

### 阶段 5：业务接入与交付文档

目标是形成面向工程团队和机器人团队的最小交付文档包，包括项目入口、业务导出 contract、字段说明、调用方式、产出物、验收 checklist 和常见错误说明。本阶段不新增生产 connector、不接真实现场系统、不扩展 package schema。

### 阶段 6：真机数据接入与数据资产化试点

目标是围绕 AI 控制器侧真实机器人作业数据，明确接入、Raw Zone、Clean Zone、Physical AI Package、Rerun 回放和训练数据准备的第一版链路。Stage 5 离线 handoff contract 继续用于脱敏样本交换、回归测试和离线验收；Stage 6 主线转为真机数据进入 AI 控制器后的存储、清洗、整理、回放和数据资产化试点。本阶段继续保持 Rerun 为可替换回放 backend，不新增生产 connector、TCP/IP server、SDK bridge 或 DB schema。

### 阶段 7.1：A01 H300 最小焊接作业窗口数据试点

目标是在真机接入条件尚未具备时，将 Stage 7 的 deterministic simulated Raw/Clean fixture 收束到 A01 H300 最小焊接作业窗口，验证 Raw Zone -> Clean Zone -> `weld_workcell` importer -> Physical AI Package -> validate/summarize/candidates/training draft/Rerun 的离线闭环，并通过 profile contract 说明 A01/A02/B08/S01 各自如何消费 evidence、候选样本或结果引用。本阶段为真实/脱敏 H300 样本替换做准备，不实现生产 connector、长期 DB schema 或 Physical AI Package schema changes。

## 近期输出物

- 竞品与开源生态调研报告
- Rerun.io 技术评测报告
- 样板场景数据链路
- 数据格式与接口规范
- 数据集整理流程
- Stage 5 工程团队 handoff 文档包
- Stage 6 真机数据接入与数据资产化文档包
- Stage 7.1 A01 H300 最小焊接作业窗口数据试点文档包
- Stage 7.1 simulated Raw/Clean fixture generator
- A01/A02/B08/S01 project profile contract 文档包
- real-data 真机准备截图索引
- 自研路线判断

## 文档目录

- [Physical AI 数据层项目启动说明](docs/260606_PhysicalAI数据层项目启动说明.md)
- [B06 Robotic IOT 与物理数据层课题](docs/03-B06_RoboticIOT与物理数据层课题.md)
- [调研目录](docs/research/README.md)
- [Rerun.io 阶段二本地技术评测设计](docs/superpowers/specs/2026-06-07-rerun-stage-2-local-evaluation-design.md)
- [阶段二运行说明](docs/stage2/README.md)
- [Rerun.io 阶段二本地技术评测报告](docs/research/04-rerun阶段二本地技术评测报告.md)
- [Simulation-first Physical AI Data Package 设计](docs/superpowers/specs/2026-06-08-simulation-first-physical-ai-data-package-design.md)
- [阶段三运行说明](docs/stage3/README.md)
- [Physical AI 数据包阶段三实施记录](docs/research/05-physical-ai数据包阶段三实施记录.md)
- [Stage 4 LeRobot 开放数据样板链路运行说明](docs/stage4/README.md)
- [LeRobot 到 Physical AI Package 映射](docs/research/06-lerobot到physical-ai-package映射.md)
- [LeRobot 开放数据样板链路记录](docs/research/06-lerobot开放数据样板链路记录.md)
- [Stage 4.2 SDK Wrapper / External Importer 边界设计](docs/superpowers/specs/2026-06-10-sdk-wrapper-importer-boundary-design.md)
- [Stage 4.2 SDK Wrapper / External Importer Boundary 实施计划](docs/superpowers/plans/2026-06-10-sdk-wrapper-importer-boundary.md)
- [Stage 4.3 Training/Evaluation Export Contract 与非 LeRobot Importer 设计](docs/superpowers/specs/2026-06-10-stage-4-3-training-importer-contract-design.md)
- [Stage 4.3 Training Importer Contract 实施计划](docs/superpowers/plans/2026-06-10-stage-4-3-training-importer-contract.md)
- [Stage 4.4 Weld Workcell 业务 Importer 设计](docs/superpowers/specs/2026-06-10-stage-4-4-weld-workcell-importer-design.md)
- [Stage 4.4 Weld Workcell Importer 实施计划](docs/superpowers/plans/2026-06-10-stage-4-4-weld-workcell-importer.md)
- [Stage 5 业务接入与交付文档设计](docs/superpowers/specs/2026-06-11-stage-5-handoff-docs-design.md)
- [Stage 5 Handoff Docs 实施计划](docs/superpowers/plans/2026-06-11-stage-5-handoff-docs.md)
- [Stage 5 业务接入与交付文档](docs/stage5/README.md)
- [Stage 5 工程团队对接文档](docs/stage5/engineering_handoff.md)
- [Stage 6 真机数据接入与数据资产化设计](docs/superpowers/specs/2026-06-11-stage-6-real-robot-ingestion-design.md)
- [Stage 6 真机数据接入与数据资产化实施计划](docs/superpowers/plans/2026-06-11-stage-6-real-robot-ingestion.md)
- [Stage 6 真机数据接入与数据资产化](docs/stage6/README.md)
- [真机数据资产模块定位](docs/stage6/real_robot_data_asset_module.md)
- [真机字段分层与映射](docs/stage6/real_data_field_mapping.md)
- [Stage 6 真机接入准备资料](docs/real-data/README.md)
- [Stage 7 仿真优先小作业窗口数据试点设计](docs/superpowers/specs/2026-06-16-stage-7-simulated-small-job-window-pilot-design.md)
- [Stage 7 Simulated Small Job Window Pilot 实施计划](docs/superpowers/plans/2026-06-16-stage-7-simulated-small-job-window-pilot.md)
- [Stage 7.1 工业物理 AI profile 对齐设计](docs/superpowers/specs/2026-06-22-stage-7-1-industrial-physical-ai-profile-alignment-design.md)
- [Stage 7.1 工业物理 AI profile 对齐计划](docs/superpowers/plans/2026-06-22-stage-7-1-industrial-physical-ai-profile-alignment.md)
- [Stage 7.1 A01 H300 最小焊接作业窗口数据试点](docs/stage7/README.md)
- [Stage 7.1 A01 H300 真实/脱敏样本请求清单](docs/stage7/sample_request_checklist.md)
- [Stage 7.1 A01 H300 Raw/Clean Zone 试点约定](docs/stage7/raw_clean_zone_pilot.md)
- [H300 字段对齐](docs/stage7/h300_weld_workcell_field_alignment.md)
- [Profile 总览](docs/profiles/README.md)
- [A01 H300 profile](docs/profiles/a01_weld_workcell_job_window.md)
- [A02 ManipulationSkillAsset evidence profile](docs/profiles/a02_manipulation_skill_asset_evidence.md)
- [B08 设备时序观测 profile](docs/profiles/b08_equipment_timeseries_observation_package.md)
- [S01 制造事件上下文 profile](docs/profiles/s01_manufacturing_event_context_package.md)
- [B06 -> A02 evidence handoff](docs/profiles/b06_to_a02_evidence_handoff.md)
- [项目执行细节](details.md)
- [AI 协作规范](AGENTS.md)

## 文档分工

README 记录项目定位、主链路、当前第一样板、当前能力、profile 入口、工程对接方式、快速开始和当前边界，保持在项目级概览层面。更细的执行记录、当前完成事项、下一步计划和阶段性决策记录在 [details.md](details.md) 中。工程团队对接字段、导出目录、验收 checklist 和常见错误由 Stage 5、Stage 7.1 和 profile 文档共同承载。

## 交付流程

阶段性任务完成后，按任务范围同步更新对应文档，再通过远端 Pull Request 合并到 `main`。PR 在远端合并完成后，清理对应本地开发分支，保持本地工作区干净。

## 当前状态

本仓库目前用于承载项目启动文档、调研材料、实验记录、接口规范、原型代码和 Stage 5 业务接入 handoff 文档。阶段二已经跑通 Rerun 本地技术评测的最小闭环；阶段三已有 simulation-first Physical AI 数据包 runnable package、validator、Rerun adapter 和 CLI prototype，覆盖机器人焊接工站与机械臂抓取/分拣两个仿真样例，并已完成两个样例包的生成、校验、汇总、候选 CSV 导出、`.rrd` 转换和 `rerun rrd verify` smoke。

阶段四已形成 LeRobot 开放数据 import adapter、lazy loader、`import-lerobot` CLI、PushT/ALOHA/fallback profile、候选指标扩展和 Rerun 多相机引用支持。Stage 4.1 已建立独立 `uv` 环境并跑通真实 `lerobot/pusht` quick smoke、`lerobot/pusht` full acceptance 命令链路与 `lerobot/aloha_static_towel` 多相机 representative smoke，最终回归为 `99 passed`。

Stage 4.2 已新增最小 SDK wrapper、external importer contract、`LeRobotPackageImporter` contract 实现、training/evaluation draft export 和 `export-training-draft` CLI；这些能力用于把现有原型边界沉淀为可被 Python 调用、可被外部 importer 扩展的最小接口层。

Stage 4.3 已收紧 training/evaluation draft export contract 到 `physical-ai-training-eval-draft/v0.2`，明确 draft manifest、samples 字段、split 允许值和“非正式训练框架格式”边界；同时新增离线 `CsvRecordingPackageImporter` fixture，用本地单文件 CSV recording 证明 external importer contract 不是 LeRobot 专用接口。当前自动化环境 native Rerun GUI 启动失败，Viewer/Blueprint 人工视觉验收仍需在 GUI 可用环境补做。

Stage 4.4 已新增离线 `WeldWorkcellPackageImporter` 业务 importer candidate，用本地机器人焊接工站导出目录验证多文件业务输入、工艺参数、事件、人工复核标签和图片引用如何进入 `robot_welding_station` Physical AI Package。该能力不新增 CLI、不接真实机器人/PLC/MES/HMI，也不改变默认离线可测试路径；输出 package 已验证可继续进入 validate、summarize、candidate export、training/evaluation draft export 和 Rerun `.rrd` adapter。

Stage 5 当前已形成业务接入与交付文档：根 README 作为项目入口，Stage 5 文档承载工程团队 handoff，Stage 4 文档继续记录 LeRobot、CSV fixture 和 Weld Workcell importer candidate 的技术细节。

Stage 6 已新增真机数据接入与数据资产化文档包，包括 `docs/stage6/README.md`、`docs/stage6/real_robot_data_asset_module.md`、`docs/stage6/real_data_field_mapping.md` 和 `docs/real-data/README.md`。`docs/real-data/1.jpg` 与 `docs/real-data/2.jpg` 当前作为 Stage 6 真机准备截图，用于支撑系统通讯关系、字段来源、优先级和待确认问题梳理。

Stage 7.1 已将 Stage 7 simulated Raw/Clean fixture 收束为 A01 H300 最小焊接作业窗口数据试点：`scripts/generate_stage7_sim_window.py` 仍是当前无真机条件下的默认可运行路径，Clean Zone 对齐现有 `WeldWorkcellPackageImporter` contract，并可继续进入 Physical AI Package 的 validate、summarize、candidate export、training/evaluation draft 和 Rerun `.rrd` adapter 链路。`docs/profiles/` 已补充 A01、A02、B08、S01 四类 profile 和 B06 -> A02 evidence handoff，明确共享上游链路与 profile-specific consumption。下一步仍需用真实/脱敏 A01 H300 最小窗口替换 simulated Raw Zone，并评审字段、时间戳、坐标系、权限、脱敏和 AI 控制器存储边界后，再决定是否需要 importer 演进、connector skeleton、DB/schema 或 package schema changes。
