# Simulation-first Physical AI Data Package 设计

## 1. 背景

Physical AI 数据层项目已经完成阶段 1 的 Rerun.io 公开资料调研和阶段 2 的本地技术评测。阶段 2 证明：Rerun 可以作为早期实验底座，支持模拟焊接工站数据的记录、`.rrd` 写入、候选样本导出、Catalog/DataFrame 查询尝试和开源机器人小样本对照。

下一阶段不应继续停留在 Rerun 工具验证，也不应直接进入真实现场系统。当前更重要的是把阶段 2 的实验结果转化成 CavLAB 自有的数据层内核：一个可表达 Physical AI 作业过程、可校验、可转换到 Rerun、可继续扩展到训练和评估的数据包规范与原型。

本阶段采用 simulation-first 路线：优先使用仿真/模拟数据确认需求、简化产品形态，再逐步优化和扩展。Rerun 在本阶段继续作为可视化和回放后端直接接入，但业务数据模型不绑定 Rerun。

## 2. 阶段定位

阶段 3 名称：

> Simulation-first Physical AI Data Package

阶段 3 的核心问题是：

> 一个面向 Physical AI 的最小作业数据包，应该如何组织任务、设备、工件、时空关系、物理过程、事件、质量、样本和可视化后端？

阶段 3 的输出不能只是文档，必须包含可运行原型。第一版原型以“开发期诊断工具”为定位：优先帮助研发者看清一个数据包缺什么、错什么、能否转换和回放，不做生产级强约束平台。

## 3. 目标

本阶段目标：

- 定义 CavLAB Physical AI 数据包 v0.1 的最小规范。
- 基于仿真生成两个符合规范的数据包：
  - 主场景：机器人焊接工站；
  - 轻量对照场景：机械臂抓取/分拣。
- 实现一个开发期 validator，能诊断数据包结构、关键字段、文件引用、时间线和坐标系问题。
- 实现一个 Rerun adapter，把自有数据包转换为 `.rrd`，用于验证可视化和回放效果。
- 保留阶段 2 已验证的候选样本导出和 Rerun 能力，但把它们放在 CavLAB 自有数据包之后。
- 为后续样板场景链路、训练导出和产品化 CLI 打基础。

## 4. 非目标

本阶段不做以下事情：

- 不接入机器人真机。
- 不引入 ROS/Gazebo/MoveIt 作为默认依赖。
- 不构建数据库、Web 平台、权限系统或多人协作系统。
- 不实现完整标注平台。
- 不做生产级数据治理、脱敏、审计和客户现场部署。
- 不 fork Rerun，不修改 Rerun Viewer 源码。
- 不承诺 Rerun 是长期唯一后端。
- 不把 schema 一次性设计成覆盖所有机器人和工业场景的完整标准。

## 5. 设计原则

### 5.1 确认需求

第一版数据包必须能回答以下问题：

- 这是谁的一次作业？
- 使用了哪些设备、工件、工具和传感器？
- 作业发生在什么时间线和坐标系中？
- 物理过程中产生了哪些帧、事件、参数、图像、点云和轨迹？
- 结果质量如何，哪些片段值得复盘或导出？
- 能否转换到 Rerun 进行可视化回放？

### 5.2 简化

第一版只做最小闭环：

- 一个 manifest；
- 几张核心表；
- 一个 artifacts 目录；
- 一个 validator；
- 一个 Rerun adapter；
- 两个仿真样例。

能用清晰字段表达的内容，不先引入复杂插件、数据库或服务端。

### 5.3 优化

优化发生在验证之后：

- 通过两个仿真场景发现 schema 是否过窄；
- 通过 validator 发现数据包最容易出错的地方；
- 通过 Rerun adapter 发现哪些字段适合直接映射，哪些需要自有抽象；
- 通过候选导出发现哪些数据能进入训练和评估流程。

## 6. 场景范围

### 6.1 主场景：机器人焊接工站

焊接工站用于验证复杂工业过程数据：

- 机器人 TCP 轨迹；
- 工件和焊缝；
- 相机图像；
- 简化点云；
- 工艺参数；
- 起弧、异常、收弧等事件；
- 缺陷概率和质量结果；
- 候选样本导出。

该场景强调工艺过程、质量追溯和多模态复盘。

### 6.2 轻量对照场景：机械臂抓取/分拣

