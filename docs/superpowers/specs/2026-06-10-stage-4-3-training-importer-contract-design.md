# Stage 4.3 Training/Evaluation Export Contract 与非 LeRobot Importer 设计

## 1. 背景

Stage 4.2 已经把 Physical AI Package 的调用边界从 CLI 原型推进到最小 SDK wrapper、external importer contract、`LeRobotPackageImporter` 和 training/evaluation draft export。当前链路可以从 package candidates 生成：

```text
PACKAGE/derived/training_eval/
  training_eval_manifest.json
  samples.csv
```

但这个 draft contract 仍偏宽松：manifest 没有明确 samples schema、split 取值和正式格式边界；`samples.csv` 只表达 candidate 到 sample 的基础映射，缺少来源 package、样本来源、label 字段语义和 artifact 引用边界。external importer contract 也主要由 LeRobot 证明，仍需要一个非 LeRobot 的离线 importer fixture 来验证 contract 不是 LeRobot 专用接口。

Stage 4.3 的任务是收紧这些边界，但不进入正式训练框架导出、不做自动切分、不接真机、不补 GUI Viewer 验收。

## 2. 项目判断

本项目的主线仍是“Physical AI Package 作为主数据结构，Rerun 作为可替换 adapter backend”。LeRobot 是开放数据样板，不是产品内核。训练/评估导出也应先服务于数据资产整理和后续训练格式设计，而不是现在就绑定 Hugging Face dataset、PyTorch dataloader 或 LeRobot replay buffer。

因此，本阶段应选择可测试、离线、低耦合的收紧方式：

- training/evaluation draft 明确自身是 draft contract；
- split 语义显式、保守，不自动推断；
- sample 字段覆盖后续训练消费需要的最小索引信息；
- importer contract 用一个本地 CSV 业务录制 fixture 证明非 LeRobot 路径；
- README、details、Stage 4 文档同步记录边界和下一步。

## 3. 方案比较

### 方案 A：小步收紧 contract + 本地 CSV importer fixture

在现有 `training_export.py` 上收紧 manifest 和 samples 字段，新增 split 校验与常量；新增一个 `CsvRecordingPackageImporter`，读取本地单文件 `frames.csv` fixture 和可选图片目录，输出 Physical AI Package。

优点：改动小、默认测试离线、能直接证明 importer contract 与 LeRobot 解耦。缺点：仍是 draft，不解决正式训练格式。

### 方案 B：直接实现正式训练/评估格式

把导出目标升级为 Hugging Face dataset、PyTorch dataloader、LeRobot-compatible buffer 或其他训练框架格式。

优点：更接近模型训练。缺点：当前缺少稳定标签规范、任务评估口径和真实训练消费方，容易过早绑定框架，并削弱 Physical AI Package 的主结构定位。

### 方案 C：只补文档，不改代码

用文档说明 draft/export/importer 边界，不修改实现。

优点：最快，风险最低。缺点：关键边界无法由测试约束，Stage 4.2 的草案状态仍会漂移。

## 4. 选定方案

采用 **方案 A：小步收紧 contract + 本地 CSV importer fixture**。

原因：

- 符合当前“外围封装、保留替换权”的阶段目标。
- 不把 Stage 4.3 扩大成训练系统、数据治理系统或 GUI 验收。
- 能用默认测试证明新增行为，不依赖网络、LeRobot、真实缓存或 GUI。
- 非 LeRobot importer 选择本地 CSV 业务录制，比引入第二个真实外部生态更稳妥。

## 5. Training/Evaluation Draft Contract

### 5.1 Manifest

`training_eval_manifest.json` 继续输出到 `PACKAGE/derived/training_eval/`，但字段收紧为：

- `export_format`: 固定为 `physical-ai-training-eval-draft/v0.2`
- `contract_status`: 固定为 `draft`
- `formal_format`: 固定为 `false`
- `source_package_id`
- `source_package_root`
- `schema_version`
- `scenario_type`
- `split`
- `allowed_splits`
- `samples_csv`
- `samples_schema_version`: 固定为 `physical-ai-training-eval-samples/v0.2`
- `sample_count`
- `candidate_count`
- `created_at`
- `notes`

