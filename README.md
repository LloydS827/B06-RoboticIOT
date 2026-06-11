# Physical AI 数据层

本项目是面向机器人、智能工站和具身智能系统的数据基础设施项目，内部课题名为 **B06 Robotic IOT 与物理数据层**。

项目目标是在真实物理系统研发和现场验证过程中，统一完成多源数据接入、采集、记录、回放、整理、标注、评估和训练数据导出。它对标 Rerun.io 等开源数据层工具，但核心关注点不是普通设备联网，而是面向 AI 的物理过程数据、可观测性、可复盘性和可训练性。

## 项目定位

机器人项目中的传感器、控制器、视觉算法、HMI、工艺系统和模型训练往往各自记录数据，导致问题难复盘、数据难复用、样本难整理、模型难验证。

Physical AI 数据层希望把这些研发和现场数据组织成可观察、可回放、可训练、可追溯的数据资产，支撑智能工站、机器人焊接、移动机器人、协作机器人、视觉检测系统和其他需要物理世界数据闭环的智能设备。

## 核心能力方向

- 多源数据接入：对接控制器、上位机、中台、HMI、相机、传感器、算法模块和业务系统。
- 多模态数据记录：记录图像、点云、位姿、轨迹、日志、事件、参数和模型输出。
- 时空对齐：建立时间戳、坐标系、设备状态和任务上下文之间的关联。
- 可视化回放：支持研发人员复盘一次真实作业，定位算法、通信、标定、路径和执行问题。
- 数据集整理：形成样本包、标签规范、失败案例库、人工修正记录和版本化数据集。
- 训练与评估导出：为模型训练、算法对比、模型评估和现场验证提供标准化数据。
- 数据治理：区分可训练数据、客户现场敏感数据、内部调试数据和产品化数据资产。

## 当前可用能力

- **Physical AI Package v0.1**：当前主数据包结构，用于承载任务上下文、设备、工件、坐标系、帧、事件、标签、指标和 artifact 引用。
- **Simulation sample generation**：可生成机器人焊接工站和机械臂抓取/分拣两个确定性仿真样例。
- **validate / summarize / candidate export**：可对 package 做开发期校验、概要汇总，并导出 `derived/candidates.csv` 候选样本。
- **Rerun `.rrd` adapter**：可把 Physical AI Package 转换为 Rerun `.rrd`，用于开发期回放和观察。
- **SDK wrapper**：提供 Python 调用层，封装 validate、summarize、candidate export、Rerun convert 和 training/evaluation draft export。
- **LeRobot importer**：可把 LeRobot 开放机器人操作数据导入 Physical AI Package，已覆盖 PushT、ALOHA 代表性样例和 fallback profile。
- **CSV recording fixture**：用本地单文件 CSV recording 验证 external importer contract 不是 LeRobot 专用接口。
- **Weld workcell importer candidate**：`WeldWorkcellPackageImporter` 可承接本地机器人焊接工站业务导出目录，是业务 importer candidate 和 handoff contract，不是生产 connector。
- **Training/evaluation draft export v0.2**：可导出 `physical-ai-training-eval-draft/v0.2`，作为后续标注、评估和正式训练格式转换前的 draft sample index。

## 快速开始

默认开发安装和验证：

```bash
python3 -m pip install -e ".[dev]"
python -m pytest -q
```

生成一个 Stage 5 演示用机器人焊接工站 package：

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

LeRobot 真实开放数据导入仍使用 Stage 4 文档中的 `uv` 可选环境和 `import-lerobot` 命令；工程业务导出对接优先阅读 Stage 5 handoff 文档。

## 工程团队对接

Stage 5 的重点是把 Stage 2-4.4 的研发成果转成工程团队可理解、可准备、可验收的交付材料。当前推荐对接方式是让工程/机器人团队先导出一份离线业务目录，再由 importer contract 转成 Physical AI Package，随后统一运行 validate、summarize、candidate export、training/evaluation draft export 和 Rerun `.rrd` adapter。

优先阅读：

- [Stage 5 业务接入与交付文档](docs/stage5/README.md)
- [工程团队对接文档](docs/stage5/engineering_handoff.md)
- [Stage 4 LeRobot 开放数据样板链路运行说明](docs/stage4/README.md)

## 启动路线

当前项目已从启动调研进入业务接入与交付文档阶段，近期工作重点如下：

1. 继续保持 Physical AI Package、validator、SDK wrapper、importer contract 和离线 CLI 默认链路可运行。
2. 将 Rerun.io 作为可替换 adapter backend 和参考生态，保留 `.rrd` 转换、验证和回放能力。
3. 以仿真样例、LeRobot 开放数据、CSV recording fixture 和 Weld Workcell importer candidate 验证数据包结构的覆盖范围。
4. 为工程团队准备离线导出 contract、字段说明、验收 checklist 和常见错误说明。
5. 在真实现场接入前，明确数据脱敏、权限审计、MES/PLC/HMI 边界和 native GUI 验收的后续工作。

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

