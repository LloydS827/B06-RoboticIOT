# 真机数据资产模块定位

## 从素材模块到数据资产模块

原“素材模块”容易被理解成图片、点云、轨迹文件和离线资料的集合。Stage 6 后建议升级为“真机数据资产模块”：它负责把真实机器人作业过程中的多源数据接入 AI 控制器，完成原始留存、清洗整理、时间对齐、语义映射、标准数据包生成、可视化回放和训练评估准备。

这个升级不是把素材目录改名，而是把模块目标从“管理若干文件”推进到“管理一次真实机器人作业的数据资产生命周期”。它要服务复盘、异常定位、样本筛选、训练评估准备和后续现场数据闭环。

## 面向对象

- 产品团队：确认模块边界、用户价值和未来是否独立产品化。
- 工程团队：确认现场数据如何进入 AI 控制器，以及 Raw Zone 和 Clean Zone 的责任边界。
- 机器人团队：确认机器人、相机、焊机、工艺和任务字段的来源、时间基准和坐标语义。
- 算法/数据团队：基于 Physical AI Package、回放 artifacts、候选样本和 training/evaluation draft 进行复盘与样本准备。

## 模块职责

真机数据资产模块管理以下对象：

- 作业上下文：工单、工件、焊缝、任务、设备、工站和工艺类型。
- 机器人数据：工程 lua、轨迹 json、关节实时角度/位置/速度/扭矩、末端笛卡尔坐标和欧拉角。
- 相机数据：深度相机资料、2D 图像、3D 点云、拍照时位姿和相机配置。
- 焊接数据：焊接类型、焊缝轨迹、下发焊机电压/电流/速度和焊枪焊接时位置。
- 工艺记录：焊接过程记录、焊接工艺记录、保护气体记录、送丝记录和异常记录。
- 事件：报警、异常、状态切换、焊接阶段事件和人工复核事件。
- source artifacts：原始 payload、原始文件、图片、点云、轨迹、lua、过程记录和异常记录。
- replay artifacts：Rerun `.rrd` 和后续可能的其他回放 backend 输出。
- training/evaluation draft outputs：候选样本、训练评估 draft manifest、样本索引和后续正式训练数据集的准备材料。

模块应支持从 Raw Zone 到 Clean Zone 再到 Physical AI Package 的追溯关系。Raw Zone 保留原始依据，Clean Zone 整理字段和语义，Physical AI Package 形成标准化主数据资产。

## 不属于本模块的职责

真机数据资产模块不是普通 IoT 平台。它不以通用设备联网、设备运维大屏或泛化遥测采集作为核心目标。

它也不是数据湖。Raw Zone 会保留原始数据，但模块价值不在于无限堆放数据，而在于把真实作业转成可复盘、可验证、可筛选、可派生的数据资产。

它不是最终训练框架。Stage 6 只准备 training/evaluation draft outputs，不定义正式训练数据集格式，不承诺训练 pipeline，也不替代后续模型训练系统。

本阶段也不新增生产 connector，不实现 TCP/IP server、SDK bridge、OPC UA/MES/HMI 直连或 DB schema。

## 与 Physical AI Package 的关系

Physical AI Package 是本模块的主标准数据资产。Raw Zone 和 Clean Zone 是进入 package 前后的准备与治理层，不应替代 package。

模块应把标准化后的作业数据组织为：

- `physical_ai_manifest.json`：任务、设备、对象、坐标系和 source dataset。
- `frames.csv`：时间线、机器人位姿、相机帧和作业阶段。
- `events.csv`：报警、异常、状态切换和焊接阶段事件。
- `metrics.csv`：焊接、电气、气体、送丝、速度和风险评分等时序指标。
- `labels.csv`：人工复核或算法标签。
- `artifacts/`：图像、点云、轨迹、source 引用和派生文件。

后续如果真实数据证明现有 schema 不足，应基于小场景试点结果再讨论扩展，而不是在 Stage 6 文档阶段预先固定。

## 与 Rerun 的关系

Rerun 不是产品内核，也不是主数据结构。它在 Stage 6 中定位为可替换 replay backend，适合开发期回放、技术验收和可视化调试。

模块应通过 adapter 从 Physical AI Package 生成 Rerun `.rrd`。这样可以保留 Rerun 的短中期价值，同时避免把产品长期能力绑定到单一 viewer 或存储格式。

当前不 fork Rerun，不做 Rerun 二次开发，也不从零开发 viewer。只有在真实或脱敏小场景跑通后，且明确 Rerun 在权限、标注、协作、部署或现场验收上存在具体不足时，再判断是否需要自研回放工作台。

## 与独立产品路线的关系

真机数据资产模块可以为未来独立产品路线预留空间，但 Stage 6 不把它直接扩成完整独立产品。

可保留的长期方向包括 Robot Data Recorder / Physical AI DataHub：面向机器人真机作业数据的记录、清洗、回放、样本筛选和训练评估准备平台。这个方向需要在至少一个真实或脱敏小场景跑通后，再评估产品边界、部署形态、权限、存储、标注协作和商业模块。

## 第一轮产品升级建议

- 在现有素材/数据模块中增加“真机作业数据资产”的一级视角。
- 用作业窗口组织数据，而不是只按文件夹或素材类型组织数据。
- 在 UI 或文档中区分 Raw Zone、Clean Zone、Physical AI Package、replay artifacts 和 training/evaluation draft outputs。
- 为每个作业数据资产显示来源、任务上下文、设备对象、时间范围、字段完整性和质量检查状态。
- 保留 source artifacts 的追溯入口，避免清洗后无法回到原始依据。
- 把 Rerun 回放作为一个可替换的 replay action，而不是产品内核。
- 第一轮只支持小场景试点和离线/准在线验收，不承诺生产 connector。