其中 `notes` 必须说明该导出不是正式训练框架格式，只是 Physical AI Package 的 draft sample index。

### 5.2 Split 语义

Stage 4.3 不做自动切分。`split` 参数可省略，省略时写入 `unspecified`；如果调用方传入 split，则必须是一个允许值。允许值为：

- `unspecified`
- `train`
- `eval`
- `validation`
- `test`
- `holdout`

不接受空字符串、大小写变体或任意自定义值。这样做的目的是避免 draft 导出在无明确策略时悄悄产生不可复现的 train/eval 切分。

### 5.3 Samples CSV

`samples.csv` 字段收紧为：

- `sample_id`
- `split`
- `package_id`
- `frame_id`
- `timestamp_s`
- `candidate_id`
- `candidate_source_type`
- `candidate_source_id`
- `object_id`
- `score`
- `reasons`
- `label_status`
- `label_ref`
- `primary_artifact_ref`
- `package_root`

字段语义：

- `sample_id` 仍由导出器顺序生成，格式为 `sample_0000`。
- `candidate_source_type` 和 `candidate_source_id` 保留 candidate 来源，不再使用含糊的 `source_type`。
- `label_status` 固定为 `unlabeled`，不编造成功/失败或质量标签。
- `label_ref` 预留给后续标注系统或正式 label mapping，Stage 4.3 固定为空。
- `primary_artifact_ref` 从对应 frame 的 `image_ref`、`point_cloud_ref`、`trajectory_ref` 中选择第一个非空引用，便于人工复核和后续训练样本定位。
- `package_root` 保留为调用环境中的 package 路径，不作为可移植正式格式承诺。

## 6. 非 LeRobot Importer Fixture

新增 `CsvRecordingPackageImporter`，source format 为 `csv_recording`。它是一个离线 fixture importer，不是正式业务 connector。

### 6.1 输入 contract

`ImportRequest` 示例：

```python
ImportRequest(
    source_format="csv_recording",
    source={"root": Path("fixtures/csv_recording")},
    output_dir=Path("artifacts/stage4/csv_recording_package"),
    options={"copy_images": True},
)
```

输入目录最小要求：

```text
source_root/
  frames.csv
  images/              # 可选
```

Stage 4.3 只支持单文件 fixture：event、label 和 metric 的输入都来自 `frames.csv` 的列，不支持 sidecar `events.csv`、`labels.csv` 或 `metrics.csv`。这样可以证明 importer contract 的非 LeRobot 性质，同时避免把本阶段扩展成通用 CSV ETL。

`frames.csv` 最小列：

- `timestamp_s`
- `phase`
- `image_path`
- `metric_name`
- `metric_value`

可选列：

- `event_type`
- `event_severity`
- `event_message`
- `label_type`
- `label_value`
- `label_confidence`

最小示例：

| timestamp_s | phase | image_path | metric_name | metric_value | event_type | event_severity | event_message | label_type | label_value | label_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0 | observe | images/frame_0000.png | object_confidence | 0.81 | start | info | Recording started | task_context | demo | 1.0 |
| 0.1 | grasp | images/frame_0001.png | grip_confidence | 0.73 | grasp_attempt | warning | Grip confidence needs review | quality | review | 0.8 |

`image_path` 解析规则：

- 空值允许，输出 frame 的 `image_ref` 为空。
- 非空值必须是相对 `source.root` 的路径，不能是绝对路径或包含 `..`。
- 默认 `copy_images=True`：图片必须存在，并复制到 `artifacts/images/frame_XXXX.ext`。
- `copy_images=False` 仅用于 contract 测试：不复制图片，输出 frame 的 `image_ref` 为空，原始 `image_path` 仍保存在 `artifacts/source/csv_recording_frames.csv`。

### 6.2 输出 contract

importer 输出合法 Physical AI Package：

- `physical_ai_manifest.json`
- `frames.csv`
- `events.csv`
- `labels.csv`
- `metrics.csv`
- `artifacts/images/`
- `artifacts/source/csv_recording_frames.csv`
- `README.md`

