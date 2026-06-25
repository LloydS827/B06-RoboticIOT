# 项目执行细节

本文档用于记录项目推进过程中的执行细节、当前完成事项、下一步计划和阶段性决策。README 保持项目级概览，本文档记录更细的过程信息和工作台账。

## 文档分工

- `README.md`：项目定位、核心能力、启动路线、重要入口和面向外部阅读的高层信息。
- `details.md`：执行日志、当前进展、下一步任务、阶段性判断和项目推进过程中的细节信息。
- `docs/`：启动说明、立项背景、调研报告、技术评测、规范草案和其他专题文档。
- `AGENTS.md`：面向 AI 协作和代码代理的项目工作规范。

## 当前完成事项

### 2026-06-06

- 初始化 git 仓库，主分支为 `main`。
- 生成项目根目录 `README.md`，沉淀项目定位、核心能力方向、启动路线和近期输出物。
- 新增 `.gitignore`，排除系统文件、编辑器文件、缓存、构建产物和本地环境变量文件。
- 建立 `docs/` 目录，并将两份关键启动文档纳入其中：
  - `docs/260606_PhysicalAI数据层项目启动说明.md`
  - `docs/03-B06_RoboticIOT与物理数据层课题.md`
- 完成初始提交并推送到远端仓库：`git@github.com:LloydS827/B06-RoboticIOT.git`。
- 新增 `AGENTS.md`，作为项目中 AI 协作和代码代理的工作规范。
- 新增本文档 `details.md`，用于记录项目执行细节和后续推进状态。
- 建立 `docs/research/` 调研目录，启动 Rerun.io 第一阶段详细调研。
- 完成 Rerun.io 调研框架与原子能力清单，明确“直接借鉴、直接复用、封装复用、二次开发、自研替代、暂缓判断”的判断口径。
- 完成 Rerun.io 第一轮公开资料调研，基线为 `rerun-sdk 0.33.0`，覆盖官方定位、系统组成、数据模型、存储、可视化、查询、训练、导入集成、许可证和风险。
- 完成 Rerun.io 二次开发路线判断矩阵，形成短期直接复用、中期外围封装、长期保留替换权的初步路线。
- 在 `README.md` 中补充项目总体路线规划，明确“先借力验证，再外围封装，最后形成自有数据层”的推进策略。

### 2026-06-07

- 确认阶段 2 进入 Rerun.io 本地技术评测，而不是机器人真机接入。
- 确认阶段 2 主线采用“自造焊接工站模拟数据 + 开源机器人数据对照验证”的混合路线。
- 新增阶段 2 设计文档：`docs/superpowers/specs/2026-06-07-rerun-stage-2-local-evaluation-design.md`。
- 在 `README.md` 中补充阶段 2 设计文档入口。
- 新增阶段 2 实施计划：`docs/superpowers/plans/2026-06-07-rerun-stage-2-local-evaluation.md`。
- 按 superpowers 流程完成阶段 2 implementation plan 的任务拆解，并使用 sub-agent 方式完成分步执行和复核。
- 新增 Python 工程骨架和阶段 2 依赖配置：`pyproject.toml`、`src/rerun_stage2/`、`tests/rerun_stage2/`。
- 完成模拟机器人焊接工站数据包生成，覆盖 `manifest.json`、`frames.csv`、`events.csv`、`quality.json`、`point_cloud.csv` 和图像序列。
- 完成 Rerun writer，验证 `.rrd` 写入、多 timeline、Transform3D、图像、点云、轨迹、TCP、工艺参数、缺陷概率和事件日志。
- 完成候选样本 CSV 导出，用于按缺陷概率筛选训练/评测候选帧。
- 完成 external-importer-style CLI：`scripts/rerun_importer_sim_weld.py`。
- 完成阶段 2 运行说明和 Viewer/Blueprint 人工检查清单：`docs/stage2/README.md`、`docs/stage2/viewer_blueprint_checklist.md`。
- 完成 LeRobot PushT 开源机器人小样本下载、字段读取和模拟包转换对照。
- 完成本地 Catalog table 创建/查询尝试和 `.rrd` Chunk/DataFrame 查询尝试。
- 新增阶段 2 技术评测报告：`docs/research/04-rerun阶段二本地技术评测报告.md`。
- 更新 Rerun 二次开发路线判断矩阵，补充阶段 2 验证状态。

### 2026-06-08

