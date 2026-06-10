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
- Stage 4.1 已完成 Hugging Face metadata 探测：`lerobot/pusht` 与 `lerobot/aloha_sim_transfer_cube_human` 均可访问；`uv run python -m pytest -q` 返回 `92 passed`。
- Stage 4.1 默认非 LeRobot 路径未改为依赖 LeRobot；本机系统 Python 缺少 `pip`/`pytest`，因此补充使用 `/tmp/stage4_1_default_dev_venv` 只安装 `.[dev]` 验证，测试返回 `92 passed` 且 `lerobot_installed=False`。
- Stage 4.1 已针对 LeRobot 0.4.4 的真实旧格式数据补 loader fallback：`lerobot/pusht` 可通过 Hugging Face streaming 读取 parquet 行，`lerobot/aloha_static_towel` 可按 metadata video keys 解码 4 路相机图像。
- Stage 4.1 已跑通真实 `lerobot/pusht` quick smoke：120 frames import、validate、summarize、export-candidates、convert-rerun 和 `rerun rrd verify` 均通过。
- Stage 4.1 已跑通真实 `lerobot/aloha_static_towel` representative smoke：60 frames、`cam_high`/`cam_left_wrist`/`cam_low`/`cam_right_wrist` 四路相机、`image_refs_json`、candidate export、Rerun `.rrd verify` 均通过。
- Stage 4.1 已完成 `lerobot/pusht` full acceptance 尝试：不加 `--max-frames` 导入 161 frames，validate/summarize/export-candidates/convert-rerun 和 full/quick/ALOHA representative `.rrd verify` 均通过；native Rerun GUI 在当前自动化环境触发 wgpu surface 尺寸错误，Viewer/Blueprint 人工视觉验收未完成，仅保留 headless Viewer 截图和 `.rrd verify` 证据。

## 下一步计划

1. 在可稳定启动 native GUI 或 web viewer 的环境中补做 Stage 4 Viewer/Blueprint 人工视觉验收，记录 GUI 观察、截图、布局保存和显示异常。
2. 如需要固定多相机展示体验，基于 ALOHA representative `.rrd` 补充项目自定义 Blueprint 或最小 Viewer 启动说明。
3. 推进 Physical AI Package SDK wrapper、external importer 边界、训练/评估导出和后端替换边界。

## 维护约定

- 当 README 中的项目定位、核心路线或文档入口变化时，同步更新 `README.md`。
- 当项目推进状态、阶段性决策、执行记录或下一步任务变化时，同步更新 `details.md`。
- 重要专题材料优先放入 `docs/`，README 和本文档只保留索引、摘要和执行状态。
- 阶段性任务收尾时，先完成 README 和 `details.md` 的必要更新，再创建远端 Pull Request；PR 在远端合并后，切回 `main`、同步远端，并清理对应本地开发分支。