manifest 中 `scenario_type` 使用现有 `arm_pick_sort`，避免为 fixture 扩展核心 schema。`source_dataset.format` 为 `csv_recording`，记录源目录、frame count 和转换时间。

最小生成规则：

- frame id 按输入顺序生成：`frame_0000`、`frame_0001`。
- frame timeline 固定为 `sim_time`，coordinate frame 固定为 `robot_base`。
- frame `phase` 直接来自输入；缺失最小列时报错。
- 每个有 `metric_name` 和 `metric_value` 的输入行生成一条 metric，id 为 `metric_XXXX`。
- 每个有 `event_type` 的输入行生成一条 event，id 为 `event_XXXX`；未给 `event_severity` 时使用 `info`，未给 `event_message` 时使用空字符串。
- 每个有 `label_type` 的输入行生成一条 label，id 为 `label_XXXX`，target 为当前 frame；未给 `label_confidence` 时使用 `1.0`。
- 空 optional 列不生成对应 event、label 或 metric。
- 输出 `artifacts/source/csv_recording_frames.csv` 原样保存输入行，便于追溯 fixture 来源。

### 6.3 设计边界

该 importer 只用于 contract 验证：

- 不接真实业务系统；
- 不新增 CLI 子命令；
- 不做 registry 或插件发现；
- 不扩展 Physical AI Package schema；
- 不要求 Rerun 特殊支持，因为已有 package 到 Rerun adapter 可以处理标准 package。

## 7. 文档更新

本阶段需要更新：

- `README.md`：补充 Stage 4.3 文档入口和当前状态摘要。
- `details.md`：记录 Stage 4.3 完成事项、关键决策、验证结果和下一步计划。
- `docs/stage4/README.md`：补充 training/evaluation draft v0.2 contract 和 CSV importer fixture 使用示例。

不补做 Viewer/Blueprint 人工视觉验收，只继续记录为 GUI 环境可用后的任务。

## 8. 测试策略

新增或更新测试覆盖：

- training/evaluation manifest v0.2 字段、draft/formal 边界、sample count 与 candidate count。
- `samples.csv` 新字段顺序、candidate 来源字段、label 占位字段和 `primary_artifact_ref`。
- split 允许值和非法 split 拒绝。
- 旧 candidate CSV 缺必要列仍报错。
- `CsvRecordingPackageImporter` 能从本地 fixture 生成合法 package，并经 `run_import` 返回 `ImportResult`。
- source format mismatch 和缺失输入字段报错。
- 默认全量测试通过，不依赖网络、LeRobot、真实缓存或 GUI。

## 9. 非目标

Stage 4.3 不做：

- 不实现正式训练框架格式。
- 不做自动 train/eval split。
- 不新增 LeRobot 真实数据验收。
- 不接真机或真实业务系统。
- 不扩展 importer registry、entry points 或插件生命周期。
- 不把 Rerun 变成主数据结构。
- 不补做 native GUI Viewer/Blueprint 验收。

## 10. 风险与处理

| 风险 | 处理 |
| --- | --- |
| draft v0.2 被误解为正式训练格式 | manifest 写入 `contract_status=draft`、`formal_format=false` 和 notes。 |
| split 过度自由导致下游不可复现 | 只接受固定允许值，不做自动切分。 |
| CSV importer 被误认为正式业务 connector | 文档和类注释明确它是 fixture importer，不新增 CLI。 |
| sample 字段过宽 | 只加入定位 sample、candidate、label 占位和 primary artifact 所需字段。 |
| 非 LeRobot fixture 侵入 schema | 使用现有 `arm_pick_sort` scenario，不扩展 schema。 |

## 11. 完成定义

Stage 4.3 完成时应具备：

- `export_training_eval_draft` 输出 v0.2 draft manifest 和收紧后的 `samples.csv`。
- split 语义明确并由测试约束。
- 有一个非 LeRobot `csv_recording` importer fixture，能通过 external importer contract 生成合法 Physical AI Package。
- README、details、Stage 4 文档已同步。
- 默认全量测试通过。
- PR 合并后本地开发分支被清理，主工作区保持干净。
