# Stage 7.1 工业物理 AI 数据层重排与 A01 H300 Profile 收敛设计

## 1. 背景

B06 已经完成 Physical AI Package、Raw/Clean Zone、Rerun adapter、LeRobot importer、Weld Workcell importer、training/evaluation draft export 和 Stage 7 simulated Raw/Clean fixture。现有路线可以支撑“可记录、可回放、可整理、可评测”的技术闭环，但项目首页仍保留较多阶段历史和 Rerun/Robotic IOT 口径，容易被误读为 Rerun 调研项目、普通设备联网项目或单一机器人数据项目。

母战略修订后，B06 需要明确成为公司工业物理 AI 的横向数据底座：服务 A01 智能焊接工站、A02 机器人技能大师、B08 设备时序样板和 S01 系统级事件闭环，使工业物理 AI 技术飞轮中的仿真、示教/采集、训练/评测、部署、生产回采、再训练/再优化形成证据链和数据资产。

当前第一优先级不是继续扩大平台范围，而是把 Stage 7 从通用 simulated fixture 收束为 A01 H300 最小焊接作业窗口数据试点，并说明其中哪些数据可以交给 A02 作为技能资产 evidence。

## 2. 目标

本轮 Stage 7.1 的目标是完成一次战略口径和 profile contract 的文档收敛，使新读者能快速回答：

1. B06 的第一定义是“工业物理 AI 数据层”，不是通用 IoT 平台、生产 connector 或 Rerun 项目。
2. B06 的主链路是 Raw Zone -> Clean Zone -> Physical AI Package -> Rerun replay -> candidate sample export -> training/evaluation draft；A01/A02/B08/S01 按各自 profile 消费 evidence、候选样本或结果引用。
3. 当前第一样板是 A01 H300 最小焊接作业窗口。
4. A01 需要向 B06 提供哪些最小真实/脱敏/仿真样本材料。
5. `WeldWorkcellPackageImporter` 如何与 H300 字段对齐，以及哪些缺口需要后续用真实样本确认。
6. B06 如何把 A01 作业窗口中的可用字段交给 A02 `ManipulationSkillAsset`，哪些字段只能作为上下文或附件。
7. B08 与 S01 拥有独立 profile 草案，不被强行塞进机器人作业数据结构。
8. 哪些是真实数据、脱敏数据、仿真数据、临时 artifact 和不可提交数据。

## 3. 非目标

本轮不做以下事项：

- 不实现生产 connector、TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连或 DB ingestion。
- 不设计长期 DB schema。
- 不修改 Physical AI Package v0.1 schema。
- 不把 A01/A02/B08/S01 四类 profile 一次性实现为代码级完整 schema。
- 不提交真实客户现场数据或未脱敏数据。
- 不改动 A02、B08、S01 仓库代码。
- 不把 Rerun 从可替换回放 backend 升级为主数据结构。
- 不将 Stage 7 的仿真 payload 定义为现场协议。

## 4. 方案选择

### 方案 A：只改 README 首页

优点是改动小、风险低。缺点是无法回答 A01 需要提供什么数据、A02 如何接收 evidence、B08/S01 如何保持独立 profile 等首次验收问题。这个方案过小，只能修辞，不能形成工程对接边界。

### 方案 B：一次性实现四类 profile schema 和 connector skeleton

优点是看起来平台化完整。缺点是当前缺少 A01 真实 H300 payload、B08/S01 现场接口和权限边界，过早实现容易固化错误字段、过度抽象，且违背“不做通用 IoT 平台”和“先用样本决定是否扩展 schema/connector”的路线。

### 方案 C：战略首页重排 + 四类 profile contract + A01 H300 Stage 7.1 收敛

优点是既修正项目定位，又保留 Stage 7 已有 simulated Raw/Clean fixture 的可运行价值；profile 先作为文档 contract 存在，A01 H300 做到字段请求、字段对齐和 A02 handoff 说明，B08/S01 保持独立草案，避免过度实现。缺点是本轮仍不产生新的真实数据接入能力，但这符合当前没有真机条件的现实。

选定方案 C。

## 5. 选定方案

Stage 7.1 定义为“工业物理 AI 数据层重排与 A01 H300 profile 收敛”。它是 Stage 7 的战略收束，不是 Stage 8。Stage 8 仍应留给真实/脱敏 A01 H300 样本替换、字段缺口评审和是否进入 connector/schema 的决策。

本轮文档结构：

