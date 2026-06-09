# LeRobot Open Dataset Workflow 设计

## 1. 背景

Physical AI 数据层已经完成阶段 3 的 simulation-first Physical AI Package 原型：可以生成两个仿真样例包，完成 validator、candidate export、Rerun adapter 和 CLI smoke。阶段 3 证明了数据包结构与本地工具链可运行，但样例数据仍以项目内生成的仿真数据为主。

下一阶段需要把数据源推进到开源机器人操作数据。这样既能避免过早接入真机，又能验证 Physical AI Package 是否能承接真实社区数据集中的 episode、image、state、action、task metadata 和多相机结构。

本阶段选择 LeRobot 作为开源数据入口。LeRobot 官方定位为面向真实机器人机器学习的数据集、模型和工具集合；其数据集格式提供统一的 episode 访问、tabular sensorimotor data、video、metadata 和 feature schema。PushT 作为主验收样例，ALOHA 系列作为代表性 smoke，用于验证更复杂操作数据的兼容性。

参考资料：

- LeRobot 文档：https://huggingface.co/docs/lerobot/en/index
- LeRobot dataset tools：https://huggingface.co/docs/lerobot/en/using_dataset_tools
- LeRobotDataset v3.0：https://huggingface.co/docs/lerobot/lerobot-dataset-v3
- `lerobot/pusht` 数据集：https://huggingface.co/datasets/lerobot/pusht

## 2. 阶段定位

阶段 4 名称：

> LeRobot Open Dataset Workflow

阶段 4 的核心问题是：

> Physical AI Package 能否通过一个通用 LeRobot adapter，承接开源机器人操作数据，并形成可校验、可回放、可筛选、可沉淀为训练/评估样本的样板链路？

本阶段仍不接入真机。真机接入涉及机器人控制器、相机、现场网络、时钟同步和业务进度，应放在后续阶段。

本阶段也不训练模型。训练/评估的重点是数据入口和样本整理，而不是模型效果。

## 3. 命名约定

后续新文档、新代码和新 CLI 文案统一使用：

- `Physical AI Package`
- `Physical AI data layer`
- `Physical AI package schema`

不再使用实验室名称作为规范、产品或 package 命名。历史文档中的旧称可作为历史记录保留；阶段 4 新增内容不得继续引入旧称。

## 4. 目标

本阶段目标：

- 实现一个面向 LeRobot 数据集的通用 adapter。
- 使用 `lerobot/pusht` 完成主验收链路。
- 使用 ALOHA 系列数据集完成代表性 smoke，验证多相机/复杂操作数据的基本兼容性。
- 将 LeRobot episode 转换为 Physical AI Package。
- 保留 LeRobot 的关键 source metadata，便于追溯原始数据集、episode、frame 和 feature schema。
- 跑通 `validate -> summarize -> export-candidates -> convert-rerun -> rerun verify`。
- 形成 LeRobot 到 Physical AI Package 的 schema mapping 文档。
- 更新 README、details 和阶段报告，明确阶段 4 完成内容与限制。

## 5. 非目标

本阶段不做：

- 不接入机器人真机。
- 不训练策略模型，不评估模型指标。
- 不实现完整 LeRobot 数据集管理工具。
- 不修改 LeRobot 源码。
- 不承诺所有 LeRobot 数据集都能完整语义化。
- 不为每个 LeRobot 数据集定制独立 importer。
- 不引入 Web 平台、标注平台、权限系统或生产治理系统。
- 不把 Rerun 作为业务 schema；Rerun 仍是 adapter backend。

## 6. 总体设计

阶段 4 使用三层结构：

### 6.1 通用 LeRobot adapter

通用 adapter 负责读取 LeRobot 数据集的共同结构：

- dataset repo id 或本地路径；
- episode index；
- frame index；
- timestamp；
- task metadata；
- `observation.*` features；
- `observation.images.*` features；
- `observation.state` 或等价 state features；
- `action`；
- dataset feature schema、fps、stats 和 episode metadata。

通用 adapter 只做保守映射，不猜测复杂业务语义。

### 6.2 Dataset profile

dataset profile 负责补充场景语义：

- `pusht` profile：用于主验收，识别 pushing task、2D state/action、episode progress 和基础成功/复盘线索。
- `aloha` profile：用于 smoke，识别多相机、多维 state/action 和复杂操作任务 metadata。
- fallback profile：当数据集没有已知 profile 时，只做通用字段映射，并输出 warning，不阻止生成最小 Physical AI Package。

profile 机制只用于解释语义，不应改变 Physical AI Package 的核心 schema。

### 6.3 Physical AI Package 映射层

