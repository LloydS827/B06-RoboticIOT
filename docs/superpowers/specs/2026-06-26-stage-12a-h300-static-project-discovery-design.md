# Stage 12A H300 Static Engineering Project Discovery Design

## 背景

Stage 11.1 已把 B06 收敛为 SDK-first 的 candidate real/de-identified onboarding 工具链：工程师可以先运行 `doctor`，再用 readiness 和 pipeline smoke 检查符合 `weld_workcell` Clean Zone contract 的候选样本。新的现场现实是：H300 真机的静态工程数据已经到位，但实时数据 API 仍需数周开发；同时，由于是第一次接触真实 H300 工程数据，字段要求、目录结构、脱敏边界和 Clean Zone 映射规则还不清楚。

本阶段应修正路线：不等待实时 API，也不提前建设 production connector。先把 H300 静态工程包作为第一类数据对象进行 discovery，明确它包含哪些工程资产、哪些能落入当前 B06 contract、哪些应保留为 Raw/source artifact、哪些会影响 A02 evidence handoff 或后续实时 API 要求。

## 当前样本观察

用户在本地受控目录 `data/H300/20260625_124428` 放入了一个 H300 工程包。该目录不应提交仓库，只用于本地结构分析和 smoke。已观察到的脱敏结构摘要如下：

- 工程主 JSON：`campcd_json/project_20260625_101838.json`，包含 `info`、`calibration`、`camera`、`photoPoses`、`pathPlan`、`extractPathPlan`、`processes`、`robot`、`runtime` 等对象。
- 相机/点云索引：`campcd_json/project_20260625_101838_campcd.json`，包含 3 组 `pcdWithCam` 图像、点云和相机位姿引用，以及 ROI。
- 图片：3 张 1440x1080 RGB JPEG。
- 点云：3 个 binary PCD 分片，字段为 `x y z`，合计约 135 万点；另有一个裸 xyz 文本点云文件。
- 焊缝 recipe：`weld_seam/recipe2_project_20260625_113936319.json`，包含 11 条 `weld_seams`。
- 规划数据：`pathPlan` 与 `extractPathPlan` 各 11 条。
- Lua/ABB RAPID 风格程序：包含 `MoveAbsJ`、`MoveL`、`ArcMPL`、`Stop`、`ROBTARGET`、`JOINTTARGET`、`SEAMDATA`、`WELDDATA`、`WEAVEDATA`、`MULTIPASSDATA` 等指令或数据定义；其中 `ArcMPL` 代表实际焊接动作。
- 焊接 flow config：包含 22 个 flow step。
- Web 原型：`http://124.71.158.78:18801/` 是 ClientEngine 控制面板，已有实时/离线模式、工程选择、下载工程、运行日志、Lua analysis 和 plan execution 页面。Lua analysis 已能展示执行序列；plan execution 对当前目录结构仍提示缺少 `project_file` 目录。

这些观察说明：H300 静态工程包不是单纯的作业窗口过程采样，而是可复用工程模板资产，连接视觉建模、点云、焊缝提取、路径规划、工艺配置和执行程序。

## 目标

Stage 12A 的目标是新增一个可复用的 H300 静态工程包 discovery 能力，让工程师和后续 pipeline 能快速回答：

1. 这个 H300 工程目录是否像一个可识别的静态工程包。
2. 它包含哪些工程资产、数量和基础结构。
3. 哪些字段或文件存在敏感信息风险，需要脱敏或只保留 onsite/local reference。
4. 哪些对象能映射到 Stage 8/11 的 gap register 与当前 `weld_workcell` Clean Zone contract。
5. 哪些对象应暂时作为 Raw/source artifact，不应过早结构化进 Physical AI Package schema。
6. 实时 API 到来时应补哪些动态信息，而不是重新定义全部数据要求。

## 非目标

Stage 12A 明确不做以下工作：

- 不提交 `data/H300` 原始工程数据、图片、点云、Lua、工程 JSON 或未脱敏内容。
- 不把报告格式转换做成 SDK 产品能力。
- 不自动把 H300 静态工程包转换成 `weld_workcell` Clean Zone。
- 不修改 Physical AI Package v0.1 schema。
- 不实现 realtime API、production connector、TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连、DB ingestion 或长期 DB schema。
- 不建设 demo UI；现有 Web 原型仅作为外部控制面板/分析原型参考。
- 不把本阶段的静态工程包结构声明为最终 H300 现场协议。
- 不把 LeRobot/open dataset 作为 H300 真实语义替代物；如使用，也仅作为 SDK robustness 的辅助验证。

