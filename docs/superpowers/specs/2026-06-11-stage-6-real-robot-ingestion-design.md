# Stage 6 真机数据接入与数据资产化设计

## 1. 背景

Stage 5 将 Stage 2-4.4 的研发成果整理成面向工程团队的 handoff 文档，默认假设是“工程团队先导出一份离线业务目录，再由 importer contract 转成 Physical AI Package”。这个假设适合脱敏样本交换和离线验证，但不再完全符合当前真机接入准备工作的实际路径。

根据 `docs/real-data/1.jpg` 的系统通讯图，真实现场链路更接近：

- 相机通过 LAN 接入视觉控制器。
- 机械臂通过控制器 SDK 与视觉控制器交互。
- 视觉控制器内包含 Gvision3D 焊缝提取算法和调度中台，调度中台负责工程创建、相机拍照、轨迹转换和下发 lua。
- HMI 平板通过 TCP/IP + JSON 与视觉控制器交互。
- AI 控制器从 SDK、TCP/IP、视觉控制器、相机、焊机等路径获得数据，并负责数据存储、清洗、整理、回放和后续训练数据集生产。

根据 `docs/real-data/2.jpg` 的字段盘点，现场可用数据不只是 Stage 4.4 里抽象出的 `job.json`、`frames.csv`、`process.csv`、`events.csv`，而是包括资料、机械臂、相机、焊机、保护气体、送丝机、工艺和任务等多个类别。它们既包含文件型资料，也包含实时通讯数据、工艺过程记录和任务上下文。

因此 Stage 6 应从“离线 importer handoff”升级为 **真机数据接入与数据资产化试点**。离线导出目录仍保留，但定位变为调试、脱敏交换、回归测试和离线验收格式；主线应是 AI 控制器上的在线/准在线数据接入、存储、清洗、标准化和数据集生产准备。

## 2. 阶段目标

Stage 6 的目标是重新定义并落地第一版真机接入准备材料：

- 将现有“素材模块/数据模块”升级为 **真机数据资产模块** 的产品定位。
- 明确 AI 控制器上的数据链路：接入、Raw Zone、Clean Zone、Physical AI Package、回放与训练数据集准备。
- 基于两张真实准备截图，整理第一版真机字段分层和接入优先级。
- 更新项目 README 和 Stage 文档，让新读者理解当前主线已经从离线业务导出转向真机接入准备。
- 保持 Physical AI Package 为主数据结构，Rerun 作为可替换回放 backend，不在本阶段 fork、二次开发或从零开发 viewer。
- 不在接口协议、样例 payload、采样频率、现场数据库表未确认前新增生产 connector。

本阶段应服务两个目标：

1. **当前产品升级**：把既有素材/数据模块升级成能承接真实机器人作业数据的真机数据资产模块。
2. **独立产品路线预留**：把“机器人真机数据层 / Physical AI DataHub / Robot Data Recorder”作为潜在独立产品方向记录下来，但不在本阶段扩成完整独立产品。

## 3. 方案比较

### 方案 A：真机接入优先，文档与 contract 先行

围绕 AI 控制器的真实数据接入链路，更新 Stage 6 文档、README、details 和字段映射材料。暂不写生产 connector，只明确模块定位、数据分层、字段优先级、接口待确认项和后续 MVP。

优点：最贴近当前真机接入准备；能降低现有模块上手难度；不依赖尚未确定的现场协议；保持默认项目可运行。缺点：本分支不直接产生在线采集代码。

### 方案 B：立即实现在线 connector 原型

根据截图推测 TCP/IP JSON、SDK 和 DB 写入路径，新增采集服务或 connector skeleton。

优点：看起来推进更快。缺点：目前缺少协议细节、样例 payload、采样频率、错误模型和运行环境；容易写出与现场实际不符的伪 connector，后续返工成本高。

### 方案 C：先设计独立产品完整架构

把模块直接定义成独立产品，设计产品架构、权限、部署、数据库、Viewer、SDK、商业模块和长期路线。