- 确认后续工作继续采用 simulation-first 路线，不接真机，先通过仿真数据把 Physical AI 数据层的产品形态、数据模型和验证闭环跑清楚。
- 确认阶段 3 采用“一个深度主场景 + 一个轻量对照场景”的设计：主场景为机器人焊接工站，轻量对照为机械臂抓取/分拣，移动机器人巡检暂缓。
- 确认阶段 3 输出不能只是文档，需要包含自有数据包 schema、开发期 validator、Rerun adapter、两个仿真样例和最小候选导出能力。
- 新增阶段 3 设计文档：`docs/superpowers/specs/2026-06-08-simulation-first-physical-ai-data-package-design.md`。
- 阶段 3 设计文档已完成三轮 spec review，并根据评审意见补充 `rerun` 可选性、坐标系结构、引用约定、候选帧归属、`sim_time` 默认规则和候选 CSV 最小列。
- 新增阶段 3 实施计划：`docs/superpowers/plans/2026-06-08-simulation-first-physical-ai-data-package.md`。
- 阶段 3 实施计划已完成三轮 plan review，修正 validator warning、`_ref` 校验范围、events/metrics 时间戳校验和 smoke/final verification 环境可复现性问题。
- 完成阶段 3 implementation 初稿：新增 `physical_ai_data` Python package，形成 Physical AI Package v0.1 的 schema/validator、package IO、候选导出、Rerun adapter 和 CLI prototype。
- 完成两个仿真样例生成能力：机器人焊接工站 `robot_welding_station` 和机械臂抓取/分拣 `arm_pick_sort`。
- 完成 candidate export，默认输出 `PACKAGE/derived/candidates.csv`，用于人工复核、训练样本筛选和评测样本整理。
- 完成 Rerun adapter，将通过 validator 的 Physical AI Package 转换为 `.rrd`；Rerun 在阶段 3 中定位为 adapter backend，不是业务 schema。
- 完成 Stage 3 CLI：`generate`、`validate`、`summarize`、`export-candidates`、`convert-rerun`。
- 测试和复核进展：已形成 `tests/physical_ai_data/` 单元测试覆盖，并完成最终 smoke；Viewer/Blueprint 人工检查和性能冒烟仍需补充。
- 阶段 3 最终 smoke 结果：`PYTHONPATH=src python3 -m pytest -q` 返回 `68 passed`；两个 24 帧样例包均生成、校验、汇总、导出候选 CSV、转换 `.rrd` 成功，两个 `.rrd` 均通过 `rerun rrd verify`。
- 新增阶段 3 运行说明：`docs/stage3/README.md`。
- 新增阶段 3 实施记录：`docs/research/05-physical-ai数据包阶段三实施记录.md`。

### 2026-06-09

- 确认 Stage 4 进入 LeRobot Open Dataset Workflow，不接机器人硬件、不训练模型，先用开源机器人操作数据验证 Physical AI Package 对真实社区数据的承接能力。
- Stage 4 已形成 LeRobot normalized episode/frame 表示、import adapter、lazy loader 和 `import-lerobot` CLI，LeRobot 依赖保持为可选安装，不破坏默认开发安装路径。
- Stage 4 已形成 `pusht`、`aloha`、`fallback` profile：PushT 用于 full acceptance，ALOHA 用于代表性多相机 smoke，fallback 用于未知 repo 的保守映射。
- Stage 4 已支持把 LeRobot feature schema、stats、episode metadata、task metadata、state/action artifact 写入 Physical AI Package，并生成 `action_norm`、`state_norm`、`action_delta`、`image_available` 等候选筛选线索。
- Stage 4 已形成 Rerun 多相机引用支持：`frames.csv` 保留主 `image_ref`，扩展列 `image_refs_json` 记录同一 frame 的全部相机 artifact。
- 新增 Stage 4 运行说明：`docs/stage4/README.md`。
- 新增 LeRobot 到 Physical AI Package 映射文档：`docs/research/06-lerobot到physical-ai-package映射.md`。
- 新增 LeRobot 开放数据样板链路记录：`docs/research/06-lerobot开放数据样板链路记录.md`；历史记录保留了环境建立前的依赖阻塞，Stage 4.1 已更新为真实 PushT quick smoke 和 ALOHA representative smoke 通过。
- Stage 4.1 已建立真实 LeRobot smoke 的独立 `uv` 环境：新增 `tool.uv.override-dependencies`，使 LeRobot dataset loader 与项目 `rerun-sdk[dataplatform]>=0.33.0` baseline 共存；该设置不降低 Rerun baseline，也不把 LeRobot 变成默认依赖。
- Stage 4.1 已生成 `uv.lock`，`uv sync --extra dev --extra lerobot` 通过；当前环境版本为 Python 3.13.5、`lerobot==0.4.4`、`rerun-sdk==0.33.0`，并确认 `lerobot.datasets.lerobot_dataset.LeRobotDataset` 可导入。
- Stage 4.1 已完成 Hugging Face metadata 探测：`lerobot/pusht` 与 `lerobot/aloha_sim_transfer_cube_human` 均可访问；环境建立阶段 `uv run python -m pytest -q` 返回 `92 passed`。
- Stage 4.1 默认非 LeRobot 路径未改为依赖 LeRobot；本机系统 Python 缺少 `pip`/`pytest`，因此补充使用临时 `.[dev]` 环境验证。最终回归中 `lerobot_installed=False`，并在前置该 venv `bin` 到 `PATH` 后返回 `99 passed`。
- Stage 4.1 已针对 LeRobot 0.4.4 的真实旧格式数据补 loader fallback：`lerobot/pusht` 可通过 Hugging Face streaming 读取 parquet 行，`lerobot/aloha_static_towel` 可按 metadata video keys 解码 4 路相机图像。
- Stage 4.1 已跑通真实 `lerobot/pusht` quick smoke：120 frames import、validate、summarize、export-candidates、convert-rerun 和 `rerun rrd verify` 均通过。
- Stage 4.1 已跑通真实 `lerobot/aloha_static_towel` representative smoke：60 frames、`cam_high`/`cam_left_wrist`/`cam_low`/`cam_right_wrist` 四路相机、`image_refs_json`、candidate export、Rerun `.rrd verify` 均通过。
- Stage 4.1 已完成 `lerobot/pusht` full acceptance 尝试：不加 `--max-frames` 导入 161 frames，validate/summarize/export-candidates/convert-rerun 和 full/quick/ALOHA representative `.rrd verify` 均通过；native Rerun GUI 在当前自动化环境触发 wgpu surface 尺寸错误，Viewer/Blueprint 人工视觉验收未完成，仅保留 headless Viewer 截图和 `.rrd verify` 证据。
- Stage 4.1 最终回归完成：`uv run python -m pytest -q` 返回 `99 passed`，最终整体 review 为 No findings；本地生成的 `.venv/`、`artifacts/`、cache、`.rrd` 均未纳入 git 跟踪。

### 2026-06-10