- README：从项目入口层重排，第一段明确 B06 是工业物理 AI 的横向数据底座项目。
- `docs/profiles/`：新增四类 profile contract 和 B06 -> A02 evidence handoff。
- `docs/stage7/`：把 Stage 7 文档从通用仿真小窗口调整为 A01 H300 最小焊接作业窗口数据试点；保留 simulated fixture 作为当前可运行替代输入。
- `details.md`：记录 Stage 7.1 决策、完成事项和下一阶段计划。

具体新增 profile 文件：

- `docs/profiles/README.md`：profile 总览、阅读顺序、适用边界。
- `docs/profiles/a01_weld_workcell_job_window.md`：A01 H300 最小焊接作业窗口 profile。
- `docs/profiles/a02_manipulation_skill_asset_evidence.md`：A02 技能资产 evidence profile。
- `docs/profiles/b08_equipment_timeseries_observation_package.md`：B08 设备时序观测 profile。
- `docs/profiles/s01_manufacturing_event_context_package.md`：S01 制造事件上下文 profile。
- `docs/profiles/b06_to_a02_evidence_handoff.md`：B06 到 A02 `ManipulationSkillAsset` evidence handoff。

## 6. README 重排要求

README 首页应按以下顺序呈现：

1. 项目定位：工业物理 AI 数据层。
2. 主链路：

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

3. 当前第一样板：A01 H300 最小焊接作业窗口。
4. 当前可用能力：Physical AI Package、Stage 7 Raw/Clean fixture、Weld Workcell importer、Rerun adapter、training/evaluation draft。
5. 四类项目 profile：A01、A02、B08、S01。
6. 工程对接方式：离线目录、脱敏样本、字段说明、验收 checklist。
7. 当前边界：不做生产 connector，不做通用 IoT 平台。

README 可以保留历史阶段目录，但应把历史阶段降级为路线背景，避免首页主体继续显得像 Rerun 调研记录。

## 7. Profile Contract

### 7.1 A01 `weld_workcell_job_window`

覆盖 A01 H300 最小焊接作业窗口。第一阶段只要求文档 contract 和样本请求，不要求完整 schema 实现。

必须覆盖：

- 作业任务：`work_order_id`、`task_id`、`job_window_id`、阶段、时间窗口。
- 工件与焊缝：`part_id`、`seam_id`、焊缝几何或焊缝引用。
- 点云：原始/脱敏点云、PCL 输出、点云坐标系、采集时间。
- 相机位姿：相机内参/外参、相机到工站/机器人坐标系的关系。
- 机器人位姿：TCP、joint、base/tool/frame 假设、采样频率。
- 标定参数：相机标定、手眼标定、工件/工装坐标系、标定版本。
- 路径点：规划路径、执行路径、修正路径。
- 工艺参数：电流、电压、速度、送丝、保护气等可得字段。
- 人工修正：示教、拖动、路径修正、专家确认。
- 执行日志：状态、事件、异常、重试、报警。
- 模型输出：检测、定位、路径规划、质量预测等中间输出。
- 质量结果：外观、尺寸、缺陷、合格/不合格、复核结论。

### 7.2 A02 `manipulation_skill_asset_evidence`

覆盖技能资产 evidence，不要求 A02 直接消费完整 A01 作业包。B06 应说明哪些字段可进入 `ManipulationSkillAsset` evidence，哪些保留为上下文或附件。

可进入 A02 evidence 的字段应偏向：

- 经人工确认或可追溯的轨迹片段。
- TCP/姿态/路径点。
- 操作上下文、工件/焊缝语义。
- 质量标签和专家审查记录。
- 失败边界、异常原因、迁移评测线索。

只能作为上下文或附件的字段包括：

- 大体量原始点云、图像、日志、PCL 中间文件。
- 现场敏感工单、客户标识、未脱敏原始文件。
- 未经确认的模型中间输出。

### 7.3 B08 `equipment_timeseries_observation_package`

覆盖设备时序观测，不把它塞进机器人作业数据结构。B08 profile 应保留设备、传感器、阶段、cycle、窗口、质量标记、模型评测和候选信号。B06 只定义与 Physical AI 数据层的衔接边界，例如可复盘窗口、候选样本、质量结果引用。

### 7.4 S01 `manufacturing_event_context_package`

覆盖系统级制造事件上下文，不要求 S01 读取机器人轨迹细节。S01 profile 应保留制造对象、状态、事件、影响范围、任务、权限、执行结果和复盘摘要。B06 对 S01 的价值是给系统级事件提供可追溯数据包、候选证据和质量结果引用。

