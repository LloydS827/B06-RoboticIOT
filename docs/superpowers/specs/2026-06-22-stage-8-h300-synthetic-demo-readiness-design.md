# Stage 8 A01 H300 仿真能力展示与真实接入准备设计

## 1. 背景

B06 当前定位已经从 Rerun/Robotic IOT 调研收束为工业物理 AI 数据层。Stage 7.1 已明确当前第一样板是 A01 H300 最小焊接作业窗口，并保留 simulated Raw/Clean fixture 作为无真机条件下的默认可运行路径。

当前关键事实是：仓库仍没有真实或脱敏 H300 样本。若直接把下一阶段命名为“真实数据试点”，容易暗示已经具备真机数据、现场协议或生产接入条件；若只继续写战略文档，又无法展示 B06 现有 Raw/Clean、importer、Package、Rerun、candidate、training draft 和 A02 evidence handoff 的实际闭环。

因此 Stage 8 应定义为 **A01 H300 仿真能力展示与真实接入准备**。它用更贴近 H300 的 synthetic 作业窗口把当前能力讲清楚，同时把真实数据到来后需要替换、确认或扩展的问题整理成可执行清单。

## 2. 假设

- 当前仍没有可提交的真实 H300 原始数据或脱敏样本。
- Stage 7.1 `generate_stage7_sim_window.py` 和 `WeldWorkcellPackageImporter` 是本轮最稳妥的默认工程路径。
- Stage 8 不改变 Physical AI Package v0.1 schema，不新增生产 connector，不设计长期 DB schema。
- Stage 8 的演示材料必须明确标注 synthetic 字段，避免被误读为现场协议或真实采集数据。
- 本轮交付应能服务两类读者：对外看能力展示的项目相关方，以及后续接真实样本的工程/机器人团队。

## 3. 目标

Stage 8 完成后，新读者应能快速回答：

1. B06 当前从 Raw Zone 到 A02 evidence handoff 的能力链路是什么。
2. A01 H300 最小作业窗口里有哪些任务、工件/焊缝、机器人位姿、图像/点云引用、PCL 输出、模型输出、人工修正、工艺参数、异常和质量结果。
3. 哪些字段当前由 synthetic fixture 提供，哪些字段等待真实/脱敏样本替换。
4. 哪些字段现有 importer 已结构化支持，哪些只能作为 source artifact 或展示引用保留。
5. 真实 H300 数据到来后，第一轮评审应检查哪些 gap，以及哪些 gap 才可能触发 importer、connector、DB/schema 或 package schema 扩展。
6. A01 作业窗口中哪些 evidence 可以给 A02 `ManipulationSkillAsset`，哪些只能作为上下文、附件或 blocked 项。

## 4. 非目标

本轮不做以下事项：

- 不声称已有真实 H300 数据。
- 不实现生产 connector、TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连或 DB ingestion。
- 不设计或修改长期 DB schema。
- 不修改 Physical AI Package v0.1 schema。
- 不把 synthetic Raw payload 定义为 H300 现场协议。
- 不做复杂 Web 产品、前端平台或长期 viewer。
- 不自动把完整 A01 package 转成 A02 技能资产。
- 不提交真实客户现场数据、未脱敏图像/点云、密钥、内网地址或商业敏感字段。

## 5. 方案比较

### 方案 A：直接进入真实数据试点

优点是名称更接近最终目标。缺点是当前没有真实数据，容易造成错误承诺；同时会把讨论过早推向 connector、DB、权限和部署，而这些问题需要真实样本证明必要性后再定。

结论：不采用。

### 方案 B：只继续写路线和 gap 文档

优点是风险低、不会误称真机能力。缺点是不能展示 B06 现有工程链路，也无法让 A01/A02 相关方看到 Raw/Clean -> Package -> replay -> candidates -> evidence handoff 的具体样貌。

结论：过小，不采用。

### 方案 C：仿真驱动的可视化样板 + 真实接入准备包

优点是忠于当前无真实数据的现实，又能把已有能力以 H300-oriented 作业窗口讲清楚；gap register 能把后续真实接入要补的样本、字段、权限和工程扩展决策列成清单。缺点是本轮仍不是生产接入，但这是当前最符合项目阶段的取舍。

结论：采用。

## 6. 选定设计

Stage 8 采用方案 C，交付四类材料和一组可运行 fixture：

