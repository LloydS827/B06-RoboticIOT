# S01 Manufacturing Event Context Package Profile

## Profile

| 项目 | 内容 |
| --- | --- |
| profile id | `manufacturing_event_context_package` |
| owning project | S01 系统级制造事件闭环 |
| 当前用途 | 定义制造事件上下文如何引用 B06 输出 |

## 定位

S01 profile 面向系统级制造事件、任务协同和复盘闭环。S01 读取 B06 输出作为事件 evidence、summary、candidate link 或 result reference，但不读取低层机器人轨迹，也不直接消费点云、PCL 中间文件或设备高频时序。

## 信息组

### 制造对象

- 工单、工件、焊缝、设备、产线或工站的脱敏引用。
- 对象层级和对象之间的关系。
- 对象是否允许离开现场或进入系统级摘要。

### 状态

- 任务状态、生产状态、质量状态、设备状态和异常状态。
- 状态来源、更新时间和可信度。
- 状态与 B06 package、candidate 或 result reference 的对应关系。

### 事件

- 事件类型、事件时间、触发来源和影响对象。
- 异常、报警、返修、人工复核、任务派发或质量确认。
- 事件证据可以引用 B06 的 replay、summary、quality result 或 onsite-only source ref。

### 影响范围

- 影响的工件、焊缝、设备、批次、工序或任务。
- 影响等级、持续时间和后续处理状态。
- 与上下游任务、质量追溯或复盘记录的关系。

### 任务

- 待处理任务、责任角色、截止时间和执行状态。
- 任务来源：事件触发、质量复核、人工派发或模型候选。
- 任务可引用 B06 candidate link，但不要求携带低层机器人轨迹。

### 权限

- 谁可以查看事件摘要、证据引用、附件或现场原始数据。
- onsite-only、脱敏可共享、可提交样本等边界。
- 不可提交数据必须保持引用或摘要，不复制到 S01 通用上下文中。

### 执行结果

- 任务执行结论、处理动作、质量结果和复核结论。
- 结果来源、执行人或系统引用。
- 与 B06 result reference、quality label 或 replay artifact 的关联。

### 复盘

- 事件摘要、原因分析、影响评估和后续改进。
- 可引用 B06 输出的 evidence/summary/result reference。
- 复盘文本不应展开低层机器人轨迹、点云或高频时序细节。

## S01 如何读取 B06 输出

| B06 输出 | S01 用法 |
| --- | --- |
| Package manifest / summary | 作为事件上下文和对象引用。 |
| Candidate sample link | 作为待复核或待派发任务的 evidence link。 |
| Rerun replay artifact | 作为研发复盘引用，不作为 S01 主数据结构。 |
| Quality result reference | 作为事件结果、任务结果或复盘结论依据。 |
| Source artifact reference | 仅在权限允许时作为 onsite-only 证据引用。 |

## 非目标

- 不读取低层机器人 TCP、joint、路径点或相机位姿。
- 不读取设备高频时序原始序列。
- 不定义 S01 生产系统权限实现。
- 不复制不可提交现场原始数据。