## 推荐方案

采用“结构化 inspection + CLI JSON + 脱敏结构摘要”的方案。

SDK 只提供可复用的结构化 discovery 结果，不负责 Markdown 报告格式转换。CLI 负责把该结果输出为 JSON，文档层记录脱敏结构摘要和路线修正。

推荐公开入口：

```python
from physical_ai_data import inspect_h300_static_project

report = inspect_h300_static_project("path/to/h300/project")
payload = report.to_dict()
```

推荐 CLI：

```bash
physical-ai-package inspect-h300-static path/to/h300/project --json
```

第一阶段不提供 `--summary-md`。如果后续多次评审证明 Markdown 摘要生成是稳定产品需求，再单独设计。

## 数据模型

新增模块建议为 `src/physical_ai_data/h300_static_project.py`，负责只读扫描和结构摘要。该模块应保持无重依赖，不引入 Open3D、pcl、pandas 或浏览器依赖；只使用标准库、Pillow（项目已有依赖）和轻量文件头解析。

建议对象：

### `H300StaticProjectReport`

字段：

- `project_root: Path`
- `recognized: bool`
- `project_info: dict[str, object]`
- `files: list[H300StaticFile]`
- `images: list[H300ImageSummary]`
- `point_clouds: list[H300PointCloudSummary]`
- `text_point_clouds: list[H300TextPointCloudSummary]`
- `weld_seams: H300WeldSeamSummary`
- `path_plans: H300PathPlanSummary`
- `lua_program: H300LuaProgramSummary | None`
- `flow_config: H300FlowConfigSummary | None`
- `sensitivity_findings: list[H300SensitivityFinding]`
- `gap_mapping: list[H300GapMapping]`
- `summary: dict[str, object]`

每个对象提供 `to_dict()`，确保 CLI JSON 可直接序列化。

### 文件与媒体摘要

- 文件摘要记录相对路径、扩展名、大小、角色猜测，不记录原始内容。
- 图片摘要记录路径、宽高、模式，不复制图片。
- PCD 摘要只解析 header，记录 fields、width、height、points、data encoding，不读取 binary 点体。
- 裸 xyz 文本点云摘要只读取少量行判断列数和行数；不输出原始点。

### 工程语义摘要

- project JSON 记录 `projectName` 是否存在、`isTemplate`、`workpieceSeamType`、主要 top-level keys、`photoPoses` count、`pathPlan` count、`extractPathPlan` count。
- campcd JSON 记录 `pcdWithCam` count、ROI 是否启用、是否存在绝对/Windows 内部路径引用。
- weld seam recipe 记录 seam count、type/orientation/weld_type 分布、segments 和 measured widths 数量摘要。
- Lua 摘要记录关键指令计数、焊接动作计数、目标点定义计数，不输出原始代码。
- flow config 记录 step count 与基本类型，不输出原始流程内容。

## 敏感信息检查

Stage 12A 的检查应保守，宁可标记 review，也不要把真实字段误判为安全。第一阶段检查：

- Windows 绝对路径，如 `C:/...`。
- IP 地址、server/port、device id。
- operator/author/reviewer/person-like 字段。
- 工程名和时间戳作为潜在业务追溯信息。
- 图片、点云、Lua、工程 JSON 这类不可默认提交的 source artifact。

检查结果只输出 finding 类型、相对路径、字段名或风险类型，不输出敏感值本身。

## Gap Mapping

报告应按 Stage 8 gap register 输出初步映射：

