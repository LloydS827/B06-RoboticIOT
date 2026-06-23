# B06 Python SDK

## 定位

B06 的主产品入口是 Python SDK。推荐在研发、平台和数据 pipeline 中直接使用 `physical_ai_data`，把 Clean Zone 工业作业数据和 synthetic/demo Raw/Clean fixture 整理为 Physical AI Package，并导出回放、候选样本、training draft 和 evidence handoff 引用。

CLI 和 scripts 的关系是：

- `physical-ai-package ...`：安装后的标准 CLI，是 SDK 的薄封装，用于工程集成和离线验收。
- `scripts/*.py`：兼容入口和开发期生成器，用于生成 synthetic/demo fixture，或在 console entrypoint 尚未安装时调用历史脚本。

Stage 10 的目标是让 SDK adoption 更稳、更容易复现。它不把项目扩展成独立 Web app、production connector 或通用 IoT 平台；Stage 8 synthetic fixture 仍是默认可运行 demo。

## 安装与运行前提

从 repo root 安装开发环境，并在 repo root 执行后续命令：

```bash
python -m pip install -e ".[dev]"
```

如果只运行 `examples/*.py`，脚本会把本地 `src/` 加入 `sys.path`；但验收 CLI、console entrypoint 和测试仍建议先完成 editable install。

## 公共 API 总览

当前顶层 SDK 从 `physical_ai_data` 导入：

```python
from physical_ai_data import (
    validate,
    summarize,
    export_candidates_csv,
    export_training_eval_draft,
    convert_to_rerun,
)
```

| API | Import path | 输入状态 | 输出 | 文件副作用 |
| --- | --- | --- | --- | --- |
| `validate(package_root)` | `physical_ai_data.validate` | 已存在的 Physical AI Package | `ValidationResult` | 无 |
| `summarize(package_root)` | `physical_ai_data.summarize` | 已存在且可读取的 package | `dict[str, object]` summary | 无 |
| `export_candidates_csv(package_root, output_csv=None, min_score=0.5)` | `physical_ai_data.export_candidates_csv` | 已存在的 package | `Path` | 写入 `output_csv`，默认 `package_root/derived/candidates.csv` |
| `export_training_eval_draft(package_root, output_dir=None, split="unspecified")` | `physical_ai_data.export_training_eval_draft` | 已存在的 package；`split` 只能是 `unspecified`、`train`、`eval`、`validation`、`test`、`holdout` | `Path` | 写入 draft 目录，默认 `package_root/derived/training_eval`；可能生成候选样本中间文件 |
| `convert_to_rerun(package_root, output_rrd)` | `physical_ai_data.convert_to_rerun` | 已存在的 package | `Path` | 写入 `.rrd` 文件 |
| `run_weld_workcell_pipeline(clean_root, output_dir, ...)` | `physical_ai_data.pipelines.run_weld_workcell_pipeline` | `weld_workcell` Clean Zone 根目录 | `PipelineResult` | 写 package；可选写 candidates、training draft、`.rrd` |
| `run_import(importer, ImportRequest(...))` | `physical_ai_data.importers.run_import` | importer contract 输入 | `ImportResult` | 由 importer 决定；`WeldWorkcellPackageImporter` 会写 package |
| `generate_stage8_h300_synthetic_demo(output_root, frame_count=5)` | `physical_ai_data.stage8_h300_demo.generate_stage8_h300_synthetic_demo` | demo 输出根目录 | Stage 8 fixture result | 写 synthetic Raw/Clean fixture；这是 demo helper，不是顶层 API |

## 返回对象

`ValidationResult` 来自 `physical_ai_data.schema`：

- `errors: list[ValidationMessage]`
- `warnings: list[ValidationMessage]`
- `summary: dict[str, object]`
- `ok: bool` property，等价于没有 errors

`ValidationMessage` 字段是 `code`、`message`、`path`。

`PipelineResult` 来自 `physical_ai_data.pipelines`：