- **Stage 8 H300 synthetic demo fixture**：在 Stage 7.1 fixture 基础上增强 H300 叙事字段和 source artifacts。
- **Stage 8 capability visualization report**：用轻量 Markdown 图表和表格展示 Raw Zone -> Clean Zone -> Package -> Rerun replay -> candidates -> A02 evidence handoff。
- **H300 synthetic-to-real gap register**：列出缺什么真实样本、哪些字段只能仿真、哪些字段 importer 已支持、哪些字段只能 source artifact、哪些字段可能需要未来扩展。
- **B06 -> A02 evidence demo example**：给出 synthetic 作业窗口如何形成 A02 evidence handoff 示例。
- **README/details 路线更新**：把 Stage 8 定位为当前下一阶段，并把 “真实/脱敏样本替换” 顺延为 Stage 9 或 Stage 8 之后的真实接入评审。

## 7. Fixture 设计

Stage 8 不新建第二套 importer contract，也不改变 Stage 7.1 默认 fixture 输出。实现上应新增独立入口 `scripts/generate_stage8_h300_synthetic_demo.py` 和独立模块/函数，内部可以复用 Stage 7.1 生成逻辑与常量，但使用独立 generated marker 和 allowlist，避免破坏 Stage 7.1 的可重复生成、测试和历史基线。

默认输出根建议为：

```text
artifacts/stage8/h300_synthetic_demo/
```

生成后的目录结构为：

```text
raw/
  manifest.raw.json
  sdk/robot_state.ndjson
  tcp_json/hmi_task_messages.ndjson
  files/
    robot_program.lua
    robot_trajectory.json
    seam_trajectory.json
    h300_job_window_story.json
    pcl_seam_candidates.json
    model_outputs.json
    manual_corrections.json
    quality_result.json
    images/front_0000.png
    point_clouds/window_0000.pcd
  process/welding_process.csv
  events/event_log.ndjson

clean/weld_workcell/
  job.json
  frames.csv
  process.csv
  events.csv
  review_labels.csv
  images/front_0000.png
```

其中 Clean Zone 仍只承诺现有 `WeldWorkcellPackageImporter` 结构化读取的字段。新增 H300 source artifacts 的职责是展示和缺口评审，不代表 importer 已支持完整 H300 字段。

新增 raw artifacts 的建议内容：

- `h300_job_window_story.json`：把作业任务、工件/焊缝、窗口阶段、设备、synthetic 标记和真实替换字段集中成一个可读索引。
- `pcl_seam_candidates.json`：模拟 PCL 焊缝候选、点云特征、坐标系和置信度。
- `model_outputs.json`：模拟 seam localization、path planning 或 quality prediction 的模型输出。
- `manual_corrections.json`：模拟人工修正路径点、审查人、修正原因和是否可作为 A02 evidence。
- `quality_result.json`：模拟质量结论、缺陷摘要、检测来源和复核状态。
- `point_clouds/window_0000.pcd`：小体量 synthetic 点云占位文件，用于展示引用链路。

`manifest.raw.json` 应增加字段分级或 source map，至少说明：

- `data_origin: synthetic`
- `real_replacement_required: true`
- `synthetic_fields`
- `real_sample_required_fields`
- `importer_supported_fields`
- `source_artifact_only_fields`

## 8. 可视化报告设计

Stage 8 不做复杂 Web 产品。能力展示采用 Markdown 文档，必要时使用 Mermaid 和表格，让仓库默认可读、可 diff、可审查。

建议新增：

- `docs/stage8/README.md`：Stage 8 总览、运行命令、交付物索引和边界。
- `docs/stage8/capability_visualization_report.md`：能力展示报告。
- `docs/stage8/h300_synthetic_to_real_gap_register.md`：gap register。
- `docs/stage8/a02_evidence_demo_example.md`：A02 evidence 示例。

展示报告至少包含：

- 数据链路图：Raw Zone -> Clean Zone -> Physical AI Package -> Rerun replay -> candidates -> A02 evidence handoff。
- H300 作业窗口时间线：approach、weld、cooldown、异常/风险标记、人工修正、质量结果。
- 字段落点表：Raw artifact、Clean contract、Package output、A02 handoff 的关系。
- Raw/Clean/Package 文件树：区分已生成、可提交 synthetic、临时 artifact 和不可提交真实数据。
- 状态板：当前已能做、真实数据后才能做、明确不做。

## 9. Gap Register 设计

Gap register 应从“后续可执行”出发，而不是泛泛列风险。每条 gap 至少包含：

- gap id
- 字段或样本组
- 当前 Stage 8 状态：synthetic / importer_supported / source_artifact_only / missing_real_sample / future_decision
- 当前落点
- 需要的真实/脱敏样本或说明
- 触发后续扩展的条件
- 默认下一步

第一版 gap register 应覆盖：