- 完成 Stage 4.2 SDK wrapper / external importer 边界设计文档：`docs/superpowers/specs/2026-06-10-sdk-wrapper-importer-boundary-design.md`。
- 完成 Stage 4.2 实施计划：`docs/superpowers/plans/2026-06-10-sdk-wrapper-importer-boundary.md`。
- 新增最小 Python SDK wrapper：`from physical_ai_data import validate, summarize, export_candidates_csv, convert_to_rerun, export_training_eval_draft`。
- 新增 external importer contract：`ImportRequest`、`ImportResult`、`PackageImporter` 和 `run_import`，把外部数据源到 Physical AI Package 的边界显式化。
- 将 LeRobot importer 沉淀为 `LeRobotPackageImporter` contract 实现，`import-lerobot` CLI 参数映射为 `ImportRequest` 后再通过 `run_import` 执行。
- 新增 training/evaluation draft export：`physical_ai_data.training_export.export_training_eval_draft`，默认输出 `PACKAGE/derived/training_eval/training_eval_manifest.json` 和 `samples.csv`。
- 新增 CLI 子命令 `export-training-draft`，用于从已有 package candidates 生成最小 training/evaluation draft。
- 修复 SDK import-side-effect 测试的进程内 `sys.modules` 清理副作用，避免与 importer monkeypatch 测试产生顺序依赖。
- 本轮最终验证结果：
  - `python -m pytest tests/physical_ai_data/test_sdk.py -q`：`3 passed in 0.72s`。
  - `python -m pytest tests/physical_ai_data/test_training_export.py tests/physical_ai_data/test_sdk.py tests/physical_ai_data/test_importers.py tests/physical_ai_data/test_cli.py tests/physical_ai_data/test_lerobot_cli.py -q`：`35 passed in 2.20s`。
  - `python -m pytest -q`：`123 passed in 4.62s`。
- 完成 Stage 4.3 training/evaluation export contract 与非 LeRobot importer 设计文档：`docs/superpowers/specs/2026-06-10-stage-4-3-training-importer-contract-design.md`。
- 完成 Stage 4.3 实施计划：`docs/superpowers/plans/2026-06-10-stage-4-3-training-importer-contract.md`。
- 将 training/evaluation draft export 收紧为 `physical-ai-training-eval-draft/v0.2`：
  - manifest 明确 `contract_status=draft`、`formal_format=false`、`allowed_splits`、`samples_schema_version`、`sample_count` 和 `candidate_count`。
  - split 只允许 `unspecified`、`train`、`eval`、`validation`、`test`、`holdout`，默认仍为 `unspecified`，不做自动切分。
  - `samples.csv` 明确 package、candidate 来源、label 占位和 `primary_artifact_ref` 字段，继续声明不是正式训练框架格式。
- 新增非 LeRobot `CsvRecordingPackageImporter` fixture：
  - source format 为 `csv_recording`，通过现有 `ImportRequest`、`ImportResult` 和 `run_import` 执行。
  - 输入为本地单文件 `frames.csv` 和可选相对图片，输出标准 Physical AI Package。
  - manifest `source_dataset` 记录源目录、源 CSV 引用、frame count 和转换时间。
  - 该 importer 用于 contract 验证，不新增 CLI、registry 或生产业务 connector。
- Stage 4.3 继续保持 Physical AI Package 作为主数据结构，Rerun 作为可替换 adapter backend。
- Stage 4.3 本轮最终验证结果：
  - `python -m pytest -q`：`148 passed in 3.21s`。
- 完成 Stage 4.4 Weld Workcell 业务 importer candidate 设计文档：`docs/superpowers/specs/2026-06-10-stage-4-4-weld-workcell-importer-design.md`。
- 完成 Stage 4.4 实施计划：`docs/superpowers/plans/2026-06-10-stage-4-4-weld-workcell-importer.md`。
- 新增 `WeldWorkcellPackageImporter`：
  - source format 为 `weld_workcell`，继续复用 `ImportRequest`、`ImportResult` 和 `run_import`。
  - 输入为本地机器人焊接工站业务导出目录，必需 `job.json`、`frames.csv`、`process.csv`、`events.csv`，可选 `review_labels.csv` 和图片目录。
  - 输出为 `robot_welding_station` Physical AI Package，保留源 JSON/CSV 到 `artifacts/source/`，并写入 TCP 轨迹、metrics、events、labels 和 source_dataset traceability。
  - 支持 `copy_images=True/False`；图片路径在两种模式下都需要通过相对路径、存在性和 symlink escape 校验。
  - `review_status` 和 `reviewer` 只保留在 source artifact，不扩展当前 `labels.csv` schema。
- Stage 4.4 将 importer contract 从 LeRobot/fixture 推进到第一个贴近业务的多文件导出 candidate，但不新增 CLI、registry、plugin lifecycle，也不接真实机器人、PLC、OPC UA、MES、HMI 或数据库。
- Stage 4.4 输出 package 已验证可继续进入 validate、summarize、export-candidates、training/evaluation draft export 和非 GUI Rerun `.rrd` adapter。
- Stage 4.4 本轮最终验证结果：
  - `python -m pytest tests/physical_ai_data/test_weld_workcell_importer.py tests/physical_ai_data/test_rerun_adapter.py tests/physical_ai_data/test_training_export.py -q`：`51 passed in 0.78s`。
  - `python -m pytest -q`：`173 passed in 2.69s`。

### 2026-06-11

