# Rerun.io 第一轮公开资料调研

## 1. 调研元信息

- 调研日期：2026-06-06
- 调研对象：Rerun.io / Rerun 开源仓库 / rerun-sdk
- 版本基线：`rerun-sdk 0.33.0`，PyPI 上传时间为 2026-05-29；GitHub 存在 `0.33.0` 标签
- 调研方法：官方文档、官方 GitHub 仓库、PyPI 包信息交叉验证
- 当前边界：本轮尚未进行本地安装、样例运行、性能压测、源码逐模块阅读和客户现场数据适配

## 2. 关键结论

Rerun.io 当前已经不只是“机器人数据可视化工具”，而是在公开定位上明确走向 Physical AI 数据层：围绕 logging、visualization、query、transform、training 和 catalog 形成一套多模态时序数据基础设施。

对本项目而言，Rerun 具有三类价值：

1. **架构借鉴价值很高**：Entity Path、Archetype/Component、多 timeline、Transform、Arrow chunk、recording/segment/dataset/catalog 这些概念，和我们要解决的机器人现场数据组织问题高度一致。
2. **原型复用价值很高**：Python SDK、Viewer、`.rrd`、MCAP 转换、OSS catalog、DataFrame 查询、LeRobot 导出，可以直接支撑第一轮样板场景实验。
3. **产品化仍需谨慎**：权限、审计、数据分级、客户现场私有化、工艺语义、质量追溯、长期数据治理、Rerun Hub 商业能力边界等，不能直接假设由 Rerun 开源部分解决。

初步路线建议是：**短期用 Rerun 做实验底座，中期在 Rerun 外层建立自有数据规范和 SDK 适配层，长期根据性能、许可、部署和产品可控性决定深度二开或自研替代。**

## 3. 官方定位

Rerun 官方文档将其描述为 Physical AI 的统一数据层，用于记录、可视化、查询、转换和训练多频、多模态、时序数据。Getting Started 文档强调它面向 robotics 和 Physical AI 团队，支持从传感器记录数据、在 Viewer 中可视化、用 dataframe 查询，并通过 dataloader 进入机器人学习训练。

这与我们项目启动说明中的目标高度重合：多源数据接入、多模态记录、时空对齐、回放、数据集整理、训练与评估导出。

但 Rerun 的公开定位偏研发数据层和机器人学习数据层；我们还需要覆盖制造现场的工艺系统、质量追溯、客户敏感数据治理、项目交付和业务权限，这些属于我们自有产品边界。

## 4. 系统组成

根据官方 Concepts 文档，Rerun 主要由以下部分构成：

| 组成 | 作用 | 对本项目判断 |
| --- | --- | --- |
| Logging SDK | 在应用内记录数据，支持 Python、Rust、C++ | 直接复用做实验，后续封装自有 SDK |
| Recording Stream | 承载应用产生的一条数据流，可保存为 `.rrd` 或发送到 Viewer/server | 借鉴为“作业记录流” |
| Viewer | 原生或 Web 可视化，多模态同步回放 | 直接复用做研发复盘 |
| Chunk Store | Viewer 内部的时间感知内存数据库 | 借鉴其时间索引和列式组织 |
| CLI | 打开、检查、转换、过滤 `.rrd` / `.mcap`，启动 server | 直接复用实验 |
| Catalog Server | 管理多 recording，并提供持久化、索引和查询 | 实验阶段复用，产品化需评估 |
| Catalog SDK | Python 查询、过滤、转换 catalog 数据 | 封装复用 |
| Rerun Hub | 商业化高性能后端和协作能力 | 公开资料调研，暂不作为开源能力假设 |
| Dataloader | 将 catalog 数据作为 PyTorch dataset 使用 | 实验性能力，需验证 |

## 5. 数据模型

### 5.1 Entity / Component / Archetype

Rerun 数据模型借鉴 ECS 思路：entity 表示对象，component 表示对象上的数据，archetype 是面向 SDK 和 Viewer 的高层组件包，例如点云、图像、Transform、时间序列等。

对我们有直接借鉴价值：

- `robot/base`、`robot/tcp`、`camera/front`、`workpiece/current`、`weld/seam_001` 可映射为 entity path；
- 位姿、速度、电参、图像、点云、模型输出、质量反馈可映射为 components 或 archetypes；
- 高层业务对象可以通过命名规范和自有 schema 建立在 Rerun 数据模型之上。

需要注意的是，Rerun 的内置类型偏通用机器人/空间数据；焊接工艺参数、工件序列、工艺卡、质检结果、人工修正、异常事件等业务语义，需要我们自定义规范。

