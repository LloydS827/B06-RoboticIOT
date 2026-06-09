# Stage 4.1 LeRobot 真实开放数据验证设计

## 1. 背景

Stage 4 已完成 LeRobot Open Dataset Workflow 的代码骨架：Physical AI Package 已支持 LeRobot normalized episode/frame 表示、lazy real loader、`import-lerobot` CLI、`pusht`/`aloha`/`fallback` profile、多相机 `image_refs_json` 和 Rerun 多相机引用回放。默认单元测试与 CLI help 已通过，且 LeRobot 依赖保持为可选安装，不破坏 Stage 3 默认开发路径。

但 Stage 4 仍缺少一项关键证据：真实 LeRobot 开放数据尚未在本机跑通。当前记录显示 PushT full acceptance 与 ALOHA smoke 均阻塞于本地未安装 LeRobot 可选依赖，因此 Stage 4 只能证明“真实数据导入能力骨架存在”，还不能证明“真实开放数据闭环可运行”。

Stage 4.1 的定位是补齐这条证据链。它不是新功能扩展阶段，而是一个真实数据验证与映射校准阶段。

## 2. 阶段目标

Stage 4.1 的核心问题是：

> 当前 LeRobot adapter 能否在独立项目环境中读取真实 LeRobot 开放数据，并完成 Physical AI Package 的导入、校验、汇总、候选导出、Rerun 转换和 `.rrd` 验证？

本阶段采用 `uv` 管理项目级 Python 环境。LeRobot 及其真实数据依赖安装在项目独立环境中，不污染系统 Python，也不改变默认开发安装路径。

## 3. 成功标准

Stage 4.1 的最低成功标准如下：

1. 建立项目独立 `uv` 环境，并确认 `.[dev,lerobot]` 可安装或记录明确阻塞原因。
2. 记录真实环境信息：Python 版本、`uv` 版本、LeRobot 版本、Rerun 版本、关键 import path、缓存目录、网络和磁盘限制。
3. PushT quick smoke 必须实际通过完整链路；如果遇到外部不可控阻塞，本阶段不能标记完成，只能形成阻塞记录。
4. ALOHA representative smoke 必须实际通过完整链路；如果遇到外部不可控阻塞，本阶段不能标记完成，只能形成阻塞记录。
5. 对通过导入的数据包执行共享检查命令：
   - `validate`
   - `summarize`
   - `export-candidates`
   - `convert-rerun`
   - `rerun rrd verify`
6. 如果真实字段与 fake fixture 测试存在差异，允许对 loader、profile、mapping 文档做小范围修补。
7. 补充 Viewer/Blueprint 人工检查记录，确认图像、多相机、metric、event、timeline 是否可读。
8. 更新 Stage 4 链路记录、LeRobot mapping 文档和 `details.md`，明确真实 smoke 结果、限制和后续建议。

PushT full acceptance 作为尝试项：如果网络、磁盘、下载体积和时间条件允许，则运行并记录完整结果；如果不允许，则记录原因，不阻塞 Stage 4.1 的最低完成标准。

外部不可控阻塞包括 Hugging Face 网络不可用、上游数据集不可访问、磁盘空间不足、平台暂不支持的二进制依赖等。此类问题需要记录命令、错误摘要、环境信息和下一步建议，但不能替代 PushT quick smoke 与 ALOHA representative smoke 的通过证据。

## 4. 非目标

Stage 4.1 不做以下事项：

- 不进入 Physical AI Package SDK wrapper。
- 不实现 external importer 的新边界。
- 不实现训练/评估导出格式。
- 不连接机器人真机。
- 不训练模型，不评估策略效果。
- 不重构 Stage 3/Stage 4 已有架构。
- 不承诺完整语义化所有 LeRobot 数据集。
- 不为每个 LeRobot repo 写专用 importer。
- 不把 LeRobot 变成默认依赖；默认测试路径仍应不依赖真实 LeRobot 安装和网络。

## 5. 环境设计

### 5.1 `uv` 项目环境

