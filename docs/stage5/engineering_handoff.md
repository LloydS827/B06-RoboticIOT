# Stage 5 工程团队对接文档

## 对接目标

本文件用于把机器人焊接工站的一次作业或一小段作业窗口，整理为 `WeldWorkcellPackageImporter` 可读取的离线导出目录。导入成功后，数据层会生成 Physical AI Package，让研发、算法和数据团队可以基于同一份 package 做复盘、候选筛选、训练评估 draft 准备和 Rerun 回放。

当前对接目标是形成可验证的交付样板，不是连接真实 PLC、OPC UA、MES、HMI、机器人控制器或数据库。

Stage 6 后，本文档的定位是离线 handoff 格式，用于脱敏样本交换、回归测试、离线验收和字段 contract 对照；它不是唯一或最终的真机接入路径。在线/准在线真机接入主线应参考 Stage 6 文档中 AI 控制器侧接入、存储、清洗、Physical AI Package 生成、Rerun 回放和训练数据准备的规划。

## 工程团队需要准备什么

- 一次作业或一小段连续作业窗口，能导出稳定的时间序列数据。
- 任务上下文：工单、工位、机器人、焊机、工件、焊缝、任务名、创建时间。
- 帧级数据：时间戳、阶段、TCP 位姿、可选图片路径。
- 工艺参数：电流、电压、送丝速度、气体流量、行走速度、缺陷概率或风险评分。
- 事件记录：时间戳、事件类型、等级、消息、关联对象。
- 可选人工复核：标签类型、值、置信度、复核状态、复核人。

## 推荐导出目录

推荐把一批离线导出数据放在一个 `source_root` 目录下：

```text
source_root/
  job.json
  frames.csv
  process.csv
  events.csv
  review_labels.csv
  images/
```

目录 contract：

- `source_root/job.json`、`source_root/frames.csv`、`source_root/process.csv`、`source_root/events.csv` 必需。
- `source_root/review_labels.csv` 可选。
- `source_root/images/` 可选；但 `frames.csv.image_path` 只要非空，就必须指向 `source_root` 下已存在的相对文件。
- `output_dir` 必须和 `source.root` 不同；当前 importer 会拒绝 `output_dir` 与 `source.root` 相同的 in-place 写入。

## 字段 Contract

通用语义：

- 所有 `timestamp_s` 都是秒。
- 数值字段必须是 finite numbers，不能是 `nan`、`inf` 或无法解析的文本。
- `image_path` 必须相对 `source_root`，不能是绝对路径，不能包含 `..`，也不能通过 symlink escape 跳出 `source_root`。
- `events.csv.object_id` 必须为空，或等于 `job.json.part_id` / `job.json.seam_id` 的具体值，例如 `part_alpha` 或 `seam_root`；不要填写字面量 `part_id` 或 `seam_id`。
- `review_status` 和 `reviewer` 保留在 `artifacts/source/review_labels.csv`，不会进入输出 package 的 `labels.csv`。

### `job.json`

| 字段 | 必需 | 含义 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `work_order_id` | 是 | 工单或作业 ID | `WO-1001` | 用于生成 package/task 标识。 |
| `station_id` | 是 | 工站 ID | `station_A` | 用于生成 package 标识。 |
| `robot_id` | 是 | 机器人设备 ID | `robot_17` | 写入 package devices。 |
| `welder_id` | 是 | 焊机或电源 ID | `welder_03` | 写入 package devices。 |
| `part_id` | 是 | 工件对象 ID | `part_alpha` | `events.csv.object_id` 可引用这个具体值。 |
| `seam_id` | 是 | 焊缝对象 ID | `seam_root` | `events.csv.object_id` 可引用这个具体值。 |
| `task_name` | 是 | 任务名称 | `Root pass weld` | 写入 package task name。 |
| `created_at` | 是 | 作业创建时间 | `2026-06-10T09:00:00Z` | 建议使用带时区的 ISO 8601 字符串。 |

### `frames.csv`