映射层输出阶段 3 已定义的数据包结构：

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

LeRobot source metadata 应写入 manifest 的扩展字段，例如：

```json
{
  "source_dataset": {
    "format": "lerobot",
    "repo_id": "lerobot/pusht",
    "episode_index": 0,
    "profile": "pusht",
    "feature_schema_ref": "artifacts/source/lerobot_features.json"
  }
}
```

## 7. 数据选择

### 7.1 主验收：`lerobot/pusht`

PushT 是阶段 4 第一版主验收数据集。选择原因：

- 经典 demo 级任务；
- 数据体量较轻；
- 适合快速验证 importer、schema mapping、validator、Rerun 回放和候选导出；
- 能体现从 open dataset 到 Physical AI Package 的完整链路。

PushT 必须完成完整闭环。

### 7.2 代表性 smoke：ALOHA 系列

ALOHA 系列用于第二 smoke。选择原因：

- 代表性更强；
- 更接近复杂机器人操作数据；
- 更可能覆盖多相机、更高维 state/action 和复杂 episode metadata；
- 能验证 adapter 不只是适配 PushT。

ALOHA smoke 的目标是兼容性验证，不要求第一版完整语义化全部字段。

## 8. 字段映射

### 8.1 Manifest

`physical_ai_manifest.json` 应包含：

- `schema_version`：沿用 `physical-ai-package/v0.1`。
- `package_id`：由 LeRobot repo id、episode index 和 profile 生成稳定 ID。
- `scenario_type`：建议使用 `open_robot_manipulation`。
- `task`：来自 LeRobot task metadata；若缺失则使用 repo id 和 episode index。
- `devices`：从 image/state/action features 推断最小设备集合，例如 camera、robot、controller。
- `objects`：profile 可补充，例如 PushT 的 block/target；fallback profile 可为空或使用 generic object。
- `coordinate_frames`：v0.1 可使用 `world`、`robot_base`、`camera_<name>`、`end_effector` 等最小坐标系；无法推断时保持 default identity。
- `timelines`：必须包含 `episode_time` 和 `sim_time`。其中 `sim_time` 可作为现有 adapter 和候选导出的兼容 timeline。
- `source_dataset`：记录 LeRobot repo id、本地路径、episode index、profile、feature schema 和转换时间。

### 8.2 Frames

`frames.csv` 中每一行对应 LeRobot episode 中的一个 frame：

- `frame_id`：`frame_<index>`。
- `timestamp_s`：使用 LeRobot `timestamp`；缺失时按 fps 和 frame index 推导。
- `timeline`：默认 `sim_time`，并在 manifest 中记录 source timeline 为 `episode_time`。
- `phase`：由 profile 生成；fallback 使用 `episode`.
- `coordinate_frame_id`：优先使用 `robot_base` 或 profile 指定 frame。
- `image_ref`：主 camera image artifact。
- `robot_state_ref`：state/action CSV 或 JSON 引用。
- `tcp_pose_ref`：如果 profile 能推断末端位姿则填入；否则为空。

多相机数据可采用：

- 主相机写入 `image_ref`；
- 其他相机写入扩展列，例如 `image_refs_json`，或写入 manifest `source_dataset.cameras`；
- Rerun adapter 后续可读取扩展列显示多相机。

### 8.3 Events

本阶段不强行从所有数据集中识别真实事件。事件来源包括：

- `episode_start`
- `episode_end`
- profile 识别出的 progress milestone；
- 数据异常，例如 missing image、non-finite action、timestamp gap，可作为 warning event。

PushT profile 可以根据 episode progress 或 state/action 简单生成阶段事件；ALOHA smoke 可只生成 start/end。

### 8.4 Labels

labels 用于训练/评估样本整理，不等同于人工标注平台。

第一版 labels 来源：

- task outcome，如果数据集中存在；
- profile 可推断的 episode-level label；
- fallback 使用 `task_context` 或 `unlabeled`.

若无法可靠判断成功/失败，不得编造 success label。

### 8.5 Metrics

metrics 记录可用于复盘和候选导出的数值：

- action norm；
- state norm；
- action delta；
- timestamp gap；
- image availability；
- profile-specific progress score。

metrics 必须可解释，不能为了导出候选而制造虚假质量指标。

## 9. Candidate Export 设计

阶段 4 继续复用阶段 3 candidate export，但需要增加 LeRobot 场景的候选来源：

- 大 action delta；
- timestamp gap；
- missing image；
- profile-specific milestone；
- episode boundary；
- potential failure/outcome label，如果数据集提供。

候选导出用于复盘与训练/评估样本整理。它不代表最终标注，也不替代模型训练数据切分。