本阶段使用项目内独立虚拟环境，建议路径为仓库根目录 `.venv/`。环境由 `uv` 创建和维护：

```bash
uv venv
uv pip install -e ".[dev,lerobot]"
```

如仓库后续引入 `uv.lock`，应确保锁文件反映当前可运行的 Stage 4.1 环境。若 LeRobot 的依赖解析与当前 Python 版本、平台或 Rerun 依赖冲突，应优先记录冲突和最小复现命令，再判断是否需要收窄版本范围。

### 5.2 默认开发路径

默认开发路径仍保持：

```bash
python3 -m pip install -e ".[dev]"
PYTHONPATH=src python3 -m pytest -q
```

Stage 4.1 不应让默认测试依赖 LeRobot、Hugging Face 网络、下载缓存或真实数据集。

### 5.3 环境记录

需要记录以下信息：

- `uv --version`
- `.venv/bin/python --version`
- `.venv/bin/python -c "import lerobot; ..."` 的结果
- `.venv/bin/python -c "import rerun; ..."` 的结果
- LeRobotDataset 的实际 import path
- Hugging Face/LeRobot 缓存位置
- 真实数据下载大小或磁盘占用的可观察结果
- 失败时的完整错误摘要

## 6. 数据选择

### 6.1 PushT quick smoke

PushT quick smoke 是 Stage 4.1 的主线验收入口。它使用 `lerobot/pusht` 的 episode 0，并限制导入帧数：

```bash
uv run python scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/pusht \
  --episode-index 0 \
  --output-dir artifacts/stage4/pusht_quick_episode_0000 \
  --profile pusht \
  --max-frames 120
```

quick smoke 必须验证真实数据最小闭环：真实 loader、真实字段、Physical AI Package 写入、validator、candidate export、Rerun adapter 和 `.rrd verify`。

### 6.2 ALOHA representative smoke

ALOHA smoke 用于验证多相机与复杂操作数据的兼容性。第一版仍采用保守映射，不要求完整语义化双臂、夹爪、标定和任务质量：

```bash
uv run python scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/aloha_sim_transfer_cube_human \
  --episode-index 0 \
  --output-dir artifacts/stage4/aloha_smoke_episode_0000 \
  --profile aloha \
  --max-frames 60
```

如果真实数据集的可用 repo、版本或字段布局发生变化，可以选择等价的公开 ALOHA 数据集，但必须在记录文档中写明替换原因、repo id、episode index 和字段差异。

### 6.3 PushT full acceptance

PushT full acceptance 是增强验收项：

```bash
uv run python scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/pusht \
  --episode-index 0 \
  --output-dir artifacts/stage4/pusht_episode_0000 \
  --profile pusht
```

如果 full acceptance 受网络、缓存、磁盘、下载体积或时间限制影响，可以不作为 Stage 4.1 的阻塞项，但必须记录尝试结果。

## 7. 验证流程

每个成功导入的数据包都需要运行：

```bash
uv run python scripts/physical_ai_package.py validate PACKAGE --json
uv run python scripts/physical_ai_package.py summarize PACKAGE --json
uv run python scripts/physical_ai_package.py export-candidates PACKAGE
uv run python scripts/physical_ai_package.py convert-rerun PACKAGE --output-rrd OUTPUT.rrd
uv run rerun rrd verify OUTPUT.rrd
```

验证结果应记录到 `docs/research/06-lerobot开放数据样板链路记录.md`。记录不需要保存完整冗长日志，但必须包含命令、结果、关键输出摘要、失败原因和生成物路径。

## 8. 允许的代码修补范围

如果真实 LeRobot 数据暴露现有 loader/profile 与真实字段不一致，可以做小范围修补：

- `src/physical_ai_data/lerobot_loader.py`
  - 兼容当前 LeRobotDataset import path。
  - 兼容真实 row 字段名、episode/frame index、timestamp、task、state、action、image 或 video 解码结果。
  - 处理真实图像对象、数组、路径或视频帧形式。