| 字段 | 必需 | 含义 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `timestamp_s` | 是 | 帧时间戳，单位秒 | `0.0` | 必须是 finite number。 |
| `phase` | 是 | 作业阶段 | `approach` | 例如 `approach`、`weld`、`cooldown`。 |
| `tcp_x` | 是 | TCP 位置 X | `0.10` | 必须是 finite number。 |
| `tcp_y` | 是 | TCP 位置 Y | `0.20` | 必须是 finite number。 |
| `tcp_z` | 是 | TCP 位置 Z | `0.30` | 必须是 finite number。 |
| `tcp_qx` | 是 | TCP 姿态四元数 X | `0.0` | 必须是 finite number。 |
| `tcp_qy` | 是 | TCP 姿态四元数 Y | `0.0` | 必须是 finite number。 |
| `tcp_qz` | 是 | TCP 姿态四元数 Z | `0.0` | 必须是 finite number。 |
| `tcp_qw` | 是 | TCP 姿态四元数 W | `1.0` | 必须是 finite number。 |
| `image_path` | 是 | 可选图片相对路径 | `images/front_0000.png` | 列必需，值可空；非空时必须是合法相对路径并指向已存在文件。 |

### `process.csv`

| 字段 | 必需 | 含义 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `timestamp_s` | 是 | 工艺参数时间戳，单位秒 | `0.1` | 必须是 finite number。 |
| `weld_current_a` | 是 | 焊接电流，单位 A | `121.5` | 写入 `weld_current` metric。 |
| `weld_voltage_v` | 是 | 焊接电压，单位 V | `23.2` | 写入 `weld_voltage` metric。 |
| `wire_feed_mpm` | 是 | 送丝速度，单位 m/min | `7.1` | 写入 `wire_feed` metric。 |
| `gas_flow_lpm` | 是 | 气体流量，单位 L/min | `15.0` | 写入 `gas_flow` metric。 |
| `travel_speed_mm_s` | 是 | 行走速度，单位 mm/s | `4.5` | 写入 `travel_speed` metric。 |
| `defect_probability` | 是 | 缺陷概率或风险评分 | `0.08` | 写入 `defect_probability` metric；数值越高表示越值得关注。若现场只有“质量分越高越好”的字段，需要先转换为风险语义再导出。 |

### `events.csv`

| 字段 | 必需 | 含义 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `timestamp_s` | 是 | 事件时间戳，单位秒 | `0.31` | 必须是 finite number，会关联到最近的 frame。 |
| `event_type` | 是 | 事件类型 | `arc_start` | 保留源系统事件语义。 |
| `severity` | 是 | 事件等级 | `info` | 为空时 importer 会写入 `info`。 |
| `message` | 是 | 事件消息 | `Arc stabilized` | 可为空字符串。 |
| `object_id` | 是 | 关联对象 ID | `seam_root` | 只能为空，或等于 `job.json.part_id` / `job.json.seam_id` 的具体值。 |

### `review_labels.csv`

| 字段 | 必需 | 含义 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `timestamp_s` | 是 | 复核标签时间戳，单位秒 | `0.19` | 必须是 finite number，会关联到最近的 frame。 |
| `label_type` | 是 | 标签类型 | `bead_quality` | 为空的行不会进入 `labels.csv`。 |
| `value` | 是 | 标签值 | `acceptable` | 写入 `labels.csv.value`。 |
| `confidence` | 是 | 标签置信度 | `0.9` | 必须是 finite number。 |
| `review_status` | 否 | 复核状态 | `reviewed` | 仅保留在 `artifacts/source/review_labels.csv`。 |
| `reviewer` | 否 | 复核人 | `qa_01` | 仅保留在 `artifacts/source/review_labels.csv`。 |

## Python 调用方式

```python
from pathlib import Path

from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter

result = run_import(
    WeldWorkcellPackageImporter(),
    ImportRequest(
        source_format="weld_workcell",
        source={"root": Path("path/to/source_root")},
        output_dir=Path("artifacts/stage5/weld_workcell_package"),
        options={"copy_images": True},
    ),
)
```

## 系统产出物

Import 成功后会立即创建 package tables 和 `artifacts/`：

- `physical_ai_manifest.json`
- `frames.csv`
- `events.csv`
- `labels.csv`
- `metrics.csv`
- `README.md`
- `artifacts/source/`
- `artifacts/images/`
- `artifacts/trajectories/tcp_path.csv`

