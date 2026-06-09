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

## PushT Full Acceptance 结果

- 命令：`PYTHONPATH=src python3 scripts/physical_ai_package.py import-lerobot --repo-id lerobot/pusht --episode-index 0 --output-dir artifacts/stage4/final_pusht_episode_0000 --profile pusht`
- 结果：未通过，阻塞于本地未安装 LeRobot 可选依赖。
- stderr：`Error: Install the lerobot optional dependency with \`pip install '.[lerobot]'\` to load real LeRobot datasets.`
- 因导入未完成，未生成 package，后续 validate/summarize/export-candidates/convert-rerun/`rerun rrd verify` 未运行。

## PushT Quick Smoke 结果

- 本轮未运行 quick smoke。
- 原因：full acceptance 的阻塞不是下载体积、网络或时间限制，而是本地缺少 `lerobot` 可选依赖；quick smoke 会在同一依赖检查处失败。
- quick smoke 只作为本地迭代和阻塞排查手段，不替代 PushT full acceptance。

## ALOHA Smoke 结果

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