## 8. Stage 7.1 文档收敛

`docs/stage7/README.md` 应调整为 A01 H300 最小焊接作业窗口数据试点：

- 说明当前没有真机接入条件，所以仍从 simulated Raw/Clean fixture 开始。
- 明确 simulated fixture 是 A01 H300 字段对齐的替身，不是生产协议。
- 将最小窗口从通用焊接片段改为 H300 最小作业窗口。
- 增加 H300 字段对齐文档入口。
- 强化 Raw/Clean Zone 的真实/脱敏/仿真/临时 artifact 边界。

`docs/stage7/sample_request_checklist.md` 应明确 A01 第一批样本请求：

- 作业任务元数据：`work_order_id`、`task_id`、`job_window_id`、时间窗口、阶段。
- 工件和焊缝引用：`part_id`、`seam_id`、焊缝几何或焊缝文件引用。
- 点云。
- 相机位姿。
- 机器人位姿。
- 标定参数。
- 路径点：规划路径、执行路径、人工修正路径。
- PCL 输出。
- 模型输出。
- 人工修正。
- 工艺参数。
- 执行日志、状态、异常和报警。
- 质量结果。

`docs/stage7/h300_weld_workcell_field_alignment.md` 应说明：

- H300 字段与现有 `WeldWorkcellPackageImporter` clean contract 的对应关系。
- 当前可直接进入 `job.json`、`frames.csv`、`process.csv`、`events.csv`、`review_labels.csv` 的字段。
- 当前只能作为 source artifact 保留的字段。
- 需要真实样本确认后再决定是否扩展 importer 或 package schema 的字段。

## 9. 数据分级与提交边界

文档必须明确：

- 真实数据：来自现场或真机的原始数据，不应直接提交仓库。
- 脱敏数据：经过客户、工单、人员、路径、图像敏感信息处理的数据；仍需确认可提交边界。
- 仿真数据：仓库内默认可提交、可运行、可复现的样本。
- 临时 artifact：本地生成的 package、`.rrd`、candidates、training draft、Raw/Clean 输出，应放在 `artifacts/` 或 `/tmp`，默认不提交。
- 不可提交数据：客户现场原始文件、未脱敏图像/点云、账号密钥、内部网络地址、权限配置、商业敏感字段。

## 10. 验收标准

本轮完成后应满足：

- README 第一段和首页结构符合工业物理 AI 数据层定位。
- Stage 7 文档明确转向 A01 H300 最小作业窗口数据试点，同时保留仿真优先路径。
- A01 样本请求清单覆盖作业任务元数据、工件/焊缝引用、点云、相机位姿、机器人位姿、标定、路径点、PCL 输出、模型输出、人工修正、工艺参数、执行日志/异常/报警和质量结果。
- `WeldWorkcellPackageImporter` 有 H300 字段对齐文档。
- 有 B06 -> A02 evidence handoff 文档。
- 有 A01/A02/B08/S01 四类 profile 草案。
- B08/S01 不被塞进机器人 workcell 结构。
- README 和 details 均同步更新。
- README 当前默认开发验证命令仍通过：`python -m pytest -q`。

## 11. 风险与缓解

- 风险：文档太大，影响入口可读性。缓解：README 保持入口摘要，profile 细节下沉到 `docs/profiles/`。
- 风险：A01 H300 字段被写得像已确认现场接口。缓解：明确这是样本请求和字段对齐，不是生产协议。
- 风险：A02 evidence handoff 过度承诺。缓解：区分可进入 `ManipulationSkillAsset` 的 evidence、上下文和附件。
- 风险：B08/S01 被机器人语义污染。缓解：单独 profile，保持时序和事件上下文的独立结构。
- 风险：真实/脱敏数据边界不清。缓解：在 README、Stage 7 和 sample checklist 都重复提交边界。

## 12. 下一阶段

下一阶段建议定义为 Stage 8：A01 H300 真实/脱敏样本替换与缺口评审。Stage 8 的输入不是更多文档，而是一个最小真实或脱敏 H300 作业窗口样本，或者在无法取得真实样本时，先用更接近 H300 字段结构的仿真 fixture 做第二轮替代。Stage 8 应基于样本决定是否需要：

- 演进 `WeldWorkcellPackageImporter`。
- 增加 connector skeleton。
- 扩展 Physical AI Package schema。
- 设计临时 DB/schema。
- 继续只演进 importer/清洗流程。
