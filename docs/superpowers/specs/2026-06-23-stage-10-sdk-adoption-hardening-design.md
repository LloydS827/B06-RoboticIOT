# Stage 10 SDK adoption hardening 设计

## 1. 背景

B06 当前已经从研究型 Rerun/Robotic IoT 项目，收束为 Python SDK first 的工业物理 AI 数据层工具包。Stage 9 已经完成三个关键动作：明确 `physical_ai_data` 是主产品 SDK、增加 `physical-ai-package` console entrypoint、提供 `run_weld_workcell_pipeline` 作为默认 H300-oriented synthetic demo 链路的一步式 helper。

当前主要风险已经不是“核心链路能不能跑通”，而是“研发、平台或工程团队能不能稳定采用”。README 和 `docs/sdk/README.md` 已说明入口关系，但 SDK API 细节、错误处理示例、可复制 examples、notebook/脚本式 walkthrough、默认 smoke 命令和 adoption checklist 仍不够完整。对新用户来说，项目仍可能看起来像一组阶段性脚本和研究文档，而不是一个可被接入的 Python 工具包。

Stage 10 应该把 Stage 9 的 SDK-first 入口变得更稳、更清晰、更容易被外部团队照着运行。它不应提前进入 production connector、DB schema、完整 Web 平台或真实 H300 现场协议；这些必须等真实或脱敏 H300 样本到位后，再按 Stage 8 `gap register` 逐项替换验证。

## 2. 假设与边界

本阶段基于以下假设推进：

- 真实或脱敏 H300 样本仍未到位，仓库默认路径继续使用 Stage 8 synthetic fixture。
- `Physical AI Package v0.1`、`weld_workcell` Clean Zone contract、training/evaluation draft v0.2 暂不变更。
- SDK first 是主产品方向，CLI 是薄封装，`scripts/` 是兼容入口和生成器。
- Rerun 仍是可替换 replay backend，不是主数据结构。
- 本阶段可以新增文档、examples、轻量 notebook-style Markdown、少量错误信息 polish 和 smoke tests。

本阶段不做：

- production connector、TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连、DB ingestion。
- 长期 DB schema、package schema changes、A02 schema 或自动 converter。
- 完整 Web 平台、Streamlit app、权限系统、数据集管理后台。
- importer registry、插件系统、profile DSL 或跨项目大一统配置层。
- 将 synthetic fixture 表述为真实 H300 协议或真实数据试点。

## 3. 目标

Stage 10 完成后，新用户应能做到：

1. 从 README 进入 SDK adoption 路径，理解先跑 synthetic demo，再替换 Clean Zone 样本的顺序。
2. 在 `docs/sdk/README.md` 中查到每个公共 SDK API 的输入、输出、返回类型、默认行为、常见错误和最小示例。
3. 直接运行仓库内 examples，完成 Stage 8 fixture 生成、pipeline helper、低层 importer contract、已存在 package 的 SDK 操作和 CLI JSON 输出检查。
4. 遇到缺文件、非法路径、错误 split、无效 package 时，看到足够定位问题的错误信息和文档说明。
5. 通过测试或 smoke 命令确认默认 SDK/CLI adoption path 没有退化。
6. 清楚知道 demo UI 仍只是后续可选评估项，不是 Stage 10 的交付主体。

## 4. 方案比较

### 方案 A：只补文档

只扩写 README 和 `docs/sdk/README.md`，不新增 examples、测试或错误信息 polish。

优点是改动小、风险低。缺点是 adoption 仍停留在“看懂”而不是“跑通”，错误信息和示例可复制性没有被自动保护。对 SDK 化来说不够稳。

结论：不采用。

### 方案 B：SDK adoption hardening 包

补 API 文档、examples、notebook-style walkthrough、错误信息 polish、CLI/SDK smoke tests、README/details 同步，并写一份轻量 demo UI 评估说明。代码只做服务于 adoption 的小改动。