后续命令会创建派生产物，包括 `derived/candidates.csv`、`derived/training_eval/` 和 `.rrd`：

```bash
python scripts/physical_ai_package.py validate artifacts/stage5/weld_workcell_package --json
python scripts/physical_ai_package.py summarize artifacts/stage5/weld_workcell_package --json
python scripts/physical_ai_package.py export-candidates artifacts/stage5/weld_workcell_package
python scripts/physical_ai_package.py export-training-draft artifacts/stage5/weld_workcell_package --split eval
python scripts/physical_ai_package.py convert-rerun artifacts/stage5/weld_workcell_package --output-rrd artifacts/stage5/weld_workcell_package.rrd
```

## 验收 Checklist

- 源目录包含 `job.json`、`frames.csv`、`process.csv`、`events.csv`。
- CSV header 符合字段 contract；`review_labels.csv` 若存在，也符合字段 contract。
- `frames.csv.image_path` 为空或是合法相对路径，并且非空路径指向已存在文件。
- Python import 成功，输出 Physical AI Package。
- `validate` 无 error。
- `summarize` 能读出 frame、event、label、metric count。
- `export-candidates` 成功生成 `derived/candidates.csv`。
- `export-training-draft --split eval` 成功生成 `derived/training_eval/`。
- `convert-rerun` 成功写出 Rerun `.rrd`。
- 记录所有缺失字段、无法提供字段和现场系统暂时无法导出的字段。

## 常见错误

- 缺文件：`source.root must contain process.csv` 这类错误表示必需文件未导出。
- 缺 job 字段：例如 `job.json missing required fields: robot_id`。
- 缺 CSV 列：例如 `process.csv missing required columns: weld_current_a`。
- malformed row：CSV 行列数不一致，常见于消息文本中未正确转义逗号。
- non-finite numeric：数值字段包含 `nan`、`inf` 或非数字文本。
- empty frames：`frames.csv` 只有 header，没有任何数据行。
- invalid image path：图片路径是绝对路径、包含 `..`、目标文件不存在，或不是 `source_root` 下的相对路径。
- symlink escape：`image_path` 通过符号链接跳出 `source_root`。
- unknown event object id：`events.csv.object_id` 不是空值，也不等于 `job.json.part_id` / `job.json.seam_id` 的具体值。
- output_dir same as source.root：`output_dir must not be the same as source.root`，请把输出 package 放到独立目录。

## 对接会议问题清单

- 数据源 ownership：哪些系统负责导出 job、frames、process、events、review labels。
- 时间戳来源和同步：机器人、焊机、相机、工艺数据、报警事件是否使用同一时间基准。
- 图片/视频导出路径：导出图片、抽帧图片或视频帧索引的路径规则和保留周期。
- 工艺参数采样频率：`process.csv` 相对 `frames.csv` 的频率、插值需求和丢点策略。
- 事件/报警字段：现场事件类型、等级、消息和关联对象如何映射到 `events.csv`。
- defect/risk score source：`defect_probability` 或风险评分来自规则、视觉、人工复核还是外部质检系统；若源系统只有质量分，需要确认转换规则。
- 脱敏和客户边界：工单、人员、设备、图片、日志中哪些字段需要脱敏，哪些数据不能离开现场。

## 当前边界

- `WeldWorkcellPackageImporter` 是业务 importer candidate，不是生产 connector。
- 当前只支持本地离线文件导入，不直接连接真实机器人、PLC、OPC UA、MES、HMI 或数据库。
- 当前不扩展 Physical AI Package schema；复核状态和复核人只保留在 source artifact。
- 当前不推断真实质量结论，不训练模型，也不自动生成正式训练集。
- Rerun 是可替换 adapter backend；主数据结构仍是 Physical AI Package。
- 在线/准在线真机数据接入、AI 控制器侧 Raw Zone / Clean Zone、接口待确认项和真机数据资产模块规划，请参考 `docs/stage6/README.md`、`docs/stage6/real_robot_data_asset_module.md` 和 `docs/stage6/real_data_field_mapping.md`。