### 5.2 Entity Path

Entity Path 是 Rerun 组织数据的核心层级路径。SDK 的 `log()` 第一个参数就是路径，每次向同一路径记录数据，等价于沿 timeline 更新该 entity。

这对本项目非常关键，因为机器人现场数据天然是层级结构：

- 工站 / 任务 / 工件；
- 机器人 / 关节 / TCP；
- 相机 / 内参 / 外参 / 图像；
- 工艺 / 焊缝 / 参数 / 电流电压；
- 算法 / 检测框 / 分割结果 / 置信度；
- 质量 / 缺陷 / 返修 / 人工确认。

建议后续专门制定 `entity_path` 命名规范，避免不同项目各自随意命名导致数据不可复用。

### 5.3 Timeline 与 Event

Rerun 的每条数据可关联一个或多个 timeline。SDK 默认创建 `log_tick` 和 `log_time`，也支持自定义时间线。这个机制适合处理机器人和现场系统常见的多时间基准问题：

- 系统接收时间；
- 传感器采集时间；
- 机器人控制周期；
- 相机帧号；
- PLC 扫描周期；
- 工艺任务阶段；
- 质量判定时间。

建议直接借鉴多 timeline 模型，并在自有规范中明确哪些 timeline 必填、哪些可选，以及如何处理时钟漂移、设备断连和补录数据。

### 5.4 Transform 与坐标系

Rerun 支持空间关系和坐标系建模，并在文档中明确提到可用 named transform frame 更贴近 ROS `tf2` 的表达方式。它适合表达机器人、相机、工件、世界坐标、TCP、点云和视觉结果之间的关系。

对本项目来说，Transform 机制应直接借鉴，但坐标系命名、标定版本、工件装夹、焊缝局部坐标、离线/在线坐标差异，需要形成自有现场规范。

### 5.5 Static Data

Rerun 支持 static data，用于表示跨所有 timeline 都成立的数据，例如标定参数、相机内参、固定几何、标签上下文等。

这非常适合记录：

- 相机内参；
- 机器人 base/world 固定变换；
- 工件 CAD 或简化模型；
- 本次任务配置；
- 类别颜色和标签说明；
- 设备静态元数据。

## 6. 存储与数据组织

### 6.1 `.rrd` Recording

Rerun 将 recording 解释为 `.rrd` 文件或由 logging process 生成的一条数据流。多个进程或机器可产生共享 recording ID / application ID 的文件，并在 Viewer 或 catalog 中合并为逻辑 recording。

这对我们的多设备现场数据链路很有价值：相机、机器人控制、焊机电参、算法输出、HMI 操作可以分进程记录，再统一进入一次作业回放。

### 6.2 Chunk 与 Arrow

Rerun 的核心数据结构是 chunk。官方文档说明 chunk 是 Arrow 编码、列式的二进制数据表，行由 row id、timestamp 和 component batch 组成。它也支持 columnar API，例如 `send_columns`、`send_dataframe`，并与 PyArrow Table 结合。

这说明 Rerun 的底层思路与多频、多模态、稀疏时序数据非常匹配。对我们来说，值得重点借鉴：

- 列式组织，而不是把所有传感器强行拼成统一频率表；
- 稀疏数据按 entity/component/timeline 组织；
- 面向查询和训练导出的 Arrow/DataFrame 接口；
- 原始记录和后处理结果可以以相同数据模型表达。

### 6.3 Catalog / Segment / Dataset

Rerun 的 catalog 将顶层对象组织为 entries，其中包括 table 和 dataset。Dataset 可由多个 segment 组成，segment 可以理解为一次 recording、一次 episode 或一段 trajectory。

这与我们“作业记录 -> 样本包 -> 数据集 -> 训练/评估”的链路高度接近。建议直接借鉴：

- 一次真实作业作为 segment；
- 一个工站或一个任务类型形成 dataset；
- 失败案例库、质量案例库、训练样本集可以作为不同 dataset 或 dataset view。

但 catalog 的权限、多用户、长期存储、高性能后端与 Rerun Hub 有关，开源部分能满足到什么程度需要实测。

## 7. 可视化与回放

Rerun Viewer 是当前最适合直接复用的部分。它支持同步查看图像、点云、3D 空间、时间序列、日志和表格，适合快速建立样板场景复盘能力。

Blueprint 是一个重要概念：它可以保存 Viewer 的布局、视图和可视化配置。对我们而言，Blueprint 可借鉴为“场景回放模板”：

- 焊接工站回放模板；
- 移动机器人定位调试模板；
- 视觉检测复盘模板；
- 模型输出和人工修正对比模板。

