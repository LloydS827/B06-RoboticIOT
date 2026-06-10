# Stage 4.4 Weld Workcell Business Importer Candidate 设计

## 1. 背景

Stage 4.3 已经把 training/evaluation draft export 收紧到 `physical-ai-training-eval-draft/v0.2`，并通过 `CsvRecordingPackageImporter` 证明 external importer contract 不是 LeRobot 专用接口。但 `csv_recording` 仍是 fixture：它验证了接口形态，却没有验证真实业务系统常见的多文件导出、工艺参数、任务上下文、事件和人工复核记录如何进入 Physical AI Package。

下一步不宜继续增加开放数据特例，也不宜直接进入正式训练框架导出。更贴近项目路线的做法，是选择一个真实业务 importer candidate，用离线样板模拟智能工站或机器人焊接系统的导出形态，并继续保持 Physical AI Package 为主数据结构、Rerun 为可替换 adapter backend。

## 2. 阶段目标

Stage 4.4 的目标是新增一个机器人焊接工站业务导出 importer candidate：

- source format 为 `weld_workcell`。
- 输入是本地业务导出目录，不依赖网络、真实硬件、数据库或 GUI。
- 输出是合法 `robot_welding_station` Physical AI Package。
- 复用现有 `ImportRequest`、`ImportResult`、`run_import` contract。
- 保留原始业务导出文件到 `artifacts/source/`，便于追溯。
- 让现有 `validate`、`summarize`、`export-candidates`、`export-training-draft` 和 `convert-rerun` 能继续消费输出 package。

本阶段不是生产 connector，也不引入正式 label schema 或训练格式。

## 3. 方案比较

### 方案 A：焊接工站业务导出 importer candidate

新增 `WeldWorkcellPackageImporter`，读取 `job.json`、`frames.csv`、`process.csv`、`events.csv`、可选 `review_labels.csv` 和图片目录，映射为 `robot_welding_station` package。

优点：贴近项目主场景，能验证多文件业务导出、工艺参数和复核标签的最小映射。缺点：仍是离线 candidate，不是真实客户系统 connector。

### 方案 B：先设计 label schema / review schema

先沉淀 label/review 状态规范，再回头接业务 importer。

优点：概念更完整。缺点：缺少真实业务输入牵引，容易设计过度；也会把 Stage 4.4 变成文档主导，而不是可运行链路。

### 方案 C：优先补 Viewer/Blueprint GUI 验收

在 GUI 可用环境中补 Stage 4 Viewer/Blueprint 人工视觉验收。

优点：补历史缺口。缺点：当前阻塞是 GUI 环境，不适合作为默认代码分支目标；也不能推进 importer contract 到业务场景。

## 4. 选定方案

采用 **方案 A：焊接工站业务导出 importer candidate**。

原因：

- 项目路线的主场景本来就是机器人焊接/智能工站，业务 importer 比继续扩 LeRobot 更贴近目标。
- Stage 4.3 已有 CSV fixture，本阶段应从“接口证明”推进到“业务语义证明”。
- 仍然保持离线、可测试、默认路径可运行，不把工作扩大到数据库、OPC UA、MES/HMI 接入或真机采集。
- 输出仍是 Physical AI Package，不引入新的主数据结构。

## 5. 输入 Contract

新增 source format：`weld_workcell`。

`ImportRequest` 示例：

```python
ImportRequest(
    source_format="weld_workcell",
    source={"root": Path("fixtures/weld_workcell_export")},
    output_dir=Path("artifacts/stage4/weld_workcell_package"),
    options={"copy_images": True},
)
```

输入目录：

```text
source_root/
  job.json
  frames.csv
  process.csv
  events.csv
  review_labels.csv     # 可选
  images/               # 可选
```

### 5.1 job.json

必需字段：

- `work_order_id`
- `station_id`
- `robot_id`
- `welder_id`
- `part_id`
- `seam_id`
- `task_name`
- `created_at`

这些字段用于 manifest 的 `package_id`、`task`、`devices`、`objects` 和 `source_dataset`。

