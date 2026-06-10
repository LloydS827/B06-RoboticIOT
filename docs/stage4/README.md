# Stage 4 LeRobot 开放数据样板链路

Stage 4 的目标是在不接入真机、不训练模型的前提下，把开源机器人操作数据接入 Physical AI Package：通过 LeRobot import adapter/CLI 导入 episode，生成可校验、可汇总、可导出候选样本、可转换为 Rerun `.rrd` 的数据包，并用 PushT 作为主验收样例、ALOHA 作为代表性兼容性 smoke。

## 安装

默认开发安装不包含 LeRobot，可继续保持 Stage 3 默认 workflow 可用：

```bash
python3 -m pip install -e ".[dev]"
```

需要运行真实 LeRobot 数据集导入时，使用本项目独立 `uv` 环境安装可选依赖；`uv.lock` 与 `tool.uv.override-dependencies` 已记录当前 LeRobot loader 与项目 Rerun baseline 的解析结果：

```bash
uv sync --extra dev --extra lerobot
```

## PushT Full Acceptance

PushT full acceptance 使用 `lerobot/pusht` 的一个完整 episode，验证从开源数据到 Physical AI Package，再到候选导出和 Rerun `.rrd` 的完整链路：

```bash
uv run python scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/pusht \
  --episode-index 0 \
  --output-dir artifacts/stage4/pusht_episode_0000 \
  --profile pusht
```

## PushT Quick Smoke

本地迭代或网络/下载时间受限时，可以先跑限制帧数的快速 smoke。该命令只验证小帧数链路，不替代 full acceptance：

```bash
uv run python scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/pusht \
  --episode-index 0 \
  --output-dir artifacts/stage4/pusht_quick_episode_0000 \
  --profile pusht \
  --max-frames 120
```

## ALOHA Representative Smoke

ALOHA smoke 用于验证多相机和复杂操作数据的代表性兼容性。第一版只要求形成可校验、可转换的轻量数据包，不要求完整语义化全部 ALOHA 字段：

```bash
uv run python scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/aloha_static_towel \
  --episode-index 0 \
  --output-dir artifacts/stage4/aloha_representative_episode_0000 \
  --profile aloha \
  --max-frames 60
```

`lerobot/aloha_sim_transfer_cube_human` 只暴露单个 `observation.images.top` 视频字段，不满足本 smoke 的多相机代表性要求；当前使用公开 ALOHA-family 数据集 `lerobot/aloha_static_towel`，其 metadata 暴露 `cam_high`、`cam_left_wrist`、`cam_low`、`cam_right_wrist` 四个相机。

如需固定主相机，可追加 `--camera CAMERA_NAME`。未指定时，数据包会保留 `image_refs_json` 中的多相机引用，并选择排序后的首个相机作为 `frames.csv` 的主 `image_ref`。

## 共享检查命令

以下命令以 PushT full acceptance 输出目录为例。若检查 quick smoke 或 ALOHA smoke，请替换 package 目录和 `.rrd` 输出路径。

```bash
uv run python scripts/physical_ai_package.py validate artifacts/stage4/pusht_episode_0000 --json
uv run python scripts/physical_ai_package.py summarize artifacts/stage4/pusht_episode_0000 --json
uv run python scripts/physical_ai_package.py export-candidates artifacts/stage4/pusht_episode_0000
uv run python scripts/physical_ai_package.py convert-rerun artifacts/stage4/pusht_episode_0000 --output-rrd artifacts/stage4/pusht_episode_0000.rrd
uv run rerun rrd verify artifacts/stage4/pusht_episode_0000.rrd
```

## 已知限制

- 本阶段不连接机器人硬件。
- 本阶段不训练模型，也不判断策略效果。
- 真实 LeRobot smoke 依赖网络、Hugging Face 数据集可用性、本地缓存和 LeRobot 版本。
- ALOHA smoke 是兼容性 smoke，不是完整语义映射；未在源数据中明确给出的机器人标定、相机外参、成功/失败标签和任务质量不会被推断。
- Rerun 仍作为 adapter backend 使用，Physical AI Package 是当前主数据包结构。