- `src/physical_ai_data/lerobot_profiles.py`
  - 校准 `pusht` 或 `aloha` profile 的保守映射，不增加无证据语义。
- `src/physical_ai_data/lerobot_adapter.py`
  - 只修补真实数据写包所需的 bug，不扩展新的包 schema。
- `src/physical_ai_data/rerun_adapter.py`
  - 只修补多相机 `.rrd` 回放所需的读取问题。
- `tests/physical_ai_data/`
  - 为真实字段差异补充 fake fixture 单元测试，确保默认测试不访问网络。

不允许把本阶段变成大规模重构。任何改动都应能追溯到真实 smoke 暴露的问题。

## 9. 文档更新范围

Stage 4.1 完成后需要更新：

- `docs/research/06-lerobot开放数据样板链路记录.md`
  - 记录 uv 环境、真实 smoke 命令、结果、失败或通过证据。
- `docs/research/06-lerobot到physical-ai-package映射.md`
  - 根据真实字段校准 mapping 和明确不推断的内容。
- `docs/stage4/README.md`
  - 如命令、环境或 repo 选择发生变化，更新运行说明。
- `details.md`
  - 记录 Stage 4.1 完成事项、限制和下一步计划。

如默认安装、README 当前状态或项目入口发生变化，再同步更新 `README.md`。如果只是补充 Stage 4.1 结果，优先更新 details 和专题文档。

## 10. Viewer/Blueprint 人工检查

本阶段需要对生成的 `.rrd` 做轻量人工检查。检查目标不是设计复杂 UI，而是确认 Rerun Viewer 中的基本可读性：

- PushT `.rrd` 能打开。
- 时间线可拖动，图像随 frame 更新。
- metric 曲线或 scalar 记录可读。
- event/log 信息可读。
- ALOHA 多相机图像能以主相机和额外相机路径出现。
- 若保存 Blueprint 或截图，应记录路径；生成物仍不提交。

人工检查结果写入 Stage 4 链路记录。若 Viewer 无法启动或 GUI 不适合当前环境，也应记录具体原因，并至少保留 `rerun rrd verify` 的命令证据。

## 11. 风险与处理

| 风险 | 处理方式 |
| --- | --- |
| LeRobot 版本或 import path 变化 | 先记录版本与 import path，再做最小兼容修补。 |
| Hugging Face 网络不可用 | 记录错误；如有本地缓存可用，使用 `--root` 或缓存路径重试。 |
| 数据体积过大 | 优先 quick smoke；full acceptance 改为尝试项。 |
| ALOHA repo 不可访问或字段变化 | 选择等价公开 ALOHA repo，并记录替换原因。 |
| 视频或图像解码依赖缺失 | 记录缺失依赖；如属于 LeRobot 可选依赖，应纳入 uv 环境修正。 |
| Rerun Viewer GUI 不可用 | 保留 `.rrd verify` 结果，并记录人工检查未完成原因。 |
| 真实字段无法保守映射 | 生成明确 warning，不编造成功/失败、标定、双臂语义或任务质量。 |

如果 PushT quick smoke 或 ALOHA representative smoke 因上述风险未实际通过，Stage 4.1 应记录为阻塞或未完成，而不是有条件完成。只有 PushT full acceptance 可以因为资源限制保留为尝试项。

## 12. 完成定义

Stage 4.1 完成时，应具备以下证据：

- 项目可通过 `uv` 独立环境运行真实 LeRobot 导入命令。
- 默认测试仍通过，且不依赖 LeRobot 或网络。
- PushT quick smoke 通过完整共享检查链路。
- ALOHA representative smoke 通过完整共享检查链路。
- PushT full acceptance 有通过记录或明确尝试失败记录。
- 真实字段差异已通过小范围代码修补或文档记录处理。
- Stage 4 链路记录和 mapping 文档已更新。
- Viewer/Blueprint 人工检查有记录，或有明确环境限制说明。

完成后，下一阶段才进入 Stage 4.2：SDK wrapper / external importer 边界。