需要验证的风险：

- Web Viewer 有内存和性能限制，官方文档提到 Web Viewer 受 Wasm 32-bit 和单线程限制；
- 大规模点云、多相机长视频和长周期作业回放性能未知；
- 现场用户需要的业务面板、操作审计和异常闭环，不一定适合直接在 Rerun Viewer 内完成。

## 8. 查询、转换与训练

### 8.1 DataFrame 查询

Rerun 的 DataFrame 查询面向机器人和传感器数据的多频、稀疏、多 timeline 问题。官方文档说明它可以在 Viewer 中交互使用，也可以通过 Catalog SDK 程序化使用；查询返回 DataFusion dataframe，并可转为 Pandas、Polars、PyArrow 等格式。

对我们而言，这可能是从回放工具走向训练数据层的关键能力：

- 按任务、工件、时间段、异常事件筛选数据；
- 将机器人位姿、图像、点云、工艺参数按指定 timeline 对齐；
- 将失败案例导出为训练样本；
- 将模型输出和人工修正合并为标注数据。

### 8.2 Lenses

Rerun 的 Lenses API 用于从已有数据中抽取、重塑和重路由 component，官方标注为 experimental。它对我们有启发意义：后处理、标注修正、格式转换、业务字段派生可以用类似“数据变换层”表达。

但由于 API 仍为实验性质，不建议第一阶段把它作为稳定产品基础。

### 8.3 LeRobot 导出与 PyTorch DataLoader

Rerun 官方提供从 catalog 导出 LeRobot dataset 的指南，也提供实验性的 `rerun.experimental.dataloader`，可把 catalog 数据作为 PyTorch iterable/map-style dataset 使用。

这对具身智能训练链路很有价值，但需要谨慎：

- 训练接口仍有 experimental 标记；
- 大规模训练官方建议考虑 Rerun Hub 的高性能后端；
- 我们需要确认自己的样本格式、标签规范、质量反馈和训练目标是否能自然映射到 LeRobot 或 PyTorch Dataset。

## 9. 导入与集成

Rerun 的 importer 机制是二次开发重点。官方文档说明 external importer 可以是任意语言编写的独立可执行文件，只要命名符合 `rerun-importer-*` 并在标准输出中输出 Rerun 数据，即可被 Viewer/SDK 自动发现。也支持 custom Rust importer。

这对本项目非常重要，因为制造现场会有大量非标准数据源：

- 机器人控制器日志；
- PLC/HMI 操作记录；
- 焊机电参；
- 工艺系统 CSV/数据库导出；
- 视觉算法中间结果；
- 厂内中台事件；
- 客户现场脱敏数据包。

建议优先使用 external importer 路线做实验，因为它能避免一开始深入修改 Rerun 源码，同时保留未来替换空间。

MCAP 支持也值得关注。Rerun CLI 包含 `rerun mcap` 子命令，可以转换和检查 `.mcap` 文件；类型系统中也有 MCAP 相关 archetypes/components。对于 ROS 2 或 Foxglove 生态的数据链路，这是直接可复用入口。

## 10. 许可证与开源边界

Rerun GitHub 仓库公开，README 显示 MIT 和 Apache 双许可证标识，仓库中存在 `LICENSE-MIT` 和 `LICENSE-APACHE` 文件。这对内部研究、实验、原型集成和二次开发是积极信号。

但还需要继续确认：

- 所有核心 crate、SDK、Viewer、Catalog OSS 部分是否完全适用同一许可证；
- Rerun Hub、商业后端、协作能力、权限能力是否闭源或受商业条款约束；
- 如果未来嵌入或分发 Viewer，商标、品牌、第三方依赖和许可证 NOTICE 如何处理。

## 11. 对本项目的路线判断

### 11.1 应直接借鉴

- Physical AI data layer 的产品边界；
- Entity Path 层级数据组织；
- Archetype/Component/Datatype 的类型分层；
- 多 timeline 和 event 模型；
- Transform / coordinate frame 机制；
- Arrow chunk 和列式稀疏时序存储思路；
- Blueprint 作为回放模板；
- recording / segment / dataset / catalog 的数据资产层级。

### 11.2 可直接复用做实验

- Python SDK；
- Viewer；
- `.rrd` 文件；
- CLI；
- OSS catalog server；
- MCAP 转换；
- DataFrame 查询；
- LeRobot 导出样例。

### 11.3 应优先封装复用