- `package_root: Path`
- `validation: ValidationResult`
- `summary: dict[str, object]`
- `candidates_csv: Path | None`
- `training_draft_dir: Path | None`
- `rrd_path: Path | None`

`ImportRequest` 来自 `physical_ai_data.importers`：

- `source_format: str`
- `source: Mapping[str, object]`
- `output_dir: str | Path`
- `options: Mapping[str, object] = {}`

`ImportResult` 字段：

- `package_root: Path`
- `source_format: str`
- `source_id: str`
- `frame_count: int`
- `warnings: list[str]`

## Pipeline helper

`run_weld_workcell_pipeline` 适合大多数 SDK adoption 场景：输入 Stage 8 或同 contract 的 `weld_workcell` Clean Zone，输出 package，并按需执行常用导出。

```python
from physical_ai_data.pipelines import run_weld_workcell_pipeline

result = run_weld_workcell_pipeline(
    clean_root="artifacts/stage8/h300_synthetic_demo/clean/weld_workcell",
    output_dir="artifacts/stage8/h300_synthetic_demo/package",
    copy_images=True,
    export_candidates=True,
    candidate_min_score=0.5,
    training_split="eval",
    output_rrd="artifacts/stage8/h300_synthetic_demo/package.rrd",
)

print(result.validation.ok)
print(result.summary)
print(result.candidates_csv)
```

默认行为：

- `copy_images=True`：把 Clean Zone 引用的图片复制进 package artifacts。
- `export_candidates=True`：显式写 `derived/candidates.csv`。
- `candidate_min_score=0.5`：候选样本最小分数。
- `training_split="unspecified"`：写 training/evaluation draft。
- `output_rrd=None`：默认不写 `.rrd`，需要回放文件时显式传路径。

可选跳过：

- `export_candidates=False`：跳过显式候选样本导出，`PipelineResult.candidates_csv` 为 `None`。
- `training_split=None`：跳过 training draft，`PipelineResult.training_draft_dir` 为 `None`。
- `output_rrd=None`：跳过 Rerun 转换，`PipelineResult.rrd_path` 为 `None`。

注意：training draft 导出可能会在内部为 sample rows 创建 candidates；但 `PipelineResult.candidates_csv` 只有在 `export_candidates=True` 时才会设置。

## 低层 importer contract

当输入仍是 `weld_workcell` Clean Zone，优先用 pipeline helper。只有在以下场景才建议直接使用 importer contract：

- 编写或测试新的 importer。
- 调试 Clean Zone 到 package 的字段映射。
- 只需要 import package，不需要 candidates、training draft 或 `.rrd`。
- 需要明确控制 importer 的 `source_format`、`source` 和 `options`。

```python
from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter

result = run_import(
    WeldWorkcellPackageImporter(),
    ImportRequest(
        source_format="weld_workcell",
        source={"root": "artifacts/stage8/h300_synthetic_demo/clean/weld_workcell"},
        output_dir="artifacts/stage8/h300_synthetic_demo/package",
        options={"copy_images": True},
    ),
)

print(result.package_root)
```

`run_import(importer, request)` 会先检查 `importer.source_format` 是否匹配 `request.source_format`；不匹配会抛出 `ValueError`。`WeldWorkcellPackageImporter` 导入后还会校验 package，校验失败也会抛出 `ValueError`。

## 错误排查

常见问题：