优点：战略完整。缺点：范围过大，会掩盖当前最重要的真机数据接入问题；也会过早决定 Rerun 二开/自研等高成本路线。

## 4. 选定方案

采用 **方案 A：真机接入优先，文档与 contract 先行**。

原因：

- 用户已经确认当前首要方向是真机接入优先，然后同步升级现有产品模块，最后再思考独立产品。
- 当前证据足以重新定义模块定位和数据链路，但不足以实现生产 connector。
- Stage 6 的关键风险不是代码量，而是真机系统边界、字段语义、时间基准、数据落盘策略和 Rerun 定位是否清楚。
- 通过文档和 contract 先行，可以为后续小场景真机试点提供清晰验收基线。

## 5. 新模块定位

### 5.1 从“素材模块”升级为“真机数据资产模块”

旧的“素材模块”容易让人理解成图片、点云、轨迹文件的集合。Stage 6 后应升级为：

> 真机数据资产模块负责把真实机器人作业过程中的多源数据接入 AI 控制器，完成原始留存、清洗整理、时间对齐、语义映射、标准数据包生成、可视化回放和训练数据集准备。

它管理的不只是素材文件，还包括：

- 作业上下文：工单、任务、设备、工件、焊缝、工艺类型。
- 机器人数据：工程 lua、轨迹 json、关节角度、关节位置、关节速度、关节扭矩、末端坐标和欧拉角。
- 视觉数据：相机资料、拍照位姿、2D 图像、3D 点云、相机配置。
- 焊接数据：焊接类型、焊缝轨迹、下发焊机电压、电流、速度、焊枪位置。
- 工艺与辅机数据：保护气体流量/浓度/压力、送丝速度、出丝长度、焊接过程记录、异常记录。
- 任务数据：焊机时间戳、工单 ID、焊缝 ID、任务 ID、设备 ID/型号。
- 派生产物：Physical AI Package、Rerun `.rrd`、候选样本、training/evaluation draft、后续正式训练数据集。

### 5.2 产品边界

本模块不是普通设备联网平台，也不是单纯数据湖。它的产品价值在于：

- 让一次真实机器人作业可以被复盘。
- 让多源现场数据变成标准化物理 AI 数据资产。
- 让算法团队能从真实作业中筛选失败案例、异常样本和训练/评估样本。
- 让工程团队能确认接口、字段、采样、时间戳和数据质量问题。

## 6. 真机数据链路

Stage 6 推荐的数据链路如下：

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
  Rerun `.rrd`、derived/candidates.csv、derived/training_eval/
        ↓