抓取/分拣用于验证 schema 的通用性，但保持在团队熟悉的机械臂能力圈内：

- 机械臂状态；
- 末端执行器动作；
- 相机图像；
- 目标物体；
- 抓取或分拣动作；
- 成功/失败结果；
- 可训练样本片段。

该场景强调感知、动作、结果和具身智能训练数据结构。

### 6.3 暂缓场景

移动机器人巡检暂缓。它有助于验证更广义的空间移动和巡检任务，但会引入导航、地图、定位和路径规划语义，容易让阶段 3 范围膨胀。后续在机械臂主线跑通后再引入。

## 7. 数据包规范 v0.1

### 7.1 目录结构

第一版数据包采用目录结构，不引入数据库：

```text
package_root/
  physical_ai_manifest.json
  frames.csv
  events.csv
  labels.csv
  metrics.csv
  artifacts/
    images/
    point_clouds/
    trajectories/
  derived/
    candidates.csv
  README.md
```

说明：

- `physical_ai_manifest.json` 是数据包主入口。
- `frames.csv` 记录按时间展开的过程帧。
- `events.csv` 记录离散事件。
- `labels.csv` 记录质量、结果或训练标签。
- `metrics.csv` 记录工艺参数、模型输出或过程指标。
- `artifacts/` 存放图像、点云、轨迹等文件。
- `derived/` 存放可再生成的派生结果。
- `README.md` 记录该包的样例说明，不作为机器校验依据。

### 7.2 Manifest 最小字段

`physical_ai_manifest.json` 必须包含：

- `schema_version`：例如 `physical-ai-package/v0.1`。
- `package_id`：数据包唯一标识。
- `scenario_type`：例如 `robot_welding_station` 或 `arm_pick_sort`。
- `created_at`：数据包生成时间。
- `task`：作业任务信息。
- `devices`：机器人、相机、传感器、工具等设备。
- `objects`：工件、目标物、夹具等物理对象。
- `coordinate_frames`：坐标系定义。
- `timelines`：时间线定义。
- `tables`：核心表文件路径和用途。
- `artifacts`：附件目录和类型。

`rerun` 为可选字段，用于记录 Rerun entity path 或显示提示。Validator v0.1 不要求该字段存在；adapter 在没有 `rerun` 字段时必须使用默认映射规则。

Manifest 第一版采用 JSON 文件，不引入 JSON Schema 作为强依赖；实现时可以用 Python 结构化校验逐步逼近 schema。

### 7.3 坐标系和引用约定

`coordinate_frames` 最小结构为数组，每个元素至少包含：

- `frame_id`：坐标系 ID，例如 `station`、`robot_base`、`tcp`、`camera_front`。
- `parent_frame_id`：父坐标系 ID；根坐标系可为空字符串。
- `pose_ref`：可选，相对 `artifacts/` 的位姿文件路径；为空字符串表示该坐标系在 v0.1 中没有单独文件，adapter 可使用默认或表内位姿。

`timelines` 最小结构为数组，每个元素至少包含：

- `timeline_id`：时间线 ID，例如 `sim_time`、`robot_tick`、`camera_frame`。
- `unit`：时间线单位，例如 `s`、`tick`、`frame`。

v0.1 样例包的 `timelines` 必须包含 `sim_time`，用于事件、指标和候选帧归属的默认时间线。

v0.1 统一引用约定：

- 以 `_id` 结尾的字段引用表内或 manifest 中定义的 ID。
- 以 `_ref` 结尾的字段引用相对 `package_root` 的文件路径，除非该字段在本节另有说明。
- 空引用统一使用空字符串，不使用 `null`。
- `frame_id`、`event_id`、`label_id`、`metric_id` 不允许为空。
- `image_ref`、`point_cloud_ref`、`trajectory_ref` 为空时表示该帧没有对应 artifact，不构成 error；非空时文件必须存在。
- `robot_state_ref` 和 `tcp_pose_ref` v0.1 视为相对文件路径；为空时 adapter 可以只使用 `frames.csv` 中的普通字段或跳过对应几何。

### 7.4 核心表

`frames.csv` 最小字段：

- `frame_id`
- `timestamp_s`
- `timeline`
- `phase`
- `coordinate_frame_id`
- `robot_state_ref`
- `tcp_pose_ref`
- `image_ref`
- `point_cloud_ref`
- `trajectory_ref`

`events.csv` 最小字段：