优点是贴合 Stage 9 后的真实缺口，能让默认路径更可采用；同时保持边界克制，不引入平台化负担。缺点是不会提供强视觉展示，但当前阶段更需要稳定入口。

结论：采用。

### 方案 C：直接做轻量 demo UI

做一个 Streamlit 或 Web 页面包装 fixture 生成、pipeline、summary 和 artifact 路径。

优点是展示直观。缺点是会引入新依赖、新运行方式和维护面；在 SDK adoption 还没打磨好之前做 UI，容易把主线重新拉回 demo，而不是沉淀可复用数据层。

结论：暂不采用。本阶段只做评估文档，明确以后什么时候值得做。

## 5. 选定设计

Stage 10 采用方案 B：**SDK adoption hardening 包**。

本阶段交付物分成四层：

1. **文档层**：README 增加 Stage 10 adoption path；`docs/sdk/README.md` 扩展为 API reference + adoption guide；新增 `docs/sdk/adoption_checklist.md` 和 `docs/sdk/demo_ui_evaluation.md`。
2. **示例层**：新增 `examples/`，提供可直接运行的 SDK pipeline、low-level importer、existing package operations 和 CLI JSON smoke 示例；新增 notebook-style Markdown walkthrough，避免引入 Jupyter 依赖。
3. **代码层**：只做必要错误信息 polish，例如把 pipeline import failure、invalid package、training split、CLI JSON payload 的常见失败定位得更清楚。错误信息应帮助用户修正输入，不引入复杂异常类型层级。
4. **验证层**：新增或扩展 focused tests，覆盖 examples 可运行性、错误信息关键文本、CLI JSON 输出和 SDK adoption path。最终仍运行全量 `python -m pytest -q`。

## 6. 文档设计

### 6.1 README 更新

README 首页应新增或调整以下内容：

- 在“如何使用本项目”中加入 Stage 10 adoption path：
  1. 安装开发环境。
  2. 生成 Stage 8 synthetic fixture。
  3. 用 SDK pipeline 或 CLI 跑通默认链路。
  4. 查看 examples 和 SDK docs。
  5. 替换为真实/脱敏 H300 样本前，先按 gap register 检查字段。
- 明确 `examples/` 是采用入口，不是生产数据或真实 H300 样本。
- 在下一步计划中说明：真实/脱敏样本到位后，再进入 gap register replacement；demo UI 仍为可选评估。

### 6.2 SDK 文档更新

`docs/sdk/README.md` 应扩展为更完整的 SDK adoption guide：

- 公共 API 总览表：函数、输入、输出、适用输入状态、是否产生文件、副作用。
- `ValidationResult`、`PipelineResult`、`ImportRequest`、`ImportResult` 的字段说明。
- `run_weld_workcell_pipeline` 的默认行为、可选输出、返回路径、跳过 candidates/training/Rerun 的方式。
- 常见错误与处理：
  - Clean Zone 缺少 `job.json`、`frames.csv`、`process.csv` 或 `events.csv`。
  - `image_path` 越界或引用不存在。
  - validation failure。
  - invalid training split。
  - package path 传错或未生成。
- CLI 与 SDK 等价关系：说明 CLI 子命令如何映射到 SDK 函数。
- 当前非目标：connector、DB、Web、H300 protocol、schema changes。

### 6.3 Adoption checklist

新增 `docs/sdk/adoption_checklist.md`，面向准备接入的研发/平台/工程团队，列出：

- 本地环境准备。
- 输入数据准备：synthetic demo、Clean Zone、真实/脱敏样本的区别。
- 最小验收命令。
- 输出物检查：manifest、summary、candidates、training draft、`.rrd`。
- 脱敏和不可提交边界。
- 何时回到 Stage 8 gap register。

### 6.4 Demo UI evaluation

新增 `docs/sdk/demo_ui_evaluation.md`，只做评估，不实现 UI。内容包括：

