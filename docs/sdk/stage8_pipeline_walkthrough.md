# Stage 8 pipeline walkthrough

这是 notebook-style Markdown walkthrough，不要求 Jupyter，也不引入新依赖。所有命令默认从 repo root 执行。

## Step 1: install

```bash
python -m pip install -e ".[dev]"
```

确认后续 Python 和 CLI 使用的是同一个环境。

## Step 2: generate Stage 8 fixture

```bash
python scripts/generate_stage8_h300_synthetic_demo.py \
  --output-root artifacts/stage8/h300_synthetic_demo \
  --frames 5
```

生成后关注两个目录：

- `artifacts/stage8/h300_synthetic_demo/raw`
- `artifacts/stage8/h300_synthetic_demo/clean/weld_workcell`

Stage 8 fixture 是 synthetic demo/readiness 输入，不代表真实 H300 field protocol。

## Step 3: run SDK pipeline

可以直接运行示例：

```bash
python examples/sdk_pipeline_stage8.py \
  --output-root /tmp/b06_stage8_pipeline_walkthrough \
  --frames 5
```

也可以在自己的 Python 脚本中使用同一 helper：

```python
from pathlib import Path

from physical_ai_data.pipelines import run_weld_workcell_pipeline
from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo

output_root = Path("/tmp/b06_stage8_pipeline_walkthrough")
fixture = generate_stage8_h300_synthetic_demo(output_root / "fixture", frame_count=5)

result = run_weld_workcell_pipeline(
    clean_root=fixture.clean_root,
    output_dir=output_root / "package",
    training_split="eval",
    output_rrd=output_root / "package.rrd",
)

print(result.validation.ok)
print(result.summary)
print(result.package_root)
print(result.candidates_csv)
print(result.training_draft_dir)
print(result.rrd_path)
```

`generate_stage8_h300_synthetic_demo` 是 demo helper，不是顶层 `physical_ai_data` API；正式业务入口优先看顶层 SDK 函数和 `run_weld_workcell_pipeline`。

## Step 4: inspect summary and output paths

一次成功运行应看到：

- `result.validation.ok` 为 `True`。
- `result.package_root` 指向输出 package。
- `result.summary` 包含 frame/event/label/metric 等计数。
- `result.candidates_csv` 指向 `derived/candidates.csv`，除非传入 `export_candidates=False`。
- `result.training_draft_dir` 指向 training/evaluation draft 目录，除非传入 `training_split=None`。
- `result.rrd_path` 指向 `.rrd` 文件；只有显式传 `output_rrd` 时才会生成。

需要逐项查看时，可运行：

```bash
physical-ai-package validate /tmp/b06_stage8_pipeline_walkthrough/package --json
physical-ai-package summarize /tmp/b06_stage8_pipeline_walkthrough/package --json
```

## Step 5: run CLI JSON smoke

CLI smoke 用于确认命令行入口仍能调用同一 SDK pipeline：

```bash
examples/cli_json_smoke.sh /tmp/b06_stage10_cli_json_smoke
```

该脚本会生成 Stage 8 synthetic fixture，运行 `physical-ai-package run-weld-workcell --json`，并检查 validation 和 frame count。

## Step 6: read gap register before replacement

在替换为真实或脱敏 H300 Clean Zone 前，先读：

- `docs/stage8/h300_synthetic_to_real_gap_register.md`
- `docs/sdk/adoption_checklist.md`
- `docs/sdk/demo_ui_evaluation.md`

如果替换过程需要 production connector、DB schema、Web platform、H300 field protocol 或 package schema 变更，先回到 gap register 记录触发条件和缺口，不在 Stage 10 walkthrough 中直接扩大范围。
