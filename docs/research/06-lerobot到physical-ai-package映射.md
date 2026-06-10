# LeRobot 到 Physical AI Package 映射

本文记录 Stage 4 LeRobot import adapter 的字段映射口径。目标是把 LeRobot episode 保守转换为 Physical AI Package，优先保证可追溯、可校验、可回放和可继续筛选，不把源数据中没有明确给出的语义强行补齐。

## LeRobot Source Fields

当前 adapter 关注以下 LeRobot 来源信息：

| 来源字段 | 用途 |
| --- | --- |
| `repo_id` | 记录原始 LeRobot/Hugging Face dataset repo，例如 `lerobot/pusht`。 |
| `root` / 本地路径 | 记录本地 LeRobot 数据缓存或本地数据集位置。 |
| `episode_index` / `episode.index` / `episode` | 选择并记录 episode。 |
| `frame_index` / `frame.idx` / `index` | 记录源 frame index，写入 `frames.csv` 的 `source_frame_index`。 |
| `timestamp` / `timestamp_s` | 优先作为 `timestamp_s`；缺失时按 fps 与 frame index 生成时间戳。 |
| `observation.image*` 或 key 中包含 `image` 的字段 | 提取图像 artifact，并按相机名写入 `artifacts/images/<camera>/`。 |
| metadata `video_keys` + `get_video_file_path(...)` | 当 LeRobot 行数据未直接返回图像、但 metadata 暴露视频相机时，按相机解码视频帧到临时 PNG，再写入 `artifacts/images/<camera>/`。 |
| `observation.state` / `state` | 写入 `artifacts/source/frame_state_action.csv` 的 `state_json`，并生成 `state_norm` metric。 |
| `action` | 写入 `artifacts/source/frame_state_action.csv` 的 `action_json`，并生成 `action_norm` 与 `action_delta` metric。 |
| `task` 与 tasks metadata | 写入 task metadata，并作为任务上下文 label 的候选来源。 |
| `features` | 保存为 `artifacts/source/lerobot_features.json`。 |
| `stats` | 保存为 `artifacts/source/lerobot_stats.json`。 |
| episode metadata | 保存为 `artifacts/source/lerobot_episode_metadata.json`。 |
| task metadata | 保存为 `artifacts/source/lerobot_task_metadata.json`。 |

## 真实预检观察字段

Task 2 使用 `uv run python` 直接调用 `load_lerobot_episode`，只加载 episode 0 的少量 frame。观察结果如下：

| repo | profile | max frames | 实际 frames | fps | row/features 字段 | state/action 维度 | 图像相机 |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `lerobot/pusht` | `pusht` | 3 | 3 | 30.0 | `action`, `episode_index`, `frame_index`, `index`, `next.done`, `next.reward`, `next.success`, `observation.state`, `task_index`, `timestamp` | 2 / 2 | 无 |
| `lerobot/aloha_sim_transfer_cube_human` | `aloha` | 2 | 2 | 50.0 | `action`, `episode_index`, `frame_index`, `index`, `next.done`, `observation.images.top`, `observation.state`, `task_index`, `timestamp` | 14 / 14 | metadata 仅暴露 `top` 单相机视频，预检 frame 中无已解码图像引用 |
| `lerobot/aloha_static_towel` | `aloha` | 60 | 60 | 50.0 | `action`, `episode_index`, `frame_index`, `index`, `next.done`, `observation.effort`, `observation.images.cam_high`, `observation.images.cam_left_wrist`, `observation.images.cam_low`, `observation.images.cam_right_wrist`, `observation.state`, `task_index`, `timestamp` | 14 / 14 | `cam_high`, `cam_left_wrist`, `cam_low`, `cam_right_wrist` |

与 fake fixture 的差异：

- `lerobot/pusht` 在 LeRobot 0.4.4 下被识别为 2.1 格式，`LeRobotDataset` 默认以 v3.0 codebase 打开时会抛 `BackwardCompatibilityError`；loader 仅在该明确旧格式错误下 fallback 到 Hugging Face `datasets.load_dataset(..., split="train", streaming=True)` 读取 parquet 行。
- `lerobot/aloha_sim_transfer_cube_human` 可通过 `LeRobotDataset` 打开 metadata/parquet，但 `meta.tasks` 等 metadata 可能是 pandas DataFrame，需要先归一化为普通 `list[dict]`/`dict` 后保存。
- `lerobot/aloha_sim_transfer_cube_human` 的 `features`/`stats` 暴露 `observation.images.top`，但这是单相机视频字段，不满足 ALOHA representative smoke 的多相机要求。
- `lerobot/aloha_static_towel` 的 `hf_dataset` 行同样不直接返回图像字段，但 metadata 暴露 4 个 video camera keys；loader 仅按 metadata 明确给出的 `video_keys` 和视频文件路径解码图像帧，不推断额外相机或伪造 refs。
- 直接走 `LeRobotDataset.__getitem__` 仍可能进入 TorchCodec 视频解码路径；当前 loader 使用 PyAV 解码 metadata 视频文件，绕开本机 TorchCodec/FFmpeg 动态库问题。
- 真实行使用 `task_index`，预检首行没有直接 `task` 字符串，因此 `task_name` 为空；adapter 仍只在源数据明确给出 `task` 时写任务名，不从 `task_index` 猜测语义。

## Manifest 映射

Physical AI Package manifest 采用 `open_robot_manipulation` 场景类型，并在 `source_dataset` 中保留 LeRobot 血缘：