### 5.2 frames.csv

必需列：

- `timestamp_s`
- `phase`
- `tcp_x`
- `tcp_y`
- `tcp_z`
- `tcp_qx`
- `tcp_qy`
- `tcp_qz`
- `tcp_qw`
- `image_path`

`image_path` 可为空；非空时必须是相对 `source.root` 的路径，不能是绝对路径、不能包含 `..`，并且需要通过 resolve 检查避免 symlink 逃逸。

### 5.3 process.csv

必需列：

- `timestamp_s`
- `weld_current_a`
- `weld_voltage_v`
- `wire_feed_mpm`
- `gas_flow_lpm`
- `travel_speed_mm_s`
- `defect_probability`

每个数值列映射为 `metrics.csv` 中的 metric。metric timestamp 直接使用 process row timestamp。

### 5.4 events.csv

必需列：

- `timestamp_s`
- `event_type`
- `severity`
- `message`
- `object_id`

`object_id` 可为空；非空时必须是 `part_id` 或 `seam_id` 映射出的对象。

### 5.5 review_labels.csv

文件可选。若文件存在，必需列为：

- `timestamp_s`
- `label_type`
- `value`
- `confidence`

可选列为：

- `review_status`
- `reviewer`

本阶段不扩展 Physical AI Package label schema。`review_status` 和 `reviewer` 保留在 `artifacts/source/review_labels.csv`；映射到 `labels.csv` 时使用现有字段：

- `label_type`
- `value`
- `confidence`
- `source`: `weld_workcell_review`
- `target_ref`: 最近 frame。

`confidence` 必须是 finite float。空 `label_type` 不生成 label；空 `value` 允许保留为空字符串。

## 6. 输出 Package

输出必须是合法 Physical AI Package v0.1：

```text
package_root/
  physical_ai_manifest.json
  frames.csv
  events.csv
  labels.csv
  metrics.csv
  README.md
  artifacts/
    images/
    trajectories/tcp_path.csv
    point_clouds/
    source/
      job.json
      frames.csv
      process.csv
      events.csv
      review_labels.csv
```

`artifacts/source/` 保留原始 JSON/CSV 文件，不重复保存原始图片目录。图片可追溯性通过源 CSV 中的 `image_path`、复制后的 `artifacts/images/frame_XXXX.ext` 和 `source_dataset.image_copy_policy` 说明，避免同时维护两套图片副本。

manifest：

- `scenario_type`: `robot_welding_station`
- `package_id`: `weld_workcell_{work_order_id}_{station_id}`
- `task`: 来自 `job.json`
- `devices`: robot、welder、front camera
- `objects`: part、seam
- `coordinate_frames`: station、robot_base、tcp、camera_front、workpiece
- `source_dataset.format`: `weld_workcell`
- `source_dataset` 记录所有源文件引用、frame count、process row count、event count、label count 和 `converted_at`
- manifest object id 直接使用 `job.json.part_id` 和 `job.json.seam_id`。`events.csv.object_id` 非空时必须等于这两个 id 之一，输出 `events.csv.related_object_id` 原样使用该 id。
- `source_dataset.image_copy_policy`: `copied_to_artifacts_images_frame_id` 或 `image_refs_empty_when_copy_images_false`

frames：

- frame id 按输入顺序生成：`frame_0000`、`frame_0001`。
- timeline 固定为 `sim_time`。
- coordinate frame 固定为 `tcp`。
- `trajectory_ref` 固定为 `artifacts/trajectories/tcp_path.csv`。
- 有图片时复制为 `artifacts/images/frame_XXXX.ext`。

events：

- event id 按输入顺序生成。
- `related_frame_id` 使用最近 frame。最近 frame 按 `abs(frame.timestamp_s - source.timestamp_s)` 选择；如距离相等，选择输入顺序更早的 frame。
- `related_object_id` 使用输入 object id；为空则为空。

labels：