- 确认下一阶段不再命名为 Stage 4.5，而是进入 **Stage 5：业务接入与交付文档阶段**。
- 完成 Stage 5 业务接入与交付文档设计文档：`docs/superpowers/specs/2026-06-11-stage-5-handoff-docs-design.md`。
- 完成 Stage 5 Handoff Docs 实施计划：`docs/superpowers/plans/2026-06-11-stage-5-handoff-docs.md`。
- 更新根目录 `README.md`，使其从研发路线记录进一步变成项目入口，覆盖当前可用能力、快速开始、常用命令、工程团队对接、文档目录、当前边界和当前状态。
- 新增 Stage 5 总览文档：`docs/stage5/README.md`，说明本阶段从技术可行性转向业务 handoff，给出面向对象、阅读顺序、系统产出物、最小验收流程和非目标。
- 新增工程团队对接文档：`docs/stage5/engineering_handoff.md`，覆盖对接目标、工程团队需要准备的数据、推荐导出目录、字段 contract、Python 调用方式、系统产出物、验收 checklist、常见错误和对接会议问题清单。
- 在 `docs/stage4/README.md` 增加 Stage 5 工程对接入口，并将 Weld Workcell 示例源目录改为明确占位路径 `path/to/source_root`，避免误认为仓库内已有真实 fixture。
- Stage 5 本轮不新增生产代码、CLI、SDK API、package schema 或真实业务数据；目标是把 Stage 2-4.4 的研发成果整理为工程团队可读、可准备、可验收的交付材料。
- Stage 5 本轮最终验证结果：
  - `python scripts/physical_ai_package.py generate welding --output-dir /tmp/stage5_demo_weld`、`validate`、`summarize`、`export-candidates`、`export-training-draft --split eval`、`convert-rerun`：全部 exit 0，生成 `/tmp/stage5_demo_weld/derived/candidates.csv`、`/tmp/stage5_demo_weld/derived/training_eval/samples.csv` 和 `/tmp/stage5_demo_weld.rrd`。
  - `python -m pytest -q`：`173 passed in 3.06s`。
- 确认 Stage 6 定义为 **真机数据接入与数据资产化试点**，阶段主线从离线 handoff 文档推进到真实机器人数据接入路径、数据资产边界和后续产品化取舍。
- Stage 6 关键决策：
  - 真机接入优先，优先围绕真实 SDK/TCP JSON/文件/DB payload 样本校准数据链路，而不是继续扩展仿真能力。
  - 现有素材/数据模块升级为真机数据资产模块，用于承接 Raw Zone、Clean Zone、脱敏、字段映射、候选样本和验收记录。
  - 独立产品路线预留，但本阶段不把 Stage 6 试点直接固化为正式产品内核。
  - Rerun 继续定位为可替换 replay backend；本阶段不 fork Rerun、不把 Rerun 作为主产品内核、不自研 viewer。
- 新增真机数据素材入口：`docs/real-data/1.jpg`、`docs/real-data/2.jpg`、`docs/real-data/README.md`。
- 新增 Stage 6 设计与执行文档：`docs/superpowers/specs/2026-06-11-stage-6-real-robot-ingestion-design.md`、`docs/superpowers/plans/2026-06-11-stage-6-real-robot-ingestion.md`、`docs/stage6/README.md`、`docs/stage6/real_robot_data_asset_module.md`、`docs/stage6/real_data_field_mapping.md`。
- 更新根目录 `README.md` 和 Stage 5 文档，使离线 handoff 被重新定位为脱敏交换、回归测试和离线验收格式；Stage 6 的主线则转向真机数据接入和数据资产化。
- Stage 6 本轮不新增生产 connector、DB schema、TCP/IP server、SDK bridge、package schema changes 或正式训练数据集格式；后续是否扩展这些能力，需要基于真实样本和字段缺口再判断。
- Stage 6 本轮最终验证结果：
  - CLI 链路：`python scripts/physical_ai_package.py generate welding --output-dir /tmp/stage6_demo_weld`、`python scripts/physical_ai_package.py validate /tmp/stage6_demo_weld --json`、`python scripts/physical_ai_package.py summarize /tmp/stage6_demo_weld --json`、`python scripts/physical_ai_package.py export-candidates /tmp/stage6_demo_weld`、`python scripts/physical_ai_package.py export-training-draft /tmp/stage6_demo_weld --split eval`、`python scripts/physical_ai_package.py convert-rerun /tmp/stage6_demo_weld --output-rrd /tmp/stage6_demo_weld.rrd`：全部 exit 0，生成 `/tmp/stage6_demo_weld/derived/candidates.csv`、`/tmp/stage6_demo_weld/derived/training_eval/samples.csv` 和 `/tmp/stage6_demo_weld.rrd`。
  - 全量测试：`python -m pytest -q`：`173 passed in 3.35s`。

### 2026-06-16

- 确认 Stage 7 定义为 **仿真优先小作业窗口数据试点**：当前还不具备真机接入条件，因此先选择 simulated small job window pilot，而不是假设已有真实 SDK/TCP/DB 接入。
- Stage 7 关键决策：
  - 使用 Raw/Clean fixture 模拟一个最小焊接作业窗口，不实现 production connector。
  - Raw Zone 保留仿真 SDK/TCP JSON、文件、过程记录和事件样貌；Clean Zone 收敛到现有 `weld_workcell` importer contract。
  - Clean Zone 通过现有 `WeldWorkcellPackageImporter` 进入 Physical AI Package，继续复用 validate、summarize、candidate export、training/evaluation draft 和 Rerun `.rrd` adapter 链路。
  - 后续真实/脱敏样本到位后，再根据字段、时间、坐标、脱敏、权限和部署缺口决定是否需要 connector skeleton、DB schema、package schema changes，或只演进 importer/清洗流程。