- G-001：工程主键、project name、task/project timestamp，当前只能作为追溯线索，不能等同工单主键。
- G-003：PCD 点云、裸 xyz 点云、PCL/焊缝候选相关文件已存在，需评审坐标系、标定版本和是否只做 source artifact。
- G-004：图像、相机参数、手眼/标定相关字段已存在，需评审脱敏边界和提交规则。
- G-005：若工程 JSON 或 recipe 中包含模型/算法输出线索，先作为 source artifact。
- G-006：人工拖拽示教、微调或 review 信息如存在，先标记为 review，不结构化为 labels。
- G-007：焊接工艺配置和 Lua 中 `WELDDATA`、`WEAVEDATA`、`MULTIPASSDATA` 能提供静态工艺模板，但不代表实时工艺采样。
- G-008：Lua 指令序列和 flow steps 可作为执行计划事件线索，但不等同实时事件日志。
- G-010：ClientEngine 离线下载和本地 TF 卡/目录信息提示部署存储边界，需要后续权限和保留策略。
- G-012：坐标系、TCP、相机位姿、工件 frame 和单位约定是本阶段重点，需要形成后续 Clean Zone draft 决策输入。

## SDK 与 CLI 边界

SDK 的职责是返回结构化对象，保证可测试、可复用、可由其他工具消费。

CLI 的职责是：

- `inspect-h300-static PROJECT_ROOT --json`
- human text 模式可输出简短摘要，但不做复杂 Markdown 报告生成。
- JSON exit code：正常识别返回 0；目录不存在或不可读返回非 0；识别到敏感风险不应导致非 0，因为这是 review finding，不是运行错误。

## 文档更新

本阶段必须更新：

- `README.md`：当前路线从“等待首条脱敏 H300 作业窗口样本”修正为“静态工程包已到位，先做 Stage 12A discovery；实时 API 后续接入”。
- `details.md`：记录 Stage 12A 背景、真实约束、设计决策、验证结果和下一步。
- 新增 `docs/stage12a/README.md`：说明静态工程包 discovery 的目的、边界、运行方式、输出解释和后续 Stage 12B/13。
- 新增 `docs/stage12a/h300_static_project_structure_summary.md`：提交脱敏结构摘要，只包含结构、数量、字段类别、风险类型和 gap mapping，不包含原始样本内容。

同时建议在 `.gitignore` 加入 `data/`，防止误提交本地真实/脱敏工程数据。

## 测试策略

真实 `data/H300` 不进入 CI，也不作为提交 fixture。

新增极小 synthetic H300 static project fixture，用于测试 inspector：

- 最小 project JSON，包含 `info`、`photoPoses`、`pathPlan`、`extractPathPlan`。
- 最小 campcd JSON，包含 1 条 `pcdWithCam` 和 Windows 路径样例。
- 最小 weld seam recipe，包含 1-2 条 seam。
- 最小 Lua 文件，包含 `MoveAbsJ`、`MoveL`、`ArcMPL`、`Stop`、`ROBTARGET`。
- 最小 flow config JSON。
- 1 张测试图片。
- 1 个 ASCII 或 header-only PCD fixture。
- 1 个小型 xyz 文本点云。

测试覆盖：

- SDK import 不加载 CLI、LeRobot 或 Rerun 重依赖。
- `inspect_h300_static_project(...)` 能识别 synthetic fixture。
- PCD header、图片尺寸、Lua 指令、weld seam、path plan、flow count 摘要正确。
- 敏感 finding 不泄露原始敏感值。
- CLI `--json` 输出可解析。
- 缺失目录或不可读输入返回明确错误。
- `.gitignore` 包含 `data/`。

## 执行顺序

1. 路线保护：更新 `.gitignore`、README 和 details 的 Stage 12A 路线表述。
2. 文档先行：新增 `docs/stage12a/README.md` 和脱敏结构摘要。
3. TDD：新增 synthetic fixture helper 和 inspector 测试。
4. 实现 `h300_static_project.py` 与顶层 SDK export。
5. 实现 CLI `inspect-h300-static --json`。
6. 补充 SDK docs/examples 索引。
7. 本地使用真实 `data/H300/20260625_124428` 做 manual smoke，只记录脱敏结果，不提交原始数据。

## 后续阶段

Stage 12B 建议做 H300 static project to Clean Zone draft readiness：基于 Stage 12A 的 mapping 和真实静态工程包，决定是否新增 `prepare_h300_clean_zone_draft(...)` 或只生成 mapping checklist。

Stage 13 建议做 realtime API readiness：等实时 API 样例可用后，基于 Stage 12A/12B 已澄清的静态字段和坐标系，补充时间戳、实时状态、事件、报警、过程参数和采样频率要求。

Stage 14 之后才评估 production connector、DB/schema 或评审 UI，前提是多工程样本和实时 API 共同证明这些能力是产品必需。