- **缺少 Clean Zone 文件**：`weld_workcell` 输入必须包含 `job.json`、`frames.csv`、`process.csv`、`events.csv`；`review_labels.csv` 可选。缺文件时先回到 fixture 生成或 Clean Zone replacement 步骤。
- **invalid package**：pipeline helper 会在 import 后调用 `validate`；若报 `weld_workcell pipeline produced invalid package`，先查看 `ValidationResult.errors` 中的 `code`、`message`、`path`。
- **invalid package source**：如果 `source_format` 不是 `weld_workcell`，`WeldWorkcellPackageImporter` 不会处理；使用正确 importer 或修正 `ImportRequest.source_format`。
- **invalid split**：当前允许值是 `unspecified`、`train`、`eval`、`validation`、`test`、`holdout`；建议 adoption 阶段统一使用 `eval` 或 `unspecified`，避免下游评审对 split 语义不一致。
- **image path issues**：`frames.csv` 的 `image_path` 必须能从 Clean Zone root 解析。若真实/脱敏替换时图片暂不可交付，先在 Stage 8 gap register 中标记，不要把缺图伪装成生产接入完成。
- **输出目录与源目录相同**：`WeldWorkcellPackageImporter` 会拒绝 `output_dir` 等于 `source.root`，避免覆盖 Clean Zone。

## CLI 到 SDK 的映射

| CLI command | SDK function/helper |
| --- | --- |
| `physical-ai-package validate PACKAGE --json` | `physical_ai_data.validate(package_root)` |
| `physical-ai-package summarize PACKAGE --json` | `physical_ai_data.summarize(package_root)` |
| `physical-ai-package export-candidates PACKAGE` | `physical_ai_data.export_candidates_csv(package_root, ...)` |
| `physical-ai-package export-training-draft PACKAGE --split eval` | `physical_ai_data.export_training_eval_draft(package_root, split="eval")` |
| `physical-ai-package convert-rerun PACKAGE --output-rrd out.rrd` | `physical_ai_data.convert_to_rerun(package_root, output_rrd)` |
| `physical-ai-package run-weld-workcell --clean-root CLEAN --output-dir PACKAGE ...` | `physical_ai_data.pipelines.run_weld_workcell_pipeline(...)` |
| `python scripts/generate_stage8_h300_synthetic_demo.py ...` | `physical_ai_data.stage8_h300_demo.generate_stage8_h300_synthetic_demo(...)`，demo helper |
| `python scripts/physical_ai_package.py ...` | 兼容 CLI wrapper，映射同上 |

## Examples

- `examples/sdk_existing_package_ops.py`：生成一个 sample package，并调用顶层 SDK 的 validate、summary、candidates、training draft、Rerun 转换。
- `examples/sdk_pipeline_stage8.py`：生成 Stage 8 H300 synthetic fixture，并调用 `run_weld_workcell_pipeline`。
- `examples/sdk_low_level_importer.py`：直接使用 `ImportRequest`、`run_import` 和 `WeldWorkcellPackageImporter`。
- `examples/cli_json_smoke.sh`：CLI JSON smoke，适合 adoption 最小验收。
- `docs/sdk/stage8_pipeline_walkthrough.md`：不依赖 Jupyter 的 notebook-style walkthrough。
- `docs/sdk/adoption_checklist.md`：SDK adoption checklist。
- `docs/sdk/demo_ui_evaluation.md`：demo UI 是否进入下一阶段的评估口径。

最小 CLI 路径：

```bash
python scripts/generate_stage8_h300_synthetic_demo.py --output-root artifacts/stage8/h300_synthetic_demo --frames 5
physical-ai-package run-weld-workcell \
  --clean-root artifacts/stage8/h300_synthetic_demo/clean/weld_workcell \
  --output-dir artifacts/stage8/h300_synthetic_demo/package \
  --training-split eval \
  --output-rrd artifacts/stage8/h300_synthetic_demo/package.rrd
```

## 边界

当前 SDK adoption 不包含以下能力：

- production connector。
- DB ingestion 或长期 DB schema。
- Web app、Streamlit app 或平台化 UI。
- H300 field protocol / 现场协议定义。
- package schema 变更。
- plugin system。

Stage 8 H300 数据仍是 synthetic demo/readiness fixture；真实或脱敏 H300 样本到位后，需要先按 `docs/stage8/h300_synthetic_to_real_gap_register.md` 逐项替换和验证，再决定是否进入 connector、DB/schema、Web platform 或现场协议工作。