- Stage 7 新增文件：
  - `src/physical_ai_data/stage7_sim_window.py`
  - `scripts/generate_stage7_sim_window.py`
  - `tests/physical_ai_data/test_stage7_sim_window.py`
  - `docs/stage7/README.md`
  - `docs/stage7/sample_request_checklist.md`
  - `docs/stage7/raw_clean_zone_pilot.md`
  - `docs/superpowers/specs/2026-06-16-stage-7-simulated-small-job-window-pilot-design.md`
  - `docs/superpowers/plans/2026-06-16-stage-7-simulated-small-job-window-pilot.md`
- 本轮入口文档更新：
  - `README.md`：将当前主线从 Stage 6 更新为 Stage 7，补充 fixture generator、常用命令、Stage 7 推荐阅读、路线规划、边界、文档目录和当前状态。
  - `details.md`：记录 Stage 7 决策、产出物、验证命令和 Stage 8-oriented 下一步计划。
- 验证前确认当前 Python editable install 原指向外层仓库，先在本 worktree 运行 `python -m pip install -e ".[dev]"`，随后用户指定的 package chain smoke 可正确解析 `physical_ai_data.stage7_sim_window`。
- Stage 7 本轮最终验证命令：
  - `python -m pytest tests/physical_ai_data/test_stage7_sim_window.py -q`：`7 passed in 0.52s`。
  - `python scripts/generate_stage7_sim_window.py --output-root /tmp/stage7_sim_weld_window --frames 5`：exit 0，生成 `/tmp/stage7_sim_weld_window/raw` 和 `/tmp/stage7_sim_weld_window/clean/weld_workcell`。
  - package chain smoke：`run_import` 生成 `/tmp/stage7_chain/package`；`validate --json` 返回 `ok: true`、`frame_count: 5`、`event_count: 2`、`label_count: 1`、`metric_count: 30`；`summarize --json`、`export-candidates`、`export-training-draft --split eval` 和 `convert-rerun` 均 exit 0，生成 `/tmp/stage7_chain/package/derived/candidates.csv`、`/tmp/stage7_chain/package/derived/training_eval` 和 `/tmp/stage7_chain/package.rrd`。
  - `python -m pytest -q`：`180 passed in 2.96s`。

### 2026-06-22

- 完成 Stage 7.1 战略重定位：B06 从历史性的 Rerun/Robotic IOT 阶段叙述收束为 **工业物理 AI 数据层**，定位为公司在机器人、智能工站、设备时序和系统级协同项目中的横向数据底座。
- 确认 Stage 7.1 决策：当前第一样板是 A01 H300 最小焊接作业窗口数据试点；当前仍没有真机接入条件，因此 simulated Raw/Clean fixture 继续作为默认可运行路径，不声称已有真实 H300 数据。
- 更新 README 首页结构：按项目定位、主链路、当前第一样板、当前可用能力、四类项目 profile、工程对接方式、当前边界、快速开始/常用命令组织，并保留历史阶段路线和文档目录在后半部分。
- 明确主链路为共享上游与 profile-specific consumption：Raw Zone -> Clean Zone -> Physical AI Package -> Rerun 回放 -> candidate sample export -> training/evaluation draft；A01、A02、B08、S01 分别消费 job-window evidence、`ManipulationSkillAsset` evidence handoff、timeseries observation candidates/result references 和 manufacturing event context/evidence references。
- 新增并索引 profile docs：`docs/profiles/README.md`、`docs/profiles/a01_weld_workcell_job_window.md`、`docs/profiles/a02_manipulation_skill_asset_evidence.md`、`docs/profiles/b08_equipment_timeseries_observation_package.md`、`docs/profiles/s01_manufacturing_event_context_package.md` 和 `docs/profiles/b06_to_a02_evidence_handoff.md`。
- 完成 A01 H300 sample request 与 field alignment 文档收敛：`docs/stage7/sample_request_checklist.md` 明确真实/脱敏样本请求，`docs/stage7/h300_weld_workcell_field_alignment.md` 说明 H300 字段如何对齐 `weld_workcell` Clean contract。
- 完成 B06 -> A02 handoff 口径：A01 作业窗口中的已确认轨迹、TCP/路径点、质量标签、专家审查、失败边界等可作为 A02 `ManipulationSkillAsset` 候选 evidence；大体量点云、图像、日志和敏感现场文件默认作为上下文或附件引用，不自动进入技能资产核心字段。
- 明确真实/脱敏/仿真/临时 artifact/不可提交数据边界：真实数据不直接提交仓库，脱敏数据需确认可提交边界，仿真数据作为默认可运行样本，临时 artifact 放在 `artifacts/` 或 `/tmp`，客户现场原始文件、未脱敏图像/点云、账号密钥、内部网络地址、权限配置和商业敏感字段不可提交。
- 明确当前仍不做生产 connector、不做通用 IoT 平台、不新增 TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连、DB ingestion、长期 DB schema 或 Physical AI Package schema changes。
- Stage 7.1 本轮最终验证结果：
  - 战略关键词扫描：`rg -n "工业物理 AI 数据层|Raw Zone|Clean Zone|Physical AI Package|weld_workcell_job_window|manipulation_skill_asset_evidence|equipment_timeseries_observation_package|manufacturing_event_context_package|H300|ManipulationSkillAsset" README.md details.md docs/profiles docs/stage7` 返回 exit 0，确认 README、details、profile 和 Stage 7.1 文档均覆盖关键口径。
  - 误承诺扫描：按 Stage 7.1 指定词表扫描 README、details、profile 和 Stage 7.1 文档；仅命中 `docs/stage7/sample_request_checklist.md` 中的否定句，未发现真实接入或生产接入已完成的表述。
  - `python scripts/generate_stage7_sim_window.py --output-root /tmp/stage7_1_sim_weld_window --frames 5`：exit 0，生成 `/tmp/stage7_1_sim_weld_window/raw` 和 `/tmp/stage7_1_sim_weld_window/clean/weld_workcell`。
  - `python -m pytest -q`：`180 passed`。
