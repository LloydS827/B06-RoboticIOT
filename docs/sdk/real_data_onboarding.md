# SDK real-data onboarding guide

## 定位

本文是 Stage 11.1 的 candidate real/de-identified Clean Zone onboarding 模板，面向已经拿到本地候选 H300 Clean/Raw roots 的工程师。它帮助你完成环境检查、readiness、pipeline smoke 和输出索引整理。

这个流程只代表候选真实/脱敏 Clean Zone 模板：仓库内默认可运行样本仍是 Stage 8 synthetic fixture，不代表仓库已有真实 H300 样本，也不代表真实数据试点完成。

## 1. 环境检查

先从 repo root 确认当前 Python import path、console entrypoint 和可选依赖状态：

```bash
physical-ai-package doctor --json
```

重点查看：

- `ok`：为 `true` 表示 SDK 环境没有阻断错误；为 `false` 时先修环境。
- `package_file`：应指向当前 worktree 或当前 repo 的 `src/physical_ai_data/__init__.py`，不要指向旧 editable install。
- `console_entrypoint`：应能解析到当前环境中的 `physical-ai-package`。
- `warnings`：`rerun`、`lerobot` 这类可选依赖缺失只影响对应能力，不代表 Clean Zone readiness 不能运行。

如果 `package_file` 指向旧 worktree，重新执行：

```bash
python -m pip install -e ".[dev]"
physical-ai-package doctor --json
```

## 2. 输入准备

候选 Clean Zone 根目录必须是 `weld_workcell` contract：

```text
path/to/candidate/clean/weld_workcell/
  job.json
  frames.csv
  process.csv
  events.csv
  review_labels.csv        # optional
```

可选 Raw root 用于 readiness 的 evidence/gap review：

```text
path/to/candidate/raw/
  manifest.raw.json        # optional but recommended
  ...
```

准备约束：

- `frames.csv` 中非空 `image_path` 必须是相对路径，并且能从 Clean Zone root 解析到存在文件。
- pipeline 输出目录不能与 Clean Zone root 相同。
- 真实或脱敏 H300 原始样本、图片、点云、工单号、内部路径和商业敏感字段不要提交仓库。
- 若脱敏边界未确认，候选数据默认放在受控目录，只在本地运行 onboarding。

## 3. Readiness

推荐先通过顶层 SDK API 检查：

```python
from physical_ai_data import assess_h300_sample_readiness

report = assess_h300_sample_readiness(
    "path/to/candidate/clean/weld_workcell",
    raw_root="path/to/candidate/raw",
)
print(report.overall_status)
print(report.to_dict())
```

也可以用 CLI 生成 JSON report：

```bash
physical-ai-package assess-h300-readiness \
  --clean-root path/to/candidate/clean/weld_workcell \
  --raw-root path/to/candidate/raw \
  --json
```

状态解释：

- `blocked`：先修 Clean Zone contract 或关键输入问题，不运行 pipeline smoke。
- `review_required`：可以进入受控 smoke，但需要人工复核 Raw evidence、脱敏权限或 Stage 8 gap register 状态。
- `ready_for_pipeline_smoke`：可以运行最小 pipeline smoke，并继续人工检查输出。

## 4. Pipeline smoke

如果 readiness 不是 `blocked`，可以运行 Stage 11.1 onboarding example：

```bash
python examples/sdk_real_data_onboarding.py \
  --clean-root path/to/candidate/clean/weld_workcell \
  --raw-root path/to/candidate/raw \
  --output-root /tmp/b06_h300_candidate_onboarding \
  --training-split eval \
  --output-rrd /tmp/b06_h300_candidate_onboarding/package.rrd
```

该脚本会先执行 `assess_h300_sample_readiness(...)`。若状态为 `blocked`，脚本输出 readiness JSON 并返回 exit 2，不写 package。若 pipeline 失败，脚本输出错误 JSON 并返回 exit 1。

也可以直接用 CLI pipeline smoke：

```bash
physical-ai-package run-weld-workcell \
  --clean-root path/to/candidate/clean/weld_workcell \
  --output-dir /tmp/b06_h300_candidate_onboarding/package \
  --training-split eval \
  --output-rrd /tmp/b06_h300_candidate_onboarding/package.rrd
```

## 5. 输出索引

Stage 11.1 推荐使用 `PipelineResult.to_dict()` 或 CLI JSON 的同一结构记录输出索引：

```python
from physical_ai_data.pipelines import run_weld_workcell_pipeline

result = run_weld_workcell_pipeline(
    clean_root="path/to/candidate/clean/weld_workcell",
    output_dir="/tmp/b06_h300_candidate_onboarding/package",
    training_split="eval",
    output_rrd="/tmp/b06_h300_candidate_onboarding/package.rrd",
)
payload = result.to_dict()
```

至少检查这些字段：

- `package_root`：生成的 Physical AI Package 根目录。
- `validation.ok`、`validation.errors`、`validation.warnings`：package 校验结果。
- `summary`：帧数、事件、标签、指标和 artifact 引用概要。
- `candidates_csv`：候选样本索引，通常为 `package/derived/candidates.csv`。
- `training_draft_dir`：training/evaluation draft 目录，通常为 `package/derived/training_eval`。
- `rrd_path`：Rerun `.rrd` 文件路径；仅代表开发期回放 artifact。

## 6. 失败分流

按失败来源分流处理：

- environment：`doctor` 报错或 import path 指向旧 worktree 时，先修 editable install、Python 环境或 PATH。
- Clean Zone contract：缺少 `job.json`、`frames.csv`、`process.csv`、`events.csv`，CSV header 不满足 contract，或图片路径不可解析时，先修 Clean Zone。
- Raw evidence：Raw root 或 `manifest.raw.json` 缺失时，记录为 review/gap 状态，不把它伪装成已完成现场接入。
- de-identification/permission：脱敏、访问、提交边界未确认时，不提交候选样本，不进入 downstream 训练或评审扩散。
- Stage 8 gap register：字段、工艺、轨迹、质量语义或 evidence 超出现有 contract 时，回到 `docs/stage8/h300_synthetic_to_real_gap_register.md` 拆分和关闭缺口。

## 边界

Stage 11.1 不实现 production connector、TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连、DB ingestion、长期 DB schema、demo UI、H300 现场协议、A02 converter 或 Physical AI Package schema changes。

Stage 12 first de-identified H300 sample replacement pilot 只有在至少一条脱敏 H300 最小作业窗口样本完成访问边界、提交边界和受控目录确认后才启动。
