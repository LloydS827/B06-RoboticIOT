# LeRobot 开放数据样板链路记录

## Stage Goal

Stage 4 的目标是把 Physical AI Package 从 simulation-first 样例推进到开源机器人操作数据：使用 LeRobot episode 作为输入，生成可校验、可汇总、可导出候选样本、可转换为 Rerun `.rrd` 的 Physical AI Package。PushT 作为 full acceptance 样例，ALOHA 作为代表性多相机兼容性 smoke。

## 已实现能力

- 新增 LeRobot normalized episode/frame 表示，用于把真实 LeRobot loader 和小型单元测试 fixture 解耦。
- 新增 LeRobot import adapter，可将 episode 写入 Physical AI Package，并保留 feature schema、stats、episode metadata、task metadata 和 state/action artifact。
- 新增 `open_robot_manipulation` 场景类型，用于承接开放机器人操作数据。
- 新增 `pusht`、`aloha`、`fallback` profile，分别覆盖 PushT 主验收、ALOHA 代表性 smoke 和未知 LeRobot repo 的保守映射。
- 新增 lazy LeRobot loader，只有执行真实 `import-lerobot` 时才导入 LeRobot。
- 新增 CLI 子命令 `import-lerobot`，支持 `--repo-id`、`--episode-index`、`--output-dir`、`--root`、`--profile`、`--max-frames`、`--camera`。
- Rerun adapter 已支持读取 `image_refs_json` 中的额外相机引用，用于多相机 LeRobot 数据包回放。
- candidate export 已扩展 LeRobot 相关候选关键字，例如 `action_delta`、`timestamp_gap` 和 `image_missing`；当前 adapter 直接生成 `action_norm`、`state_norm`、`action_delta` 和 `image_available` 等基础 metric。

## 单元测试与基础 CLI 验证结果

- `PYTHONPATH=src python3 -m pytest -q`：`92 passed`。
- `PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot --help`：通过，帮助输出包含 `--repo-id`、`--episode-index`、`--output-dir`、`--profile`、`--max-frames` 和 `--camera`。
- 默认测试不需要安装 LeRobot，不访问网络、缓存或真实数据集。

## Stage 4.1 uv 环境

- 状态：Task 1 环境基线已建立；本任务未运行真实 LeRobot 数据 import，PushT quick/full 和 ALOHA smoke 仍待后续任务执行。
- 工作区检查：`git status --short` 初始输出为空，未发现需要保留的既有改动。
- `uv` 可用性：
  - `command -v uv`：`/Users/lloyd/.local/bin/uv`
  - `uv --version`：`uv 0.11.17 (a33a629d6 2026-05-28 aarch64-apple-darwin)`
- 初始解析失败核心原因：项目默认依赖 `rerun-sdk[dataplatform]>=0.33.0`，而当前可解析的 LeRobot 版本要求较旧的 `rerun-sdk`：
  - `lerobot>=0.3.0,<0.4.0` 依赖 `rerun-sdk>=0.21.0,<0.23.0`
  - `lerobot>=0.4.0` 依赖 `rerun-sdk>=0.24.0,<0.27.0`
  - 因此 `b06-physical-ai-data-layer[lerobot]` 与项目已有 `rerun-sdk[dataplatform]>=0.33.0` 约束不可同时满足。
- 解决方式：在 `pyproject.toml` 新增 `tool.uv.override-dependencies = ["rerun-sdk[dataplatform]>=0.33.0"]`，让 LeRobot dataset loader 与项目 Rerun 0.33 baseline 在独立 `uv` 环境中共存。
  - 该 override 不降低项目 Rerun baseline。
  - 该 override 不把 LeRobot 变成默认依赖；LeRobot 仍只在 `lerobot` extra 中安装。
  - 未收窄 `requires-python`。
- 环境建立：
  - `uv lock`：通过，`Resolved 124 packages in 479ms`，生成 `uv.lock`。
  - `uv sync --extra dev --extra lerobot`：通过，`Installed 102 packages`。
- 运行版本：
  - `uv run python --version`：`Python 3.13.5`
  - `lerobot==0.4.4`
  - `rerun-sdk==0.33.0`
  - `datasets==4.8.5`
  - `huggingface_hub==0.35.3`
- `LeRobotDataset` import path 探测：
  - 可用：`lerobot.datasets.lerobot_dataset -> <class 'lerobot.datasets.lerobot_dataset.LeRobotDataset'>`
  - 不可用：`lerobot.common.datasets.lerobot_dataset`，`ModuleNotFoundError: No module named 'lerobot.common'`