- 自有 `entity_path` 命名规范；
- 自有任务上下文和工艺参数 schema；
- 自有 SDK wrapper；
- 自有数据包目录结构；
- 自有训练导出流程；
- 自有 importer 规范。

### 11.4 可考虑二次开发

- External importer；
- Custom Rust importer；
- Viewer 扩展；
- Web Viewer 嵌入；
- Catalog SDK 上的数据整理和转换流程；
- 基于 Rerun 数据模型的标注/修正工具。

### 11.5 建议自研或单独建设

- 客户现场数据权限、审计、脱敏和分级；
- 质量追溯业务模型；
- 工艺任务和工件模型；
- 失败案例库和人工修正流程；
- 长期项目资产管理；
- 与 CavLAB 内部项目、中台和交付体系的集成。

## 12. 风险与待验证项

| 风险 | 说明 | 后续验证 |
| --- | --- | --- |
| 性能未知 | 点云、长视频、多设备、多小时 recording 需要实测 | 本地样例与真实数据压测 |
| Web Viewer 限制 | 官方说明 Web Viewer 受 Wasm 32-bit 和单线程限制 | 对比 Native Viewer 与 Web Viewer |
| 训练接口实验性 | dataloader 与 lenses 仍有 experimental 属性 | 只做实验，不作为近期稳定产品承诺 |
| 商业能力边界 | Hub、协作、权限、高性能后端不等于 OSS 能力 | 调研开源/商业边界 |
| 业务语义缺失 | Rerun 不会天然理解焊接工艺和质量追溯 | 建立自有 schema |
| 数据治理不足 | 客户现场敏感数据、权限、审计需自研 | 另起数据治理规范 |
| 二开成本未知 | Viewer/Rust 深度定制需要源码阅读 | 后续源码结构调研 |

## 13. 下一步建议

1. 建立第一轮本地 Rerun 实验目录和 Python 环境。
2. 使用 Python SDK 生成最小多模态 recording：图像、点云、位姿、轨迹、日志、事件、工艺参数。
3. 使用 Viewer 验证回放、时间轴、坐标系、Blueprint 保存。
4. 使用 OSS catalog 注册多个 `.rrd`，验证 DataFrame 查询和跨 segment 筛选。
5. 尝试导出 LeRobot 或 PyTorch DataLoader 样例，判断训练链路可用性。
6. 设计一个 external importer，将模拟现场 CSV/JSON/图像目录转换为 Rerun recording。
7. 在实验后更新二次开发矩阵，将“初判”改为“已验证/不适用/需替代”。

## 14. 本轮主要来源

- Rerun 官方文档索引：<https://rerun.io/llms.txt>
- What is Rerun：<https://rerun.io/docs/overview/what-is-rerun>
- Getting Started：<https://rerun.io/docs/getting-started.md>
- How does Rerun work：<https://rerun.io/docs/concepts/how-does-rerun-work.md>
- Recordings：<https://rerun.io/docs/concepts/logging-and-ingestion/recordings.md>
- Entities and Components：<https://rerun.io/docs/concepts/logging-and-ingestion/entity-component.md>
- Entity Path：<https://rerun.io/docs/concepts/logging-and-ingestion/entity-path.md>
- Timelines：<https://rerun.io/docs/concepts/logging-and-ingestion/timelines.md>
- Transforms：<https://rerun.io/docs/concepts/logging-and-ingestion/transforms.md>
- Static Data：<https://rerun.io/docs/concepts/logging-and-ingestion/static.md>
- Chunks：<https://rerun.io/docs/concepts/logging-and-ingestion/chunks.md>
- Blueprints：<https://rerun.io/docs/concepts/visualization/blueprints.md>
- DataFrame Queries：<https://rerun.io/docs/concepts/query-and-transform/dataframe-queries.md>
- Catalog Object Model：<https://rerun.io/docs/concepts/query-and-transform/catalog-object-model.md>
- Lenses：<https://rerun.io/docs/concepts/query-and-transform/lenses.md>
- Train：<https://rerun.io/docs/concepts/train.md>
- Dataloader：<https://rerun.io/docs/howto/train/dataloader.md>
- LeRobot Export：<https://rerun.io/docs/howto/train/lerobot_export.md>
- Importers：<https://rerun.io/docs/concepts/logging-and-ingestion/importers/overview.md>
- MCAP Message Formats：<https://rerun.io/docs/concepts/logging-and-ingestion/mcap/message-formats.md>
- CLI Manual：<https://rerun.io/docs/reference/cli.md>
- Rerun GitHub：<https://github.com/rerun-io/rerun>
- rerun-sdk PyPI：<https://pypi.org/project/rerun-sdk/>