- review labels 可选。
- label target 使用最近 frame，规则同 events。
- 不在 package schema 中新增 `review_status` 字段。

metrics：

- process 每个数值列生成一个 metric。
- metric name 使用稳定名称：`weld_current`、`weld_voltage`、`wire_feed`、`gas_flow`、`travel_speed`、`defect_probability`。
- unit 分别为 `A`、`V`、`m/min`、`L/min`、`mm/s`、`ratio`。

## 7. 错误处理

 importer 应拒绝：

- `source_format` 不匹配。
- 缺少 `source.root`、`job.json`、`frames.csv`、`process.csv` 或 `events.csv`。
- `job.json` 缺必需字段。
- CSV 缺必需列或存在 malformed row。
- `frames.csv` 没有任何数据行。
- 数值字段无法解析为 finite float。
- 非空 `image_path` 使用绝对路径、`..`、symlink 逃逸或指向不存在文件。
- `events.csv.object_id` 引用未知对象。

错误使用 `ValueError`，消息应包含具体缺失文件、字段或列名，便于 importer 使用方定位。

## 8. 测试策略

新增测试覆盖：

- happy path：本地 fixture 生成合法 `robot_welding_station` package。
- manifest source_dataset traceability。
- frames、trajectory、metrics、events、labels 的关键映射。
- 输出 package 可通过 `validate_package`、`summarize_package`、`export_candidates` 和 `export_training_eval_draft`。
- 输出 package 可通过非 GUI 的 Rerun adapter smoke，验证 `.rrd` 文件生成；不要求 native Viewer/Blueprint 人工验收。
- `copy_images=False` 时 image refs 为空但 package 仍合法。
- source format mismatch。
- 缺必需文件、缺必需 job 字段、缺 CSV 必需列。
- malformed CSV rows。
- image path absolute、parent traversal、symlink escape 和 missing image。
- event object id 引用未知对象。
- 最近 frame 规则：超出 frame 时间范围时选最近端点，tie 选较早 frame。

默认测试不能依赖网络、LeRobot、真实硬件、GUI 或本地缓存。

## 9. 文档更新

需要更新：

- `README.md`：增加 Stage 4.4 spec/plan 入口和当前状态摘要。
- `details.md`：记录 Stage 4.4 完成事项、验证结果和下一步计划。
- `docs/stage4/README.md`：新增 Weld Workcell importer candidate 使用示例和输入 contract。

## 10. 非目标

Stage 4.4 不做：

- 不接真实机器人、PLC、OPC UA、MES、HMI 或数据库。
- 不新增 CLI 子命令。
- 不做 importer registry 或 plugin lifecycle。
- 不扩展 Physical AI Package schema version。
- 不实现正式 label schema、review workflow 或训练框架导出。
- 不补做 GUI Viewer/Blueprint 验收。
- 不把 Rerun 变成主数据结构。

## 11. 风险与处理

| 风险 | 处理 |
| --- | --- |
| importer 变成半生产 connector | 明确命名为 candidate，不加 CLI，不接外部服务。 |
| 输入 contract 过宽 | 只支持固定本地目录和固定文件名。 |
| label/review 设计过早扩 schema | review 状态保留在 source artifact，不进入 labels.csv 新列。 |
| 与 CSV fixture 重复 | CSV fixture 是通用接口证明；weld workcell importer 验证业务语义和多文件导出。 |
| 默认测试变慢或依赖外部环境 | 全部使用 pytest tmp_path 生成离线 fixture。 |

## 12. 完成定义

Stage 4.4 完成时应具备：

- 有 `WeldWorkcellPackageImporter`，通过 external importer contract 输出合法 `robot_welding_station` package。
- 业务导出输入 contract、输出映射和错误处理被测试约束。
- 输出 package 可继续进入候选导出和 training/evaluation draft export。
- README、details、Stage 4 文档已同步。
- 默认全量测试通过。

PR、远端合并和本地 worktree/分支清理属于交付流程，不作为 spec 的产品完成定义；本轮仍会按项目维护约定执行这些收尾动作。
