# Stage 4.2 SDK Wrapper / External Importer 边界设计

## 1. 背景

Stage 3 已经形成 Physical AI Package v0.1 的最小数据包结构、validator、candidate export、Rerun adapter 和 CLI。Stage 4 已经把 LeRobot 开放机器人数据导入 Physical AI Package，并在 Stage 4.1 补齐真实 PushT quick、ALOHA representative、PushT full acceptance 的命令证据。当前链路证明了“数据能导入、包能校验、候选能导出、Rerun 能验证”。

但现有使用方式仍偏 CLI 和样板脚本：外部数据源如果想接入，容易直接调用内部函数或复制 LeRobot adapter 的结构。下一阶段需要先固化边界，而不是继续添加更多数据集特例。

Stage 4.2 的定位是把 Physical AI Package 从“可运行原型”推进到“可被外部调用和扩展的最小接口层”。

## 2. 阶段目标

Stage 4.2 要回答四个问题：

1. Python 调用方应该从哪里进入 Physical AI Package 的最小 SDK？
2. CLI、SDK、external importer 三者分别负责什么，哪些能力不应该互相侵入？
3. LeRobot importer 如何从样板验证沉淀成可复用 importer contract？
4. Stage 4.3 训练/评估导出需要的最小导出草案是什么？

本阶段不追求完整插件系统，也不进入真实模型训练。目标是建立小而稳定的边界，让后续真机 importer、业务系统 importer、训练导出和 Viewer 验收都有清楚的承接点。

## 3. 现状判断

当前代码中已经存在以下能力：

- `physical_ai_data.validation.validate_package`：校验包。
- `physical_ai_data.candidates.summarize_package`：汇总包。
- `physical_ai_data.candidates.export_candidates`：导出候选 CSV。
- `physical_ai_data.rerun_adapter.write_rrd`：转换为 Rerun `.rrd`。
- `physical_ai_data.lerobot_loader.load_lerobot_episode`：真实 LeRobot 数据加载。
- `physical_ai_data.lerobot_adapter.import_lerobot_episode`：将 normalized episode 写入 Physical AI Package。
- `physical_ai_data.cli`：把上述能力暴露为命令行。

主要缺口是边界命名不够明确：

- Python SDK 调用方需要知道内部模块名。
- CLI 直接编排 loader 与 adapter，没有一个可测试的 importer command contract。
- LeRobot adapter 已经具备 importer 形态，但没有显式 `source -> package` contract。
- 训练/评估导出还停留在 candidate CSV，没有 manifest 草案说明输出可被谁消费。

## 4. 设计原则

- **薄封装优先**：SDK wrapper 只组合现有稳定能力，不复制业务逻辑。
- **CLI 是外壳**：CLI 负责参数解析、错误展示和退出码；核心行为放在 SDK 或 importer contract 中。
- **Importer 是边界**：external importer 的输入可以是第三方数据源，但输出必须是 Physical AI Package 目录。
- **LeRobot 是首个实现，不是特殊规则中心**：LeRobot importer 使用同一 importer contract，不为未来 importer 设计复杂注册系统。
- **训练/评估导出先做草案**：输出最小 manifest 和 CSV 索引，记录 package、candidate、split、label/status 占位，不承诺训练框架格式。
- **默认路径保持可用**：默认 `.[dev]` 测试不依赖 LeRobot、网络、真实数据缓存或 GUI。

## 5. 方案比较

### 方案 A：薄 SDK + 显式 importer contract

新增 `physical_ai_data.sdk` 作为 Python 调用入口，新增 `physical_ai_data.importers` 定义 importer request/result 和通用执行函数。LeRobot importer 通过 contract 暴露。CLI 调用 SDK/importer contract，而不是直接拼内部函数。训练/评估导出新增最小草案模块。

优点：改动小，贴合当前代码结构，能立即明确边界。缺点：不是完整插件系统，后续多 importer 时还需要扩展注册方式。

### 方案 B：完整插件/注册系统

设计 importer registry、entry points、动态加载、统一配置和扩展 discovery。