后续训练数据集与评估数据集
```

离线 `weld_workcell` importer contract 在 Stage 6 后仍保留，但定位调整为：

- 脱敏样本交换格式。
- 本地回归测试 fixture。
- 现场无法直接连通时的临时导入路径。
- 真机接入字段 contract 的离线等价物。

## 7. 数据分层设计

### 7.1 Raw Zone

Raw Zone 保存现场系统来的原始形态，不强行改名或丢字段。它适合存：

- 机械臂工程 `.lua`。
- 机械臂轨迹 `.json`。
- 焊缝轨迹 `.json`。
- 相机 2D 图像、3D 点云、拍照位姿和相机配置。
- TCP/IP JSON 原始消息。
- HMI 下发或回传的任务消息。
- 焊接过程记录、工艺记录、异常记录。
- 任务、工单、设备 ID 等原始上下文。

原则：

- Raw Zone 是可追溯依据，不追求立即训练可用。
- Raw Zone 中的客户敏感字段后续必须有脱敏策略。
- Raw Zone 不等于正式 package，也不等于训练数据集。

### 7.2 Clean Zone

Clean Zone 负责把 Raw Zone 整理成可进入标准数据包的中间层。它适合处理：

- 字段命名统一。
- 时间戳单位和时区统一。
- 多源时间对齐。
- 坐标系和姿态表示统一。
- 缺失值、异常值、重复记录和采样频率记录。
- 工艺语义映射，例如焊接类型、焊缝轨迹、异常类型。

原则：

- Clean Zone 必须能追溯回 Raw Zone。
- Clean Zone 不应覆盖 Raw Zone。
- Clean Zone 中的派生字段必须标明来源或转换规则。

### 7.3 Physical AI Package

Physical AI Package 继续作为主数据结构，承接标准化后的作业数据：

- `physical_ai_manifest.json`：任务、设备、对象、坐标系、source dataset。
- `frames.csv`：时间线、TCP/相机等帧级引用。
- `events.csv`：报警、异常、状态切换、焊接阶段事件。
- `metrics.csv`：电流、电压、速度、气体、送丝、风险评分等时序指标。
- `labels.csv`：人工复核或算法标签。
- `artifacts/`：图像、点云、轨迹、原始 source 引用和派生文件。

### 7.4 Training Dataset

训练数据集不是 Raw Zone，也不是直接的 Physical AI Package。它应由清洗后的 package 派生，并在后续阶段明确：

- 样本粒度：frame、window、trajectory segment、weld seam、task episode。
- split 规则：train/eval/test 或现场验证集。
- label 来源：人工复核、规则、视觉算法、质检结果。
- 数据版本：来源 package、生成时间、过滤规则、转换脚本版本。

Stage 6 只更新定位和准备材料，不定义正式训练框架格式。

## 8. 截图字段到数据模型的初步映射

| 类别 | 截图字段 | Stage 6 目标位置 | Stage 6 优先级 |
| --- | --- | --- | --- |
| 资料 | 焊接机器人模型文件 | Raw Zone artifact；后续可进入 manifest device metadata | P2 |
| 资料 | 深度相机资料 | Raw Zone artifact；后续可进入 camera metadata | P2 |
| 资料 | 机械臂资料 | Raw Zone artifact；后续可进入 robot metadata | P2 |
| 资料 | 焊机资料 | Raw Zone artifact；后续可进入 welder metadata | P2 |
| 机械臂 | 机器人控制器中机械臂运行文件 `.lua` | Raw Zone artifact；package artifact 引用 | P1 |
| 机械臂 | 机械臂轨迹文件 `.json` | Raw Zone + Clean Zone trajectory；package trajectory artifact | P0 |
| 机械臂 | 关节实时角度/位置/速度/扭矩 | Clean Zone time series；package metrics 或后续 joint state table | P0 |
| 机械臂 | 机械臂末端笛卡尔坐标/欧拉角 | Clean Zone pose；package frames | P0 |
| 相机 | 焊缝轨迹文件 `.json` | Raw Zone + Clean Zone seam trajectory；package artifact / object relation | P0 |
| 相机 | 深度相机点云 | Raw Zone artifact；package point cloud artifact | P1 |
| 相机 | 深度相机 2D 图像 | Raw Zone artifact；package image artifact | P0 |
| 相机 | 深度相机拍照时位姿 | Clean Zone pose；package frames / camera pose metadata | P0 |
| 焊机 | 下发焊接电压/电流/速度 | Clean Zone metrics；package metrics | P0 |
| 焊机 | 焊枪焊接时位置 | Clean Zone pose/event；package frames/events | P1 |
| 保护气体 | 流量/浓度/压力 | Clean Zone metrics；package metrics | P1 |
| 送丝机 | 送丝速度/出丝长度 | Clean Zone metrics；package metrics | P1 |
| 工艺 | 焊接过程记录 | Raw Zone + events/metrics | P0 |
| 工艺 | 焊接工艺记录 | Raw Zone + manifest/task metadata | P1 |
| 工艺 | 焊接异常记录 | events.csv；candidate export 的重要来源 | P0 |
| 任务 | 焊机时间戳 | 统一时间基准输入 | P0 |
| 任务 | 工单 ID/工件编号 | manifest task/object/source metadata | P0 |
| 任务 | 焊缝 ID/任务 ID | manifest task/object/source metadata | P0 |
| 任务 | 设备 ID/型号 | manifest devices/source metadata | P0 |

P0 表示第一轮真机试点必须确认；P1 表示建议纳入第一轮或第二轮；P2 表示先保留资料和 metadata，不阻塞试点。

## 9. Rerun 定位决策

Stage 6 采用以下决策：

- **不 fork Rerun。**
- **不把 Rerun 二次开发成主产品内核。**
- **不从零开发 viewer。**
- **继续使用 Rerun 核心能力作为可替换回放 backend。**

原因：

- 当前最核心问题是真机数据接入、清洗、对齐和资产化，不是 Viewer 自研。
- Rerun 已能覆盖开发期 `.rrd` 回放、调试和视觉验收需求。
- Physical AI Package、Raw Zone、Clean Zone 和后续数据库才是我们的主资产。
- 保持 adapter 边界可以避免长期被某一个 viewer 或存储格式锁死。

未来是否二开或自研 Viewer，应在以下条件满足后再判断：

- 已有至少一个真实/脱敏小场景跑通完整链路。
- 已明确 Rerun Viewer 在现场验收、权限、标注、协作或部署上的具体不足。
- 已能区分“产品需要的回放工作台”和“开发期观察工具”的边界。

## 10. Stage 6 MVP 边界

本轮 Stage 6 应交付：

- Stage 6 设计 spec。
- Stage 6 实施 plan。
- `docs/stage6/README.md`：真机数据接入与数据资产化阶段总览。
- `docs/stage6/real_robot_data_asset_module.md`：面向产品和工程团队的新模块定位说明。
- `docs/stage6/real_data_field_mapping.md`：基于两张截图的字段分层、优先级和待确认问题。
- `docs/real-data/README.md`：说明 `1.jpg` 和 `2.jpg` 是 Stage 6 真实接入准备资料。
- README 更新：把 Stage 6 主线加入项目定位、路线和文档目录。
- Stage 5 文档更新：说明原离线 handoff contract 在 Stage 6 后的角色调整。
- `details.md` 更新：记录 Stage 6 决策、验证结果和下一阶段计划。

本轮 Stage 6 不做：

- 不新增生产 connector。
- 不新增长期数据库 schema。
- 不实现 TCP/IP server、SDK bridge、OPC UA/MES/HMI 直连。
- 不改变 Physical AI Package v0.1 schema。
- 不新增正式训练数据集格式。
- 不把 Rerun 作为不可替换内核。

## 11. 验收标准

Stage 6 本轮完成后应满足：

- 新读者能通过 README 理解项目已进入真机数据接入准备阶段。
- 工程/机器人团队能通过 Stage 6 文档理解 AI 控制器上的数据链路和他们需要确认的字段。
- 产品团队能理解“素材模块”为什么升级为“真机数据资产模块”。
- Rerun 定位不再含糊：短中期使用核心回放能力，保持 adapter 可替换，不进行 fork/二开/自研 viewer 决策。
- 离线 `weld_workcell` importer contract 的新角色清楚：它是脱敏交换、回归测试和离线验收格式，不是真机接入主线。
- 默认项目仍可安装、测试和运行现有离线命令。

验证命令：

```bash
python -m pytest -q
python scripts/physical_ai_package.py generate welding --output-dir /tmp/stage6_demo_weld
python scripts/physical_ai_package.py validate /tmp/stage6_demo_weld --json
python scripts/physical_ai_package.py summarize /tmp/stage6_demo_weld --json
python scripts/physical_ai_package.py export-candidates /tmp/stage6_demo_weld
python scripts/physical_ai_package.py export-training-draft /tmp/stage6_demo_weld --split eval
python scripts/physical_ai_package.py convert-rerun /tmp/stage6_demo_weld --output-rrd /tmp/stage6_demo_weld.rrd
```

## 12. 下一阶段预期

Stage 6 文档与定位完成后，下一阶段应进入 **真实/脱敏小场景数据接入试点**：

- 选定一个最小焊接作业窗口。
- 获取 SDK/TCP JSON/文件/DB 的真实样例 payload。
- 明确时间戳来源、采样频率、字段单位、坐标系和数据保存位置。
- 用最小字段集合跑通 Raw Zone 到 Clean Zone 再到 Physical AI Package。
- 基于真实数据决定是否需要扩展 package schema、数据库 schema 或在线接入服务。
