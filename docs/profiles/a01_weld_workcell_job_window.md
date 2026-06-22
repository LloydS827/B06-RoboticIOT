# A01 Weld Workcell Job Window Profile

## Profile

| 项目 | 内容 |
| --- | --- |
| profile id | `weld_workcell_job_window` |
| owning project | A01 智能焊接工站 / H300 |
| 当前用途 | 定义 H300 最小焊接作业窗口给 B06 的数据 contract |
| 实现状态 | 文档 contract 和样本请求，不是完整 schema 实现 |

## 最小窗口

最小窗口建议覆盖一个 `job_window_id`，绑定一个工单、一个任务、一个工件和一条焊缝。时间范围以 3-10 秒为第一轮样本粒度，至少能看清 `approach`、`weld`、`cooldown` 等关键阶段之一或多个阶段。

这个窗口用于验证 Raw Zone -> Clean Zone -> Physical AI Package -> replay/candidate/training draft 的链路，不要求一次覆盖完整班次、完整工艺卡或生产数据库。

## 信息组

### 作业任务

- `work_order_id`：工单或脱敏后的工单引用。
- `task_id`：焊接任务或作业步骤。
- `job_window_id`：本次最小窗口唯一标识。
- 阶段：例如 `approach`、`weld`、`cooldown`、`review`。
- 时间窗口：开始时间、结束时间、时间基准和时区说明。

### 工件与焊缝

- `part_id`：工件或脱敏工件编号。
- `seam_id`：焊缝编号或脱敏焊缝引用。
- 焊缝几何、轨迹文件或 CAD/工装中的焊缝引用。
- 工件、工装、焊缝坐标系的来源和版本。

### 点云与 PCL

- 原始点云文件引用，真实数据默认不提交。
- 脱敏点云或裁剪点云引用。
- PCL 输出，例如分割、配准、焊缝提取或特征点文件。
- 点云坐标系、采集时间、相机/传感器来源。

### 相机位姿

- 相机内参、外参和版本。
- 相机到工站、机器人 base、工件或焊缝坐标系的关系。
- 图像或点云采集时的相机位姿。
- 位姿来源：标定文件、视觉控制器输出或人工配置。

### 机器人位姿

- TCP 位姿、joint 状态和采样频率。
- base/tool/frame 假设和坐标系定义。
- 焊枪、末端执行器或工具中心点的版本说明。
- 位姿与相机、工件、焊缝之间的时间对齐关系。

### 标定参数

- 相机标定参数和版本。
- 手眼标定参数和版本。
- 工件、工装、机器人 base、tool frame 的关系。
- 标定有效时间、来源和复核状态。

### 路径点

- 规划路径点。
- 实际执行路径点。
- 人工修正路径点。
- 路径点与 TCP、焊缝、工艺阶段的绑定关系。

### 工艺参数

- 电流、电压、速度、送丝、保护气等可得字段。
- 下发值、实际记录值和采样频率的区分。
- 参数版本、工艺卡引用或脱敏工艺配置引用。

### 模型输出

- 焊缝检测、定位、点云处理、路径规划、质量预测等中间输出。
- 输出置信度、模型版本、输入引用和时间戳。
- 未经确认的模型输出只能作为候选或上下文，不自动成为训练标签。

### 人工修正

- 示教、拖动、路径修正和专家确认记录。
- 修正前后路径差异。
- 审查人、审查时间和审查结论的脱敏引用。

### 执行日志与异常

- 状态切换、事件、异常、重试和报警。
- 事件等级、来源系统、关联对象和时间戳。
- 异常原因若含现场敏感信息，应保留脱敏摘要或 onsite-only 引用。

### 质量结果

- 外观、尺寸、缺陷、合格/不合格和复核结论。
- 质量结果来源：人工复核、检测系统、返修记录或抽检记录。
- 质量标签应能追溯到窗口、焊缝和 reviewer/source。

## B06 映射

| 层级 | 映射方式 |
| --- | --- |
| Raw Zone | 保留 H300 原始 payload、点云、图像、轨迹、PCL 输出、日志和来源文件引用。真实或未脱敏数据不可提交。 |
| Clean Zone | 对齐当前 `weld_workcell` 离线 contract，整理为 `job.json`、`frames.csv`、`process.csv`、`events.csv`、`review_labels.csv` 等中间文件。 |
| Physical AI Package | 生成可验证 package，用于 Rerun replay、candidate sample export 和 training/evaluation draft。 |
| A02 handoff | 只把经确认的轨迹、TCP、路径点、质量标签、专家审查和失败边界作为 evidence/context 交给 A02。 |

## 非目标

- 不定义 H300 完整生产协议。
- 不实现生产 connector、TCP/IP server、SDK bridge、OPC UA、MES、HMI、PLC 直连或 DB ingestion。
- 不设计长期 DB schema。
- 不修改 Physical AI Package v0.1 schema。
- 不把仿真 fixture 写成现场协议。
- 不提交未脱敏真实数据或现场敏感文件。