- 完成 Stage 8 A01 H300 synthetic demo readiness：本阶段明确不命名为真实数据试点，也不声称已有真实或脱敏 H300 样本。
- Stage 8 关键决策：
  - 使用独立 H300-oriented synthetic Raw/Clean fixture 作为第二轮 readiness/demo 样板，Stage 7.1 保留为 A01 H300 Clean Zone contract 和 simulated fixture 的历史基线。
  - Raw Zone 允许记录 H300 story、PCL、点云、模型输出、人工修正和质量结果等 source artifacts；Clean Zone 继续只承诺现有 `weld_workcell` importer contract。
  - 通过 `gap register` 管理真实/脱敏样本替换的缺口，不在无样本条件下扩展现场协议、connector、DB 或 package schema。
  - A02 只接收 synthetic evidence handoff 示例口径；不定义 A02 schema，不提供自动 converter。
- Stage 8 新增交付物：
  - `src/physical_ai_data/stage8_h300_demo.py`
  - `scripts/generate_stage8_h300_synthetic_demo.py`
  - `tests/physical_ai_data/test_stage8_h300_demo.py`
  - `docs/stage8/README.md`
  - `docs/stage8/capability_visualization_report.md`
  - `docs/stage8/h300_synthetic_to_real_gap_register.md`
  - `docs/stage8/a02_evidence_demo_example.md`
  - `docs/superpowers/specs/2026-06-22-stage-8-h300-synthetic-demo-readiness-design.md`
  - `docs/superpowers/plans/2026-06-22-stage-8-h300-synthetic-demo-readiness.md`
- Stage 8 本轮没有新增 production connector、TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连、DB ingestion、长期 DB schema、Physical AI Package schema changes、A02 schema 或 A02 自动转换工具。
- Stage 8 本轮最终验证结果：
  - `rm -rf /tmp/stage8_h300_demo /tmp/stage8_h300_package /tmp/stage8_h300_package.rrd`：exit 0。
  - `python scripts/generate_stage8_h300_synthetic_demo.py --output-root /tmp/stage8_h300_demo --frames 5`：exit 0，生成 `/tmp/stage8_h300_demo/raw` 和 `/tmp/stage8_h300_demo/clean/weld_workcell`。
  - `PYTHONPATH=src python - <<'PY' ... run_import(WeldWorkcellPackageImporter(), ImportRequest(...)) ... PY`：exit 0，生成 `/tmp/stage8_h300_package`。
  - `python scripts/physical_ai_package.py validate /tmp/stage8_h300_package --json`：exit 0，返回 `ok: true`、`frame_count: 5`、`event_count: 2`、`label_count: 1`、`metric_count: 30`、`artifact_ref_count: 7`。
  - `python scripts/physical_ai_package.py summarize /tmp/stage8_h300_package --json`：exit 0，返回 phases `approach`、`cooldown`、`weld`，event types `arc_start`、`manual_review_required`。
  - `python scripts/physical_ai_package.py export-candidates /tmp/stage8_h300_package`：exit 0，生成 `/tmp/stage8_h300_package/derived/candidates.csv`。
  - `python scripts/physical_ai_package.py export-training-draft /tmp/stage8_h300_package --split eval`：exit 0，生成 `/tmp/stage8_h300_package/derived/training_eval`。
  - `python scripts/physical_ai_package.py convert-rerun /tmp/stage8_h300_package --output-rrd /tmp/stage8_h300_package.rrd`：exit 0，生成 `/tmp/stage8_h300_package.rrd`。
  - `python -m pytest tests/physical_ai_data/test_stage8_h300_demo.py -q`：`7 passed in 0.62s`。
  - `python -m pytest -q`：`187 passed in 3.00s`。
  - Stage 8 关键词扫描：exit 0，确认 README、details、Stage 7/8 文档、Stage 8 spec 和 plan 均覆盖 Stage 8、H300 synthetic、synthetic-to-real、gap register、A02 evidence handoff 和生成脚本口径。
  - Stage 8 误承诺扫描：首次按全历史递归范围执行时命中 `docs/superpowers/plans/2026-06-22-stage-7-1-industrial-physical-ai-profile-alignment.md` 中的旧扫描命令文本；随后将 Stage 8 验收扫描范围收敛到本轮新增/更新文件后，误承诺扫描 exit 1，无命中。

### 2026-06-23

- 完成 Stage 9 SDK 化与用户入口收敛：B06 对外定位收束为 **Python SDK first** 的工业物理 AI 数据层工具包。
- 明确入口关系：`physical_ai_data` 是主产品 SDK，`physical-ai-package` 是安装后的标准 CLI 薄入口，`scripts/` 保留为兼容入口和开发期生成器。
- 已新增 pyproject console entrypoint：`physical-ai-package = physical_ai_data.cli:main`。
- 已新增 `physical_ai_data.pipelines.run_weld_workcell_pipeline`，用于从 Stage 8 `weld_workcell` Clean Zone 一步生成 Physical AI Package、校验、汇总、候选样本、training/evaluation draft 和可选 Rerun `.rrd`。
- 根目录 `README.md` 已新增“如何使用本项目”章节、SDK/CLI/scripts 关系表、Mermaid 架构图和三分钟运行流程，并把默认命令切到 `physical-ai-package run-weld-workcell`。
- SDK 文档入口收敛到 `docs/sdk/README.md`，覆盖稳定公共 API、pipeline helper、importer contract、CLI 与 scripts 的关系和当前边界。
- 本轮没有新增 Streamlit/Web app、production connector、DB/schema、H300 现场协议或 plugin system。
- 完成 Stage 10 SDK adoption hardening：本阶段目标是让研发、平台和工程团队能稳定采用 SDK/CLI，而不是扩大到 production connector、DB/schema、完整 Web 平台或 H300 现场协议。
- 新增 Stage 10 设计与执行文档：
  - `docs/superpowers/specs/2026-06-23-stage-10-sdk-adoption-hardening-design.md`
  - `docs/superpowers/plans/2026-06-23-stage-10-sdk-adoption-hardening.md`