- 真实 `job_window_id`、`task_id` 和工单主键。
- 真实机器人 TCP/joint/state 采样频率与时间戳来源。
- 点云文件、PCL 输出、坐标系和标定版本。
- 相机内外参、手眼标定和图像脱敏边界。
- 模型输出版本、置信度、路径建议和质量预测。
- 人工修正来源、审查工具、reviewer 和状态。
- 工艺参数单位、频率、缺失值和设备来源。
- 异常/报警/执行日志字段。
- 质量结果来源、检测口径、复核结论和是否可进入 A02 evidence。
- AI 控制器上的 Raw/Clean/Package/rrd/candidates/draft 存储位置和权限。

## 10. A02 Evidence 示例设计

`docs/stage8/a02_evidence_demo_example.md` 不定义 A02 schema，只给出 B06 能交付的 A02 evidence handoff 示例。示例应清楚区分：

- `evidence`：人工确认轨迹、TCP/路径点、质量标签、失败边界、专家审查。
- `context`：工件/焊缝语义、工艺参数、模型输出摘要、坐标系假设。
- `attachment_reference`：图像、点云、PCL、source artifact 和 Rerun `.rrd` 引用。
- `blocked`：未脱敏真实客户、工单、人员、设备身份、内网路径和敏感画面。

示例内容必须标注 `synthetic_demo_only: true`，并说明真实数据到来后需要替换 source refs 和审查来源。

## 11. README 与 details 更新

README 应更新：

- 当前第一样板从 Stage 7.1 过渡为 Stage 8 synthetic demo readiness。
- 快速开始增加 Stage 8 fixture 生成命令。
- 文档目录增加 `docs/stage8/`、Stage 8 spec 和 plan。
- 总体路线增加 Stage 8，并说明下一步真实/脱敏样本替换不应在无样本时命名为真实试点。

`details.md` 应更新：

- 记录 Stage 8 的关键决策、交付物、验证命令和下一阶段规划。
- 下一步计划应指向真实/脱敏 H300 样本替换与 gap register 逐条关闭。

`docs/stage7/README.md` 应同步增加 Stage 8 过渡说明或更新“下一步”小节：

- Stage 7.1 保持为 A01 H300 最小作业窗口的历史基线和默认 Clean Zone contract 说明。
- Stage 8 是在仍无真实样本条件下的第二轮 H300-oriented synthetic 替代展示。
- 真实/脱敏样本替换与 gap register 关闭顺延到 Stage 9 或 Stage 8 之后的真实接入评审。

## 12. 验收标准

本轮完成后应满足：

- Stage 8 fixture 生成命令可运行，并生成 Raw/Clean 目录。
- 新增 H300 source artifacts 存在，且明确标记 synthetic。
- Clean Zone 仍可通过 `WeldWorkcellPackageImporter` 进入 Physical AI Package。
- 生成的 package 可继续 validate、summarize、export-candidates、export-training-draft 和 convert-rerun。
- README 或 Stage 8 文档给出明确的 Clean Zone -> Package -> validate/summarize/candidates/training draft/Rerun convert 命令或最小 Python/SDK 示例，不能只验证 fixture 生成。
- `docs/stage8/` 包含能力展示报告、gap register 和 A02 evidence 示例。
- README 和 details 均同步更新。
- 关键词扫描能命中 Stage 8、synthetic、gap register、A02 evidence handoff 等关键口径。
- 误承诺扫描不能出现“真实样本/现场协议/生产接入/DB ingestion/正式 DB schema/package schema/A02 schema 或 A02 自动转换已完成”等误导性表述；扫描词表应避免在验收文字中自引用。
- `python -m pytest -q` 通过。

## 13. 风险与缓解

- 风险：新增 fixture 被误认为真实数据。缓解：文件名、manifest 和文档中统一标注 synthetic、demo、not production protocol。
- 风险：source artifacts 增加后被误读为 importer 已支持。缓解：gap register 和字段落点表明确区分 importer_supported 与 source_artifact_only。
- 风险：文档展示过重，像产品平台。缓解：只做 Markdown/Mermaid，不做 Web app。
- 风险：fixture 变复杂后破坏 Stage 7 默认链路。缓解：复用现有 Clean Zone contract，并用测试覆盖新增 artifact 及 importer chain。
- 风险：真实接入问题继续停留在口号。缓解：gap register 每条都写清需要的真实样本、触发条件和默认下一步。

## 14. 下一阶段建议

Stage 8 完成后，下一阶段建议定义为 **Stage 9：A01 H300 真实/脱敏样本替换与 gap register 关闭**。Stage 9 的前提是至少拿到一个真实或脱敏 H300 最小作业窗口样本；若仍没有真实样本，则不应进入 connector 或 DB/schema 实现，而应继续围绕 Stage 8 gap register 推动样本、权限、脱敏和字段说明到位。