优点：长期扩展性更强。缺点：当前只有 LeRobot 一个真实 importer，容易过度设计，也会增加测试和安装复杂度。

### 方案 C：只补文档，不改代码

用文档定义 CLI/SDK/importer 边界，暂不落地 SDK module 和 contract。

优点：最快，风险低。缺点：边界不能被测试约束，下一阶段仍可能继续复制内部调用。

## 6. 选定方案

本阶段采用 **方案 A：薄 SDK + 显式 importer contract**。

原因：

- 当前项目正处在“外围封装”阶段，需要可调用边界，但还不需要插件生态。
- LeRobot 已经是足够真实的 importer 样板，适合抽出最小 contract。
- 训练/评估导出只是 Stage 4.3 的铺垫，先形成 draft artifact 更符合 YAGNI。
- 该方案可以用单元测试约束，不依赖真实 LeRobot、网络或 GUI。

## 7. SDK 边界

新增 `src/physical_ai_data/sdk.py`，提供最小 Python SDK 入口：

- `validate(package_root) -> ValidationResult`
- `summarize(package_root) -> dict[str, object]`
- `export_candidates_csv(package_root, output_csv=None, min_score=0.5) -> Path`
- `convert_to_rerun(package_root, output_rrd) -> Path`
- `export_training_eval_draft(package_root, output_dir=None, split="unspecified") -> Path`

SDK 不重新定义 schema，不吞掉 validator 错误，不访问 CLI `argparse.Namespace`，也不导入 LeRobot 可选依赖。

`physical_ai_data.__init__` 应导出这些稳定入口，方便调用方使用：

```python
from physical_ai_data import validate, summarize, export_candidates_csv
```

## 8. CLI 边界

CLI 继续保留当前子命令：

- `generate`
- `validate`
- `summarize`
- `export-candidates`
- `convert-rerun`
- `import-lerobot`

新增一个最小命令：

- `export-training-draft`

CLI 只负责：

- 参数解析；
- 调用 SDK 或 importer contract；
- 打印人类可读或 JSON 输出；
- 返回退出码。

CLI 不直接读写训练导出 CSV 的内部结构，也不直接实例化第三方 importer 的内部实现细节。

## 9. External Importer Contract

新增 `src/physical_ai_data/importers.py`，定义最小 importer contract：

- `ImportRequest`
  - `source_format: str`
  - `source: Mapping[str, object]`
  - `output_dir: Path`
  - `options: Mapping[str, object]`
- `ImportResult`
  - `package_root: Path`
  - `source_format: str`
  - `source_id: str`
  - `frame_count: int`
  - `warnings: list[str]`
- `PackageImporter` protocol
  - `source_format: str`
  - `import_package(request: ImportRequest) -> ImportResult`
- `run_import(importer, request) -> ImportResult`

contract 只规定“外部源生成 Physical AI Package”的最小形态，不规定插件发现、并发、远程下载、鉴权和缓存策略。

## 10. LeRobot Importer Contract 落地

新增 `LeRobotPackageImporter`，作为首个 contract 实现。它内部继续复用：

- `load_lerobot_episode`
- `import_lerobot_episode`
- `validate_package`

CLI 的 `import-lerobot` 改为构造 `ImportRequest` 并调用 `LeRobotPackageImporter`。这能让同一条导入行为既能被 CLI 调用，也能被 Python SDK 或未来 orchestrator 调用。

LeRobot importer 的 contract 输入最小字段：

- `repo_id`
- `episode_index`
- `root`
- `profile`
- `max_frames`
- `camera`

本阶段不增加 LeRobot 专用 CLI 参数，避免把 Stage 4.2 变成 LeRobot 功能扩展阶段。

## 11. 训练/评估导出草案

新增 `src/physical_ai_data/training_export.py`，输出最小 draft artifact：

```text
PACKAGE/derived/training_eval/
  training_eval_manifest.json
  samples.csv
```

`training_eval_manifest.json` 记录：

- `export_format`: `physical-ai-training-eval-draft/v0.1`
- `source_package_id`
- `source_package_root`
- `schema_version`
- `scenario_type`
- `split`
- `samples_csv`
- `candidate_count`
- `created_at`