- SDK adoption 文档已扩展：
  - `docs/sdk/README.md`：补齐公共 API、import path、返回对象、pipeline helper、importer contract、错误排查、CLI 到 SDK 映射和边界。
  - `docs/sdk/adoption_checklist.md`：面向接入团队的环境、输入、验收、输出和数据敏感性 checklist。
  - `docs/sdk/stage8_pipeline_walkthrough.md`：不依赖 Jupyter 的 Stage 8 notebook-style walkthrough。
  - `docs/sdk/demo_ui_evaluation.md`：记录轻量 demo UI 的触发条件与非目标，本阶段不实现 UI。
- 新增可运行 examples：
  - `examples/sdk_pipeline_stage8.py`
  - `examples/sdk_existing_package_ops.py`
  - `examples/sdk_low_level_importer.py`
  - `examples/cli_json_smoke.sh`
- 新增 `tests/physical_ai_data/test_examples.py`，覆盖 Python examples 和 CLI JSON smoke，包括从非 repo cwd 调用 shell smoke 的场景。
- 完成 SDK adoption error polish：`run_weld_workcell_pipeline` 的 import/validation failure 信息包含 `clean_root` 或 `package_root`，training draft invalid split 信息包含 draft contract 和允许值。
- Stage 10 本轮最终验证结果：
  - focused verification：`python -m pytest tests/physical_ai_data/test_pipelines.py tests/physical_ai_data/test_training_export.py tests/physical_ai_data/test_examples.py tests/physical_ai_data/test_cli.py tests/physical_ai_data/test_sdk.py -q` 返回 `55 passed in 5.78s`。
  - manual examples：
    - `python examples/sdk_pipeline_stage8.py --output-root /tmp/b06_stage10_sdk_pipeline_verify --frames 5`：exit 0，返回 `validation_ok: true`、`frame_count: 5`，并生成 package、candidates、training draft 和 `.rrd`。
    - `python examples/sdk_existing_package_ops.py --output-root /tmp/b06_stage10_existing_ops_verify --frames 8`：exit 0，返回 `validation_ok: true`、`frame_count: 8`，并生成 candidates、training draft 和 `.rrd`。
    - `python examples/sdk_low_level_importer.py --output-root /tmp/b06_stage10_low_level_verify --frames 5`：exit 0，返回 `source_format: weld_workcell`、`frame_count: 5`。
    - `bash examples/cli_json_smoke.sh /tmp/b06_stage10_cli_json_verify`：exit 0，返回 `validation.ok: true`、`frame_count: 5`。
  - full test suite：`python -m pytest -q` 返回 `211 passed in 6.86s`。
  - boundary scan：`rg -n "production connector|DB schema|完整 Web 平台|H300 现场协议|真实 H300 协议|真实数据试点" README.md details.md docs/sdk docs/superpowers/specs/2026-06-23-stage-10-sdk-adoption-hardening-design.md docs/superpowers/plans/2026-06-23-stage-10-sdk-adoption-hardening.md` exit 0；命中均为非目标、边界或历史阶段说明，未发现声称已完成 production connector、DB/schema、完整 Web 平台或真实 H300 协议的表述。

### 2026-06-24

- 完成 Stage 11 H300 sample replacement readiness：本阶段目标是在 Stage 8 synthetic baseline 和 Stage 10 SDK adoption path 之后，提供真实/脱敏 H300 样本替换前的本地检查、gap 状态口径和文档路径。
- Stage 11 关键决策：
  - readiness checker 只读取本地 `weld_workcell` Clean Zone 和可选 Raw Zone，不写 package、不联网、不提交真实样本。
  - `overall_status=blocked` 只表示 Clean Zone replacement 仍有阻塞项；CLI assessment 本身执行成功时仍返回 exit 0，便于记录 blocked report。
  - Raw/source artifact 缺口只进入 review/gap status，不单独阻断 pipeline smoke。
  - 空 `image_path` 沿用现有 `WeldWorkcellPackageImporter` contract，表示该帧无图片；非空 `image_path` 必须相对、不可越界且目标存在。
  - Stage 11 不实现 production connector、DB/schema、H300 现场协议、demo UI、A02 converter，也不修改 Physical AI Package v0.1 schema。
- Stage 11 新增/更新文件：
  - `src/physical_ai_data/stage11_readiness.py`
  - `tests/physical_ai_data/test_stage11_readiness.py`
  - `docs/stage11/README.md`
  - `docs/superpowers/specs/2026-06-24-stage-11-h300-sample-replacement-readiness-design.md`
  - `docs/superpowers/plans/2026-06-24-stage-11-h300-sample-replacement-readiness.md`
  - `README.md`
  - `details.md`
  - `src/physical_ai_data/cli.py`
  - `tests/physical_ai_data/test_cli.py`