- 可能的目标用户：评审、非工程干系人、A01/A02 协作评估。
- 可展示内容：summary、artifact paths、candidate samples、Rerun recording reference、gap register status。
- 不适合现在做的原因：真实样本未到位、SDK adoption 仍需先稳定、UI 会增加依赖和维护面。
- 触发条件：至少一条脱敏 H300 样本进入 Clean Zone；SDK examples 被稳定使用；有明确评审场景需要低门槛展示。

## 7. 示例设计

新增 `examples/`，保持无新依赖、可从仓库根目录直接运行。

建议文件：

- `examples/sdk_pipeline_stage8.py`：生成 Stage 8 synthetic fixture，调用 `run_weld_workcell_pipeline`，打印 summary 和关键输出路径。
- `examples/sdk_existing_package_ops.py`：生成一个 deterministic package，演示 `validate`、`summarize`、`export_candidates_csv`、`export_training_eval_draft`、`convert_to_rerun`。
- `examples/sdk_low_level_importer.py`：生成 Stage 8 fixture，演示 `ImportRequest`、`run_import` 和 `WeldWorkcellPackageImporter` 的低层 contract。
- `examples/cli_json_smoke.sh`：用标准 CLI 跑 pipeline 并检查 JSON 输出；脚本应可读、显式、失败即退出。
- `docs/sdk/stage8_pipeline_walkthrough.md`：notebook-style walkthrough，用 Markdown 和代码块组织，不要求 Jupyter。

示例默认输出到 `/tmp` 或可通过参数指定输出目录，避免把 artifact 放入仓库。示例文件不应偷偷联网、不应读取真实数据、不应依赖未安装的 optional LeRobot。

## 8. 错误信息 polish

错误信息只做必要增强：

- pipeline import failure 应保留现有前缀，并包含 source path、缺失文件或字段名。
- invalid package failure 应包含 validation code、message 和 path。
- CLI 顶层 `Error:` 应继续保持简洁，但底层错误文本要能直接定位到输入目录或字段。
- training split 错误应告诉用户允许值来自 draft contract。

不新增复杂 exception class，不做本地化错误系统，不引入 error code registry。

## 9. 测试与验证

本阶段测试策略：

- 为 examples 增加 focused smoke tests，确保 Python examples 可以通过 `subprocess` 从仓库根目录运行。
- 为 shell example 增加轻量测试，或至少在最终验证中手动运行。
- 补错误信息测试：缺少 `process.csv`、invalid training split、defensive validation failure。
- 保留已有 SDK import side-effect 测试，确保公共 SDK import 不加载 CLI/LeRobot/Rerun。
- 最终验证：
  - `python -m pytest tests/physical_ai_data/test_pipelines.py tests/physical_ai_data/test_cli.py tests/physical_ai_data/test_sdk.py -q`
  - `python -m pytest -q`
  - 至少运行一个 Python example 和 CLI JSON smoke。

## 10. 成功标准

Stage 10 完成时应满足：

- README 和 `details.md` 均记录 Stage 10 的定位、边界、产出物和下一步计划。
- `docs/sdk/README.md` 从入口说明升级为可采用的 SDK guide。
- `docs/sdk/adoption_checklist.md`、`docs/sdk/demo_ui_evaluation.md` 和 `docs/sdk/stage8_pipeline_walkthrough.md` 存在且不承诺真实数据能力。
- `examples/` 中的示例可运行，并默认写入 `/tmp` 或显式输出目录。
- 错误信息更适合排查 adoption 常见问题。
- focused tests 和全量测试通过。
- 没有新增 production connector、DB/schema、完整 Web 平台或 H300 现场协议。

## 11. 下一阶段衔接

Stage 10 之后建议进入 **Stage 11 H300 sample replacement readiness**，但前提是真实或脱敏 H300 样本至少到位一条。下一阶段应基于 Stage 8 `gap register`：

- 逐条关闭能直接落入现有 Clean Zone contract 的 gap。
- 对无法表达但影响 candidates、training draft、A02 evidence 或审计复盘的字段，拆成 importer 或 metadata 扩展任务。
- 仍避免在缺少真实样本时建设 production connector、DB schema 或完整 Web 平台。
