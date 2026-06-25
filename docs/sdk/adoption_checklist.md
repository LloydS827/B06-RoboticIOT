# SDK adoption checklist

本文用于 Stage 10 SDK 采纳评审。目标是让外部研发或数据团队能从 repo root 跑通默认 synthetic demo，并知道何时可以替换为真实或脱敏 Clean Zone 输入。

## 1. 环境准备

- 从 repo root 执行：

```bash
python -m pip install -e ".[dev]"
```

- 后续命令都从 repo root 运行。
- 如果使用临时输出，优先写到 `/tmp/...` 或 `artifacts/stage8/...` 这类可再生成路径。
- 运行 SDK environment doctor，确认 editable install、import path 和 console entrypoint 指向当前仓库：

```bash
physical-ai-package doctor --json
```

如果 `doctor` 报错，或 `package_file` 指向旧 worktree，先修环境后再进入 demo 或 candidate real/de-identified onboarding。

## 2. Synthetic demo 路径

默认 runnable demo 仍是 Stage 8 H300 synthetic fixture：

```bash
python scripts/generate_stage8_h300_synthetic_demo.py \
  --output-root artifacts/stage8/h300_synthetic_demo \
  --frames 5
```

关键输入目录：

- Clean Zone：`artifacts/stage8/h300_synthetic_demo/clean/weld_workcell`
- Raw/source artifacts：`artifacts/stage8/h300_synthetic_demo/raw`

Python SDK 路径可参考 `examples/sdk_pipeline_stage8.py`。

## 3. Candidate real/de-identified Clean Zone replacement 路径

替换为真实或脱敏数据时，不直接改 SDK schema，也不先做 production connector。先阅读 [SDK real-data onboarding guide](real_data_onboarding.md)，再准备一个符合 `weld_workcell` contract 的 Clean Zone 目录：

- 必需文件：`job.json`、`frames.csv`、`process.csv`、`events.csv`
- 可选文件：`review_labels.csv`
- 图片路径：`frames.csv` 中的 `image_path` 能从 Clean Zone root 解析
- 输出目录：不要与 Clean Zone root 相同

最小替换方式不是直接跑 pipeline，而是先执行 readiness：

```bash
physical-ai-package assess-h300-readiness \
  --clean-root path/to/candidate/clean/weld_workcell \
  --raw-root path/to/candidate/raw \
  --json
```

如果 `overall_status=blocked`，先修 Clean Zone，再重新运行 readiness；不要继续 pipeline smoke。如果状态不是 `blocked`，再使用 `examples/sdk_real_data_onboarding.py` 或 `physical-ai-package run-weld-workcell` 做受控 smoke。

## 4. 最小验收命令

CLI smoke：

```bash
bash examples/cli_json_smoke.sh /tmp/b06_stage10_cli_json_smoke
```

SDK pipeline smoke：

```bash
python examples/sdk_pipeline_stage8.py --output-root /tmp/b06_stage10_sdk_pipeline --frames 5
```

已有 package 操作：

```bash
python examples/sdk_existing_package_ops.py --output-root /tmp/b06_stage10_existing_package_ops --frames 5
```

低层 importer contract：

```bash
python examples/sdk_low_level_importer.py --output-root /tmp/b06_stage10_low_level_importer --frames 5
```

## 5. 输出检查清单

一次 adoption run 至少确认：

- package manifest：`physical_ai_manifest.json` 存在，`validate(...).ok` 为 `True`。
- summary：`summary["frame_count"]` 与输入帧数一致，events/labels/metrics 数量符合预期。
- candidates：`derived/candidates.csv` 存在，或者明确设置 `export_candidates=False` 并接受 `PipelineResult.candidates_csv is None`。
- training draft：`derived/training_eval` 存在，或者明确设置 `training_split=None`。
- `.rrd`：如果需要 Rerun 回放，`output_rrd` 指向的文件存在；否则接受 `PipelineResult.rrd_path is None`。
- 输出索引：SDK 路径优先记录 `PipelineResult.to_dict()`，CLI 路径记录同等 JSON 字段。

## 6. 数据敏感性和不提交边界

- 不提交真实或脱敏 H300 原始样本、图片、工艺参数、客户工单号或可识别设备信息。
- 不把本地 `/tmp`、`artifacts/stage8/...` 运行产物作为人工修改成果提交。
- 文档中可以记录字段缺口、路径形态和验收结果，但不要贴真实敏感行级数据。
- 如果必须保留样例，先完成脱敏评审，并确认它属于可公开 fixture，而不是现场数据副本。

## 7. 何时回到 Stage 8 gap register

遇到以下情况，先回到 `docs/stage8/h300_synthetic_to_real_gap_register.md`，不要在 Stage 10 直接扩展平台范围：

- 真实或脱敏 H300 样本字段无法落入现有 Clean Zone contract。
- 图片、轨迹、工艺时序或事件语义缺失，导致 package 校验或评审解释不稳定。
- 需要 production connector、DB schema、Web platform 或 H300 field protocol 才能继续。
- 评审方要求的 evidence 超出当前 package、candidates、training draft 和 `.rrd` 输出。