- Stage 11 readiness checker 行为：
  - 必需 Clean Zone 文件为 `job.json`、`frames.csv`、`process.csv`、`events.csv`。
  - 检查 `job.json` 的作业/任务/窗口标识线索和 `weld_workcell` importer required fields，`frames.csv` 的 `timestamp_s`、TCP pose、required columns 和非空图片路径安全性，`process.csv` / `events.csv` 的 CSV header 与 required columns，以及可选 `review_labels.csv` 的 required columns。
  - 若提供 Raw Zone root，读取 `manifest.raw.json` 和 Stage 8 gap register 对应的 source artifact 路径，为 G-003、G-004、G-005、G-009、G-011、G-012 等提供 review evidence。
  - report 输出 `checks`、`gap_statuses` 和 `summary`，可通过 SDK `assess_h300_sample_readiness(...)` 或 CLI `physical-ai-package assess-h300-readiness --clean-root ... --raw-root ... --json` 获取。
- Stage 11 本轮验证结果：
  - 基线验证：实现前在隔离 worktree 运行 `python -m pytest -q` 返回 `211 passed in 10.11s`。
  - Task 1 focused：`python -m pytest tests/physical_ai_data/test_stage8_h300_demo.py tests/physical_ai_data/test_stage11_readiness.py -q` 返回 `17 passed in 0.55s`。
  - Task 2 targeted：`python -m pytest tests/physical_ai_data/test_cli.py::test_cli_assess_h300_readiness_maps_args tests/physical_ai_data/test_cli.py::test_cli_assess_h300_readiness_stage8_json_smoke tests/physical_ai_data/test_cli.py::test_cli_assess_h300_readiness_blocked_report_still_exits_zero tests/physical_ai_data/test_cli.py::test_cli_assess_h300_readiness_text_output_lists_gap_next_steps -q` 返回 `4 passed in 0.21s`。
  - Task 2 combined：`python -m pytest tests/physical_ai_data/test_stage11_readiness.py tests/physical_ai_data/test_cli.py -q` 返回 `34 passed in 2.37s`。
  - 文档阶段 focused：`python -m pytest tests/physical_ai_data/test_stage11_readiness.py tests/physical_ai_data/test_cli.py -q` 返回 `34 passed in 3.14s`。
  - full test suite：`python -m pytest -q` 返回 `224 passed in 11.63s`。
  - Stage 8 fixture generation：`python scripts/generate_stage8_h300_synthetic_demo.py --output-root /tmp/stage11_h300_demo --frames 5` exit 0，生成 `/tmp/stage11_h300_demo/raw` 和 `/tmp/stage11_h300_demo/clean/weld_workcell`。
  - 首次直接运行 `physical-ai-package assess-h300-readiness ...` 命中旧 editable install，CLI 尚未包含新子命令；随后在当前 worktree 执行 `python -m pip install -e ".[dev]"` 后重跑成功。
  - manual readiness smoke：`physical-ai-package assess-h300-readiness --clean-root /tmp/stage11_h300_demo/clean/weld_workcell --raw-root /tmp/stage11_h300_demo/raw --json` exit 0，返回 `overall_status: review_required`、`summary.frame_count: 5`，并包含 12 条 `gap_statuses`。
  - 最终 focused verification：`python -m pytest tests/physical_ai_data/test_stage11_readiness.py tests/physical_ai_data/test_cli.py -q` 返回 `36 passed in 2.29s`。
  - 最终 full test suite：`python -m pytest -q` 返回 `226 passed in 7.04s`。
  - 最终 readiness smoke：重新生成 `/tmp/stage11_h300_demo` 后运行 `physical-ai-package assess-h300-readiness --clean-root /tmp/stage11_h300_demo/clean/weld_workcell --raw-root /tmp/stage11_h300_demo/raw --json`，exit 0，返回 `overall_status: review_required`、`summary.frame_count: 5` 和 12 条 `gap_statuses`。
  - 最终文档正向扫描：`rg -n "Stage 11|sample replacement readiness|assess-h300-readiness|gap register|Stage 12|脱敏 H300|不实现 production connector|不修改 Physical AI Package" README.md details.md docs/stage11 docs/superpowers/specs/2026-06-24-stage-11-h300-sample-replacement-readiness-design.md` exit 0。
  - 最终误承诺扫描：按 Stage 11 指定词表扫描 README、details 和 `docs/stage11`，exit 1，无命中；为避免扫描命令文本自命中，本文不内嵌完整词表。
- Stage 12 建议：只有在至少一条脱敏 H300 最小作业窗口样本完成访问边界、提交边界和受控目录确认后，才进入 first de-identified H300 sample replacement pilot；Stage 12 应基于 Stage 11 report 和 Stage 8 gap register 逐条关闭、拆分或升级缺口。

## 下一步计划

1. 至少一条脱敏 H300 最小作业窗口样本完成访问和提交边界确认后，进入 Stage 12 first de-identified H300 sample replacement pilot，并用 Stage 11 readiness report 驱动 Stage 8 gap register 的关闭、拆分或升级。
2. SDK examples 被稳定采用且有明确评审展示需求后，再评估轻量 demo UI；该 UI 只作为演示入口，不替代 SDK 主产品边界。
3. 在样本驱动的 gap 证明必要前，继续避免 production connector、DB/schema、完整 Web 平台或 H300 现场协议建设。

## 维护约定

- 当 README 中的项目定位、核心路线或文档入口变化时，同步更新 `README.md`。
- 当项目推进状态、阶段性决策、执行记录或下一步任务变化时，同步更新 `details.md`。
- 重要专题材料优先放入 `docs/`，README 和本文档只保留索引、摘要和执行状态。
- 阶段性任务收尾时，先完成 README 和 `details.md` 的必要更新，再创建远端 Pull Request；PR 在远端合并后，切回 `main`、同步远端，并清理对应本地开发分支。