- `event_id`
- `timestamp_s`
- `event_type`
- `severity`
- `message`
- `related_frame_id`
- `related_object_id`

`labels.csv` 最小字段：

- `label_id`
- `label_type`
- `target_ref`
- `value`
- `confidence`
- `source`

`metrics.csv` 最小字段：

- `metric_id`
- `timestamp_s`
- `metric_name`
- `value`
- `unit`
- `source`

场景特有字段可以追加，但 validator v0.1 只要求最小字段存在且类型可解析。

`frames.coordinate_frame_id` 必须引用 manifest 中的 `coordinate_frames.frame_id`。`frames.timeline` 必须引用 manifest 中的 `timelines.timeline_id`。

`labels.target_ref` v0.1 支持两种形式：

- `frame:<frame_id>`：标签归属某一帧；
- `object:<object_id>`：标签归属 manifest `objects` 中的对象。

v0.1 中，`events.timestamp_s` 和 `metrics.timestamp_s` 均默认属于 `sim_time`。如果后续版本需要多 timeline 事件或指标，再为 `events.csv` 和 `metrics.csv` 增加显式 `timeline` 字段。

`metrics.timestamp_s` 归属候选帧时，按 `sim_time` 上时间差最小的 `frames.timestamp_s` 匹配。

## 8. Validator 设计

### 8.1 定位

Validator v0.1 是开发期诊断工具，不是生产级验收系统。它应尽量输出清楚的问题报告，帮助研发者修正数据包，而不是只返回失败。

### 8.2 校验内容

第一版校验：

- 目录是否存在；
- `physical_ai_manifest.json` 是否存在且 JSON 可解析；
- 必填 manifest 字段是否存在；
- `schema_version` 是否为支持版本；
- 核心表是否存在；
- 核心表必填列是否存在；
- 非空 `_ref` 文件引用是否存在；
- `timestamp_s` 是否可解析为数值；
- `frame_id`、`event_id`、`label_id` 等关键 ID 是否非空；
- `frames.coordinate_frame_id` 是否引用 manifest 中声明的坐标系；
- `frames.timeline` 是否引用 manifest 中声明的时间线；
- `labels.target_ref` 是否符合 v0.1 支持的引用形式；
- 场景类型是否为 v0.1 支持集合。

### 8.3 输出

Validator 输出分为：

- `errors`：会阻止转换或基本使用的问题；
- `warnings`：不阻止转换，但可能影响复盘、导出或后续扩展的问题；
- `summary`：数据包概览，例如帧数、事件数、标签数、artifact 数、场景类型。

CLI 第一版可以输出人类可读文本和 JSON 两种格式。

## 9. Rerun Adapter 设计

### 9.1 定位

Rerun adapter 是外围转换层：

```text
CavLAB Physical AI package -> validator -> Rerun adapter -> .rrd
```

业务代码不直接以 Rerun entity path 作为主 schema。Rerun 映射可以变化，但 CavLAB 数据包结构保持稳定。

### 9.2 映射原则

- `coordinate_frames` 映射为 Rerun Transform3D；缺少 `pose_ref` 的静态坐标系使用默认 identity transform 或场景生成器提供的表内位姿。
- 图像 artifact 映射为 Rerun Image。
- 点云 artifact 映射为 Rerun Points3D。
- 轨迹 artifact 映射为 Rerun LineStrips3D。
- metrics 映射为 Rerun Scalars。
- events 映射为 Rerun TextLog 或事件 entity。
- labels 映射为结果/质量/训练样本上下文。

### 9.3 后端边界

Rerun adapter 不负责定义业务语义，只负责解释 CavLAB 数据包并转换为 Rerun 可视化对象。未来可以增加其他 adapter，例如 Parquet、LeRobot、MCAP 或自有 viewer。

## 10. 查询与导出

阶段 3 保留一个最小查询/导出能力，用于证明数据包不仅能看，还能被整理：

- 按 `event_type`、`label_type`、`metric_name` 或 `confidence` 筛选候选帧；
- 输出 `derived/candidates.csv`；
- 候选导出必须从 CavLAB 数据包读取，而不是从 Rerun `.rrd` 反推；
- Rerun DataFrame/Chunk 查询作为对照能力继续记录，但不作为第一版核心依赖。