| Physical AI Package 字段 | LeRobot 来源或生成规则 |
| --- | --- |
| `schema_version` | 使用当前 Physical AI Package schema version。 |
| `package_id` | 由 `repo_id`、`episode_index` 和 profile 生成稳定 ID。 |
| `scenario_type` | 固定为 `open_robot_manipulation`。 |
| `task.task_id` | `episode_<episode_index>`。 |
| `task.name` | 优先使用 LeRobot `task`；缺失时使用 `LeRobot episode`。 |
| `devices` | 固定包含 `robot_arm`；每个识别出的 camera 生成一个 `camera_<camera>` device。 |
| `objects` | 由 profile 给出保守对象集合。 |
| `coordinate_frames` | 当前写入 `station` 与 `robot_base` 的最小框架，不推断真实标定。 |
| `timelines` | 写入 `sim_time` 与 `episode_time`，当前 frames 默认使用 `sim_time`。 |
| `source_dataset.format` | 固定为 `lerobot`。 |
| `source_dataset.repo_id` | LeRobot `repo_id`。 |
| `source_dataset.episode_index` | 导入的 episode index。 |
| `source_dataset.profile` | 实际使用的 profile：`pusht`、`aloha` 或 `fallback`。 |
| `source_dataset.fps` | LeRobot dataset fps 或 loader 可取得的 fps。 |
| `source_dataset.frame_count` | 实际写入的数据包 frame 数。 |
| `source_dataset.*_ref` | 指向 `artifacts/source/` 下保存的 LeRobot 原始 metadata。 |
| `source_dataset.converted_at` | 转换时间。 |

## Frames / Events / Labels / Metrics 映射

`frames.csv` 每行对应一个导入后的 LeRobot frame：

- `frame_id` 使用输出顺序生成，如 `frame_0000`。
- `timestamp_s` 使用 LeRobot timestamp；缺失时按 `frame_index / fps` 生成。
- `timeline` 当前固定为 `sim_time`。
- `phase` 来自 profile，PushT 为 `pushing`，ALOHA 为 `manipulation`，fallback 为 `episode`。
- `coordinate_frame_id` 当前固定为 `robot_base`，不推断真实世界坐标。
- `robot_state_ref` 指向 `artifacts/source/frame_state_action.csv`。
- `image_ref` 是主相机图像引用；多相机全集写入扩展列 `image_refs_json`。
- `source_frame_index` 保留 LeRobot 源 frame index。

`events.csv` 当前生成最小事件：

- `episode_start`
- `episode_end`
- fallback profile 额外生成 `profile_fallback` warning

`labels.csv` 当前生成一个 `task_context` label，目标为首帧，用于记录任务上下文。它不是成功/失败标签，也不是人工标注结果。

`metrics.csv` 当前生成：

- `action_norm`：action 向量 L2 norm。
- `state_norm`：state 向量 L2 norm。
- `action_delta`：相邻 action 的 L2 delta。
- `image_available`：当前 frame 是否有图像。

## Image / State / Action Artifacts

图像按相机拆分保存：

```text
artifacts/images/<camera>/frame_0000.png
```

`frames.csv` 的 `image_ref` 指向主相机图像；`image_refs_json` 保存同一 frame 的全部相机引用，例如：

```json
{"front": "artifacts/images/front/frame_0000.png", "side": "artifacts/images/side/frame_0000.png"}
```

state/action 不展开为固定列，而是写入：

```text
artifacts/source/frame_state_action.csv
```

该表包含 `frame_id`、`timestamp_s`、`source_frame_index`、`state_json`、`action_json`。这样可以避免在第一版中假设不同 LeRobot 数据集的状态维度、动作维度和关节语义完全一致。

## Profile 映射

### PushT Profile

PushT profile 用于 `lerobot/pusht` 主验收：

- `phase` 写为 `pushing`。
- manifest `objects` 写入 `block` 与 `target`。
- 保留 2D state/action 到 `frame_state_action.csv`，不把 state 维度强行解释为世界坐标。
- 使用 `action_delta`、`action_norm`、`state_norm` 支撑候选样本导出和复盘筛选。

### ALOHA Profile

ALOHA profile 用于代表性 smoke：

- `phase` 写为 `manipulation`。
- manifest `objects` 使用保守的 `task_object`。
- 多相机图像通过 `image_refs_json` 保留，Rerun adapter 可读取额外相机引用；Task 4 使用 `lerobot/aloha_static_towel` 观察到 `cam_high`、`cam_left_wrist`、`cam_low`、`cam_right_wrist`。
- state/action 保持数组形式，不在第一版中推断双臂关节名、夹爪状态或相机标定。

### Fallback Profile

fallback profile 用于未知 LeRobot repo：

- `phase` 写为 `episode`。
- manifest `objects` 使用保守的 `task_object`。
- `events.csv` 生成 `profile_fallback` warning。
- 只做通用 image/state/action/timestamp/metadata 映射，不阻止生成最小 Physical AI Package。

## 明确不推断的字段

以下字段如果 LeRobot 源数据没有明确给出，Stage 4 adapter 不会推断：

- episode 成功/失败、任务完成度或策略质量。
- 人工标签、缺陷标签、评估标签和训练划分。
- 机器人型号、关节名称、运动学链、TCP 位姿和真实坐标系。
- 相机内参、外参、标定关系和跨相机几何约束。
- 物体真实姿态、目标位姿、碰撞状态和接触状态。
- ALOHA 双臂/夹爪的完整语义字段。
- LeRobot 数据集中没有暴露的隐藏 metadata。

这些字段后续可以由 profile 扩展、人工标注、业务规则或更明确的数据源补充，但不应在通用 import adapter 中静默猜测。