## 10. CLI 形态

阶段 4 建议新增或扩展 CLI：

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/pusht \
  --episode-index 0 \
  --output-dir artifacts/stage4/pusht_episode_0000
```

可选参数：

- `--root PATH`：使用本地 LeRobot 数据缓存或本地数据集。
- `--profile pusht|aloha|auto|fallback`。
- `--max-frames N`：用于 smoke 限制输出规模。
- `--camera NAME`：选择主相机。
- `--copy-images` / `--link-images`：控制 image artifact 处理方式。

导入后继续使用阶段 3 命令：

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage4/pusht_episode_0000 --json
PYTHONPATH=src python3 scripts/physical_ai_package.py summarize artifacts/stage4/pusht_episode_0000 --json
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage4/pusht_episode_0000
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage4/pusht_episode_0000 --output-rrd artifacts/stage4/pusht_episode_0000.rrd
```

## 11. 依赖与可用性

LeRobot 相关依赖不应破坏现有默认工作流。

建议策略：

- `physical_ai_data` 现有能力继续保持默认可测试。
- LeRobot adapter 使用 lazy import。
- 可在 `pyproject.toml` 增加 optional dependency，例如 `.[lerobot]`。
- 单元测试使用小型 fixture 或 fake LeRobot sample，不依赖大规模下载。
- 真实 `lerobot/pusht` 和 ALOHA smoke 放入 smoke 命令或集成测试，不作为默认单元测试硬依赖。

## 12. 测试策略

第一版测试应覆盖：

- LeRobot feature schema 解析。
- episode frame 到 `frames.csv` 的稳定映射。
- image/state/action artifact 生成。
- source metadata 保留。
- PushT profile 输出有效 Physical AI Package。
- fallback profile 在未知数据集上仍能生成最小包并给 warning。
- candidate export 能基于 action/state/timestamp 生成候选。
- Rerun adapter 可转换导入后的 package。
- CLI `import-lerobot` 参数错误返回非零。
- 默认 `PYTHONPATH=src python3 -m pytest -q` 不依赖真实数据下载。

Smoke 测试应覆盖：

- `lerobot/pusht` 完整链路。
- ALOHA 系列至少一个 episode 的轻量链路。
- 两个输出包均通过 validator。
- 两个输出包均可生成 `.rrd` 并通过 `rerun rrd verify`。

## 13. 成功标准

阶段 4 完成时，至少应满足：

- 有 LeRobot Open Dataset Workflow 设计说明。
- 有 LeRobot adapter 原型。
- `lerobot/pusht` 一个 episode 可导入为 Physical AI Package。
- PushT package 可 validate、summarize、export-candidates、convert-rerun，并通过 `rerun rrd verify`。
- ALOHA 系列完成一个 episode 的 smoke，不要求完整语义化。
- 有 LeRobot 到 Physical AI Package schema mapping 文档。
- README、details 和阶段报告更新。
- 新增能力不破坏阶段 3 默认命令和测试。

## 14. 风险与应对

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| LeRobot 版本变化 | API 或数据格式不稳定 | adapter lazy import，记录测试时版本，优先依赖公开 dataset abstraction |
| ALOHA 数据过大 | 下载和 smoke 成本高 | 使用 `--max-frames` 和单 episode，必要时只做 metadata + small frame subset |
| 多相机映射复杂 | Rerun 显示和 package 字段膨胀 | 第一版选择主相机，其他相机进入扩展 metadata |
| 语义推断过度 | 生成虚假事件或标签 | fallback 保守映射，不编造 success/failure |
| 默认测试依赖网络 | 新用户无法稳定运行 | 真实数据 smoke 不进入默认单元测试 |
| 命名污染 | 把实验室名误写成产品规范 | 新增内容统一使用 Physical AI Package |

## 15. 后续阶段衔接

阶段 4 完成后，建议进入：

### 阶段 5：Physical AI Package SDK Wrapper

把导入、校验、summary、candidate export、Rerun conversion 封装成稳定 Python API 和 CLI contract。

### 阶段 6：Training/Evaluation Export

基于 candidate rows 和 source metadata，设计训练/评估样本导出格式。

### 阶段 7：真实样板场景接入

在项目进度允许后，再接入真实机器人或智能工站数据，验证在线采集、时钟同步、现场 artifact 和真实复盘需求。

## 16. 待用户 review

本 spec 明确阶段 4 采用 LeRobot 通用 adapter，PushT 为主验收样例，ALOHA 系列为代表性 smoke。用户 review 通过后，下一步进入 implementation plan，不直接开始编码。