### 阶段 6：产品化与自研边界收敛

目标是根据样板场景和技术评测结果，决定 Rerun 在长期架构中的角色：作为开发期工具、可替换内核、二次开发基础，或仅作为参考实现。同时，自研客户现场权限、审计、脱敏、数据分级、质量追溯、工艺语义和长期数据资产管理等产品化能力。

## 近期输出物

- 竞品与开源生态调研报告
- Rerun.io 技术评测报告
- 样板场景数据链路
- 数据格式与接口规范
- 数据集整理流程
- Stage 5 工程团队 handoff 文档包
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
- [项目执行细节](details.md)
- [AI 协作规范](AGENTS.md)

## 当前边界

- Rerun 是可替换 adapter backend 和开发期回放后端，不是 Physical AI 数据层的主数据结构。
- Weld workcell importer 是 candidate/handoff contract，不是生产 connector；它不连接真实机器人、PLC、OPC UA、MES、HMI 或数据库。
- LeRobot importer、CSV recording fixture 和 Weld workcell importer candidate 当前都服务于离线验证和 contract 收敛，不代表客户现场产品化接入已经完成。
- 真实现场集成、权限/审计、数据脱敏、MES/PLC/HMI 直连、native GUI acceptance 仍是未来工作。
- Training/evaluation draft export v0.2 是 draft sample index，不是正式训练框架格式；当前不自动划分训练/评估集，也不推断策略效果。

## 文档分工

README 记录项目定位、当前能力、快速开始、重要入口和当前边界，保持在项目级概览层面。更细的执行记录、当前完成事项、下一步计划和阶段性决策记录在 [details.md](details.md) 中。工程团队对接字段、导出目录、验收 checklist 和常见错误由 Stage 5 文档承载。

## 交付流程

阶段性任务完成后，按任务范围同步更新对应文档，再通过远端 Pull Request 合并到 `main`。PR 在远端合并完成后，清理对应本地开发分支，保持本地工作区干净。

## 当前状态

本仓库目前用于承载项目启动文档、调研材料、实验记录、接口规范、原型代码和 Stage 5 业务接入 handoff 文档。阶段二已经跑通 Rerun 本地技术评测的最小闭环；阶段三已有 simulation-first Physical AI 数据包 runnable package、validator、Rerun adapter 和 CLI prototype，覆盖机器人焊接工站与机械臂抓取/分拣两个仿真样例，并已完成两个样例包的生成、校验、汇总、候选 CSV 导出、`.rrd` 转换和 `rerun rrd verify` smoke。

阶段四已形成 LeRobot 开放数据 import adapter、lazy loader、`import-lerobot` CLI、PushT/ALOHA/fallback profile、候选指标扩展和 Rerun 多相机引用支持。Stage 4.1 已建立独立 `uv` 环境并跑通真实 `lerobot/pusht` quick smoke、`lerobot/pusht` full acceptance 命令链路与 `lerobot/aloha_static_towel` 多相机 representative smoke，最终回归为 `99 passed`。

Stage 4.2 已新增最小 SDK wrapper、external importer contract、`LeRobotPackageImporter` contract 实现、training/evaluation draft export 和 `export-training-draft` CLI；这些能力用于把现有原型边界沉淀为可被 Python 调用、可被外部 importer 扩展的最小接口层。

Stage 4.3 已收紧 training/evaluation draft export contract 到 `physical-ai-training-eval-draft/v0.2`，明确 draft manifest、samples 字段、split 允许值和“非正式训练框架格式”边界；同时新增离线 `CsvRecordingPackageImporter` fixture，用本地单文件 CSV recording 证明 external importer contract 不是 LeRobot 专用接口。当前自动化环境 native Rerun GUI 启动失败，Viewer/Blueprint 人工视觉验收仍需在 GUI 可用环境补做。

Stage 4.4 已新增离线 `WeldWorkcellPackageImporter` 业务 importer candidate，用本地机器人焊接工站导出目录验证多文件业务输入、工艺参数、事件、人工复核标签和图片引用如何进入 `robot_welding_station` Physical AI Package。该能力不新增 CLI、不接真实机器人/PLC/MES/HMI，也不改变默认离线可测试路径；输出 package 已验证可继续进入 validate、summarize、candidate export、training/evaluation draft export 和 Rerun `.rrd` adapter。

Stage 5 当前进入业务接入与交付文档阶段：根 README 作为项目入口，Stage 5 文档承载工程团队 handoff，Stage 4 文档继续记录 LeRobot、CSV fixture 和 Weld Workcell importer candidate 的技术细节。下一步仍需在真实样本可用、脱敏和现场系统边界明确后，再推进小场景试点、权限审计、数据脱敏、MES/PLC/HMI 直连和 native GUI acceptance。