- 环境变量与真实解析 cache 路径：
  - `HF_HOME=`、`HF_HUB_CACHE=`、`HF_DATASETS_CACHE=`、`LEROBOT_HOME=`、`LEROBOT_DATA_HOME=` 均为空。
  - `huggingface_hub.HF_HOME=/Users/lloyd/.cache/huggingface`
  - `huggingface_hub.HF_HUB_CACHE=/Users/lloyd/.cache/huggingface/hub`
  - `datasets.HF_DATASETS_CACHE=/Users/lloyd/.cache/huggingface/datasets`
  - `CACHE_PATH /Users/lloyd/.cache/huggingface exists=True`
  - `CACHE_PATH /Users/lloyd/.cache/huggingface/hub exists=True`
  - `CACHE_PATH /Users/lloyd/.cache/huggingface/datasets exists=False`
  - `CACHE_PATH /Users/lloyd/.cache/lerobot exists=False`
- Hugging Face dataset metadata 网络探测：
  - `HF_DATASET_OK lerobot/pusht sha=7628202a2180972f291ba1bc6723834921e72c19 files=8`
  - `HF_DATASET_OK lerobot/aloha_sim_transfer_cube_human sha=6a43d500f101255823a9d2b9dc244eeb01a2cd31 files=10`
- `uv` 环境回归测试：`uv run python -m pytest -q` 返回 `92 passed in 11.90s`。
- 默认非 LeRobot workflow 验证：
  - `python3 --version`：`Python 3.9.6`
  - `python3 -m pip --version`：失败，`/Library/Developer/CommandLineTools/usr/bin/python3: No module named pip`
  - `python3 -m pip install -e ".[dev]"`：失败，`/Library/Developer/CommandLineTools/usr/bin/python3: No module named pip`
  - `PYTHONPATH=src python3 -m pytest -q`：失败，`/Library/Developer/CommandLineTools/usr/bin/python3: No module named pytest`
  - 最接近的非 LeRobot 检查：用 `/tmp/stage4_1_default_dev_venv` 临时环境只安装 `.[dev]`，并将该 venv 的 `bin` 放到 `PATH` 前面后运行 `PYTHONPATH=src /tmp/stage4_1_default_dev_venv/bin/python -m pytest -q`，返回 `92 passed in 5.39s`。
  - 临时默认 dev 环境检查：`lerobot_installed=False`。
  - 判断：默认安装路径不需要 LeRobot；本轮未把默认依赖改成包含 LeRobot。
- sync 后 cache/环境占用与磁盘状态：
  - `du -sh /Users/lloyd/.cache/huggingface`：`1.0G`
  - `du -sh /Users/lloyd/.cache/huggingface/hub`：`1.0G`
  - `/Users/lloyd/.cache/huggingface/datasets`：不存在。
  - `/Users/lloyd/.cache/lerobot`：不存在。
  - `du -sh .venv`：`1.6G`
  - `df -h .`：`/dev/disk3s5 460Gi 171Gi 251Gi 41% /System/Volumes/Data`
- 本地生成状态：`.venv/`、下载数据、cache、`artifacts/`、`.rrd` 和 `*.egg-info/` 均为本地生成状态，不提交；本轮显式补充 `.venv/`、`*.egg-info/` 到 `.gitignore`。
- 下方 PushT/ALOHA 结果为 Stage 4.1 环境建立前的历史记录；本节已解除 LeRobot 可选依赖安装阻塞，但本任务不运行真实数据 import，因此真实 smoke 状态仍待后续任务更新。

## Task 2 真实 Loader Preflight

- 命令：`uv run python - <<'PY' ... load_lerobot_episode(...) ... PY`，分别加载：
  - `repo_id="lerobot/pusht"`，`episode_index=0`，`profile="pusht"`，`max_frames=3`
  - `repo_id="lerobot/aloha_sim_transfer_cube_human"`，`episode_index=0`，`profile="aloha"`，`max_frames=2`
- 初始结果：PushT 在 `LeRobotDataset` 初始化阶段失败，错误为：

```text
lerobot.datasets.backward_compatibility.BackwardCompatibilityError:
The dataset you requested (lerobot/pusht) is in 2.1 format.

We introduced a new format since v3.0 which is not backward compatible with v2.1.
```

- 修复：`lerobot_loader.py` 仅在捕获 LeRobot `BackwardCompatibilityError` 时 fallback 到 `datasets.load_dataset(repo_id, split="train", streaming=True)` 读取旧格式 parquet 行；保留原有 `LeRobotDataset` 当前/legacy import path 和 constructor fallback。
- 第二次预检中 ALOHA 能读取 frame，但在 task metadata 归一化处失败：

```text
ValueError: The truth value of a DataFrame is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
```

- 修复：`lerobot_loader.py` 的 `_normalize` 支持 DataFrame-like `to_dict(orient="records")`，把 `meta.tasks` 等 metadata 转为普通 Python 数据再保存，不推断任务语义。
- 修复后的最终 preflight 输出摘要：

