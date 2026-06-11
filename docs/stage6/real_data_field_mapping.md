# 真机字段分层与映射

## 资料来源

本文件基于 `docs/real-data/1.jpg` 和 `docs/real-data/2.jpg` 的 Stage 6 真机接入准备资料，以及已批准的 Stage 6 设计说明整理。

当前资料用于规划第一轮字段分层、优先级和待确认问题，不是生产协议文档。不能仅凭截图推断具体 payload、采样频率、数据库 schema、字段单位或 connector 实现。

## 优先级定义

- P0：第一轮真机试点必须确认。缺少这些字段或语义时，Raw Zone 到 Clean Zone 再到 Physical AI Package 的最小链路会不完整。
- P1：建议纳入第一轮或第二轮。它们能提升复盘、诊断和样本筛选价值，但不一定阻塞最小试点。
- P2：先保留资料和 metadata，不阻塞试点。主要用于后续设备建模、配置追溯、资料管理或产品化增强。

## 字段映射表

| 类别 | 字段 | Stage 6 目标位置 | 优先级 | 第一轮说明 |
| --- | --- | --- | --- | --- |
| 资料 | 焊接机器人模型文件 | Raw Zone artifact；后续可进入 manifest device metadata | P2 | 先作为资料留存，确认文件来源、版本和脱敏边界。 |
| 资料 | 深度相机资料 | Raw Zone artifact；后续可进入 camera metadata | P2 | 先作为资料留存，确认相机型号、配置和标定资料边界。 |
| 资料 | 机械臂资料 | Raw Zone artifact；后续可进入 robot metadata | P2 | 先作为资料留存，确认设备资料与任务数据的关联方式。 |
| 资料 | 焊机资料 | Raw Zone artifact；后续可进入 welder metadata | P2 | 先作为资料留存，确认焊机型号和配置资料边界。 |
| 机械臂 | 机器人控制器中机械臂运行文件 `.lua` | Raw Zone artifact；package artifact 引用 | P1 | 需要确认文件获取方式、版本关系和与任务的绑定方式。 |
| 机械臂 | 机械臂轨迹文件 `.json` | Raw Zone + Clean Zone trajectory；package trajectory artifact | P0 | 需要确认轨迹字段语义、时间信息、坐标系和任务关联。 |
| 机械臂 | 关节实时角度/位置/速度/扭矩 | Clean Zone time series；package metrics 或后续 joint state table | P0 | 需要确认字段来源、时间戳来源、坐标/关节命名和缺失策略。 |
| 机械臂 | 机械臂末端笛卡尔坐标/欧拉角 | Clean Zone pose；package frames | P0 | 需要确认坐标系、姿态表示、时间基准和与相机/焊枪的关系。 |
| 相机 | 焊缝轨迹文件 `.json` | Raw Zone + Clean Zone seam trajectory；package artifact / object relation | P0 | 需要确认焊缝 ID、轨迹点语义、坐标系和与工件的关联。 |
| 相机 | 深度相机点云 | Raw Zone artifact；package point cloud artifact | P1 | 需要确认文件格式、命名规则、时间关联和存储路径。 |
| 相机 | 深度相机 2D 图像 | Raw Zone artifact；package image artifact | P0 | 需要确认图片路径、帧时间、脱敏要求和与机器人位姿的关联。 |
| 相机 | 深度相机拍照时位姿 | Clean Zone pose；package frames / camera pose metadata | P0 | 需要确认位姿来源、坐标系、时间戳和与图像/点云的绑定。 |
| 焊机 | 下发焊接电压/电流/速度 | Clean Zone metrics；package metrics | P0 | 需要确认这些值是下发值、记录值或两者都有，以及时间关联方式。 |
| 焊机 | 焊枪焊接时位置 | Clean Zone pose/event；package frames/events | P1 | 需要确认焊枪位置来源、坐标系和与机器人末端位姿的关系。 |
| 保护气体 | 流量/浓度/压力 | Clean Zone metrics；package metrics | P1 | 需要确认来源系统、时间戳、字段语义和是否进入第一轮试点。 |
| 送丝机 | 送丝速度/出丝长度 | Clean Zone metrics；package metrics | P1 | 需要确认来源系统、时间戳、字段语义和与焊接阶段的关联。 |
| 工艺 | 焊接过程记录 | Raw Zone + events/metrics | P0 | 需要确认记录结构、阶段语义、时间基准和与异常记录的关系。 |
| 工艺 | 焊接工艺记录 | Raw Zone + manifest/task metadata | P1 | 需要确认工艺参数版本、任务绑定方式和是否可脱敏外发。 |
| 工艺 | 焊接异常记录 | events.csv；candidate export 的重要来源 | P0 | 需要确认异常类型、等级、消息、时间戳和关联对象。 |
| 任务 | 焊机时间戳 | 统一时间基准输入 | P0 | 需要确认是否作为主时间源或对齐输入，以及与机器人/相机时间的同步方式。 |
| 任务 | 工单 ID/工件编号 | manifest task/object/source metadata | P0 | 需要确认命名规则、脱敏规则和与作业窗口的关系。 |
| 任务 | 焊缝 ID/任务 ID | manifest task/object/source metadata | P0 | 需要确认任务粒度、焊缝粒度和事件/轨迹如何引用这些 ID。 |
| 任务 | 设备 ID/型号 | manifest devices/source metadata | P0 | 需要确认机器人、相机、焊机和辅机的设备 ID 规则。 |

## 第一轮必须确认的问题

- 数据源 ownership：每类字段由机器人控制器、视觉控制器、HMI、焊机、AI 控制器或其他系统提供。
- 接入形态：第一轮通过 SDK、TCP/IP JSON、文件同步、DB 写入还是离线导出进入 AI 控制器。
- 时间基准：机器人、相机、焊机、工艺记录和异常记录是否使用同一时间源；如果不是，如何对齐。
- 坐标系：机器人末端、相机、焊枪、工件和焊缝轨迹分别使用什么坐标系，转换关系由谁提供。
- 字段单位和语义：必须由现场资料或样例确认，文档阶段不编造单位。
- 文件与 payload 样例：需要真实或脱敏的 SDK/TCP JSON 示例、轨迹文件、图像/点云命名规则和过程记录样例。
- 数据保存位置：Raw Zone、Clean Zone、Physical AI Package 和回放 artifacts 在 AI 控制器上的存储路径与保留策略。
- 脱敏和权限：工单、设备、图片、日志、异常消息和人员信息中哪些内容不能离开现场。

## 暂不决定的问题

- 不决定生产 connector 的协议实现、错误模型、重连策略和部署方式。
- 不决定长期数据库 schema。
- 不决定 Physical AI Package v0.1 schema 扩展。
- 不决定正式训练数据集格式。
- 不决定采样频率、插值策略或 payload 字段类型。
- 不决定是否 fork、二次开发 Rerun 或自研 viewer。
- 不决定 Robot Data Recorder / Physical AI DataHub 的完整独立产品形态。