`derived/candidates.csv` 是派生产物，样例包初始生成时可以不存在；运行候选导出命令后必须生成。Validator 默认不要求该文件存在，但如果 manifest 或用户显式声明该派生产物，则应检查文件是否存在。

候选帧归属规则：

- event 候选：使用 `events.related_frame_id`；为空时按 `events.timestamp_s` 匹配最近帧。
- label 候选：`labels.target_ref` 为 `frame:<frame_id>` 时直接归属该帧；为 `object:<object_id>` 时按实现阶段定义的场景规则扩展，v0.1 可以只输出 object-level 候选。
- metric 候选：按 `metrics.timestamp_s` 匹配最近帧。
- 多个来源命中同一帧时，输出一行候选，聚合命中原因。

`derived/candidates.csv` 最小列：

- `candidate_id`
- `source_type`
- `source_id`
- `frame_id`
- `object_id`
- `timestamp_s`
- `reasons`
- `score`

其中 `source_type` 可为 `event`、`label`、`metric` 或 `mixed`；`object_id` 和 `score` 可为空字符串。

## 11. CLI 形态

第一版 CLI 必须提供以下能力，具体命名在 implementation plan 中确定：

- 生成焊接工站样例包；
- 生成机械臂抓取/分拣样例包；
- 校验数据包；
- 汇总数据包；
- 转换为 Rerun `.rrd`；
- 导出候选样本。

这些命令都应是本地文件系统命令，不要求服务端。

## 12. 测试策略

阶段 3 的实现计划应覆盖以下测试：

- manifest 必填字段缺失时 validator 能报告 error；
- 核心表缺列时 validator 能报告 error；
- artifact 引用不存在时 validator 能报告 error；
- 非阻塞问题能进入 warning；
- 焊接样例包能通过 validator；
- 抓取/分拣样例包能通过 validator；
- 两个样例包都能转换为 `.rrd`；
- `.rrd` 能通过 `rerun rrd verify`；
- 候选样本导出能产生稳定 CSV；
- CLI 参数错误能返回非零状态和清楚错误信息。

## 13. 成功标准

阶段 3 完成时，至少应满足：

- 有一份 CavLAB Physical AI 数据包 v0.1 设计说明。
- 有两个可生成的仿真数据包：焊接工站和机械臂抓取/分拣。
- 两个数据包都能通过 validator。
- Validator 能对刻意构造的错误包给出清楚诊断。
- 两个数据包都能转换为 Rerun `.rrd` 并通过 Rerun CLI 校验。
- 能导出一个最小候选样本 CSV。
- README、details 和阶段报告能说明本阶段完成了什么、没完成什么、下一步是什么。

理想但非必须：

- 完成 Viewer/Blueprint 人工检查记录；
- 完成小规模性能冒烟记录；
- 初步形成 schema 演进规则。

## 14. 风险与应对

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| Schema 过早复杂化 | 拖慢原型，难以验证 | v0.1 只要求最小字段，场景特有字段作为扩展 |
| Schema 被焊接场景绑定 | 后续通用性不足 | 加入机械臂抓取/分拣轻量对照场景 |
| Rerun 映射反向污染业务模型 | 后续替换困难 | CavLAB package 是主模型，Rerun 只做 adapter |
| Validator 变成生产级规则引擎 | 阶段范围膨胀 | v0.1 只做开发期诊断 |
| 仿真数据太假 | 对真实业务帮助有限 | 保持字段语义贴近机械臂作业，后续阶段再接真实样板 |
| CLI 数量过多 | 使用和维护复杂 | 第一版只保留生成、校验、汇总、转换、导出 |

## 15. 后续阶段衔接

阶段 3 完成后，建议进入：

### 阶段 4：样板场景链路原型

围绕一个具体机械臂作业，把数据包生成、校验、回放、候选导出、人工复核和问题定位串成链路。

### 阶段 5：数据集整理与训练导出

基于数据包和候选样本，设计标签、失败案例、训练/评估拆分和导出格式。

### 阶段 6：最小产品化 CLI 或界面

把阶段 3 和阶段 4 的能力收敛成研发人员可持续使用的工具入口。

### 阶段 7：治理与现场化

在真实场景和工具链稳定后，再考虑权限、审计、脱敏、数据分级、长期存储和客户现场部署。

## 16. 待用户 review

本 spec 明确了阶段 3 的设计方向。用户 review 通过后，下一步进入 implementation plan，不直接开始编码。