`samples.csv` 最小列：

- `sample_id`
- `split`
- `frame_id`
- `timestamp_s`
- `candidate_id`
- `source_type`
- `score`
- `label_status`
- `package_root`

导出逻辑：

- 先 validate package；
- 如果 candidates 不存在，则调用现有 candidate export 生成；
- 把 candidate row 转成 sample row；
- `label_status` 固定为 `unlabeled`，不编造成功/失败或训练标签；
- `split` 默认 `unspecified`，调用方可传入 `train`、`eval`、`holdout` 等字符串，但本阶段不做自动切分。

## 12. 文档更新

本阶段需要更新：

- `README.md`
  - 补充 Stage 4.2 文档入口和当前状态摘要。
- `details.md`
  - 记录 Stage 4.2 完成事项、关键决策和下一步计划。
- `docs/stage4/README.md`
  - 增加 SDK/importer/training draft 使用入口。
- `docs/research/06-lerobot开放数据样板链路记录.md`
  - 补充 LeRobot importer 已沉淀为 contract 的记录。
- 新增或更新专题文档：
  - `docs/superpowers/specs/2026-06-10-sdk-wrapper-importer-boundary-design.md`
  - `docs/superpowers/plans/2026-06-10-sdk-wrapper-importer-boundary.md`

## 13. 测试策略

新增测试应覆盖：

- SDK wrapper 调用现有 validator/summarizer/candidate/Rerun/export draft。
- CLI `export-training-draft` 输出 manifest 和 samples。
- importer contract 能执行 fake importer 并返回 `ImportResult`。
- `LeRobotPackageImporter` 使用 monkeypatch 的 fake loader，不安装真实 LeRobot、不访问网络。
- `import-lerobot` CLI 仍列出原有选项并可通过 fake loader 写包。
- 默认全量测试通过。

真实 LeRobot smoke 不作为 Stage 4.2 必跑项；Stage 4.1 已经提供真实数据证据。Stage 4.2 的验证重点是边界可测试、默认环境可运行。

## 14. 非目标

Stage 4.2 不做：

- 不新增完整 plugin registry 或 entry points。
- 不引入数据库、Catalog 服务或远端数据管理。
- 不改变 Physical AI Package v0.1 schema。
- 不实现真实训练框架导出，例如 Hugging Face dataset、PyTorch dataloader、LeRobot replay buffer。
- 不实现自动 train/eval split 策略。
- 不增加新的真实 LeRobot dataset 验收。
- 不解决 native GUI Viewer/Blueprint 环境问题；该项仍等待 GUI 环境可用时补做。

## 15. 风险与处理

| 风险 | 处理 |
| --- | --- |
| SDK wrapper 变成重复逻辑 | 只代理现有函数，测试以行为为准。 |
| importer contract 过早复杂化 | 不做 registry、entry point、动态发现和插件生命周期。 |
| LeRobot importer 与 CLI 行为不一致 | CLI 改走同一个 `LeRobotPackageImporter`。 |
| training draft 被误认为正式训练格式 | 命名包含 `draft`，manifest version 明确为 draft。 |
| 默认测试误依赖 LeRobot | LeRobot importer 测试使用 monkeypatch fake loader。 |
| 文档与代码边界漂移 | README/details/stage4 运行说明同步更新。 |

## 16. 完成定义

Stage 4.2 完成时应具备：

- 有最小 SDK 入口，可从 Python 直接调用 validate/summarize/export/convert/training draft。
- CLI、SDK、external importer 的职责边界在文档和代码中一致。
- LeRobot import 已通过 `LeRobotPackageImporter` contract 暴露，CLI 复用该 contract。
- 有最小训练/评估导出草案，能从候选 CSV 生成 manifest 和 samples。
- 默认测试通过，不依赖 LeRobot、网络、真实缓存或 GUI。
- README、details 和 Stage 4 文档已更新。
- Viewer/Blueprint 人工视觉验收仍作为下一阶段或 GUI 环境可用后的补充项记录。