| repo | episode | max frames | frame count | fps | features keys | stats keys | camera names | state/action dims |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `lerobot/pusht` | 0 | 3 | 3 | 30.0 | `action`, `episode_index`, `frame_index`, `index`, `next.done`, `next.reward`, `next.success`, `observation.state`, `task_index`, `timestamp` | 无 | 无 | 2 / 2 |
| `lerobot/aloha_sim_transfer_cube_human` | 0 | 2 | 2 | 50.0 | `action`, `episode_index`, `frame_index`, `index`, `next.done`, `observation.images.top`, `observation.state`, `task_index`, `timestamp` | `action`, `episode_index`, `frame_index`, `index`, `next.done`, `observation.images.top`, `observation.state`, `task_index`, `timestamp` | 预检 frame 未返回已解码图像引用 | 14 / 14 |

- 图像限制：ALOHA metadata 暴露 `observation.images.top`，但当前 loader preflight 通过 `hf_dataset` 行读取到的是非图像核心字段；直接调用 `LeRobotDataset.__getitem__` 会进入 TorchCodec 视频解码路径，并在本机失败：

```text
RuntimeError: Could not load libtorchcodec.
Likely causes:
1. FFmpeg is not properly installed in your environment.
2. The PyTorch version (2.10.0) is not compatible with this version of TorchCodec.
```

- 本任务不修复 TorchCodec/FFmpeg 环境问题，也不伪造图像相机；记录为后续真实视频帧 smoke 的环境关注项。
- 测试结果：
  - 新增旧格式 fallback fake fixture：先失败于 `FakeBackwardCompatibilityError: dataset is in 2.1 format`，修复后通过。
  - 新增 DataFrame-like task metadata fake fixture：先失败于 `ValueError: truth value is ambiguous`，修复后通过。
  - `uv run python -m pytest tests/physical_ai_data/test_lerobot_loader.py -q`：`9 passed in 0.10s`
  - `uv run python -m pytest tests/physical_ai_data/test_lerobot_loader.py tests/physical_ai_data/test_lerobot_adapter.py -q`：`18 passed in 0.12s`
  - `uv run python -m pytest -q`：`94 passed in 2.92s`

## 历史记录：PushT Full Acceptance 结果

- 命令：`PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot --repo-id lerobot/pusht --episode-index 0 --output-dir artifacts/stage4/final_pusht_episode_0000 --profile pusht`
- 结果：未通过，阻塞于本地未安装 LeRobot 可选依赖。
- stderr：`Error: Install the lerobot optional dependency with \`pip install '.[lerobot]'\` to load real LeRobot datasets.`
- 因导入未完成，未生成 package，后续 validate/summarize/export-candidates/convert-rerun/`rerun rrd verify` 未运行。

## 历史记录：PushT Quick Smoke 结果

- 本轮未运行 quick smoke。
- 原因：full acceptance 的阻塞不是下载体积、网络或时间限制，而是本地缺少 `lerobot` 可选依赖；quick smoke 会在同一依赖检查处失败。
- quick smoke 只作为本地迭代和阻塞排查手段，不替代 PushT full acceptance。

## 历史记录：ALOHA Smoke 结果

- 命令：`PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot --repo-id lerobot/aloha_sim_transfer_cube_human --episode-index 0 --output-dir artifacts/stage4/final_aloha_smoke_episode_0000 --profile aloha --max-frames 60`
- 结果：未通过，阻塞于本地未安装 LeRobot 可选依赖。
- stderr：`Error: Install the lerobot optional dependency with \`pip install '.[lerobot]'\` to load real LeRobot datasets.`
- 因导入未完成，未生成 package，后续 validate/convert-rerun/`rerun rrd verify` 未运行。

## 风险限制

- 真实 LeRobot smoke 依赖网络、Hugging Face 数据集可用性、本地缓存、LeRobot 版本和磁盘空间。
- LeRobot API 和数据集布局可能随版本变化，当前 loader 使用 lazy import 和当前/历史 import path fallback 降低风险。
- Stage 4 不连接真实机器人硬件，不训练模型，不判断策略效果。
- 通用 adapter 不推断源数据中没有明确给出的成功/失败、标定、机器人运动学、相机几何和任务质量。
- ALOHA 多相机与复杂状态字段当前按保守方式保留，后续如需完整语义化，需要单独扩展 profile。

## 下一步

1. 由主线程运行 PushT full acceptance，并把真实命令输出补入本文档。
2. 如果 full acceptance 受阻，先运行 PushT quick smoke，记录阻塞原因和最小可用链路结果。
3. 运行 ALOHA representative smoke，确认多相机 artifact 与 Rerun adapter 输出。
4. 补充 Viewer/Blueprint 人工检查，记录多相机显示、时间线、事件和指标观察结果。
5. 基于真实 smoke 结果校准 mapping 文档，明确是否需要新增 profile 字段或 loader 兼容逻辑。
