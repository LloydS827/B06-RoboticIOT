# B06 Python SDK

## 定位

B06 的主产品入口是 Python SDK。推荐在研发、平台和数据 pipeline 中直接使用 `physical_ai_data`，把 Clean Zone 工业作业数据和 synthetic/demo Raw/Clean fixture 整理为 Physical AI Package，并导出回放、候选样本、training draft 和 evidence handoff 引用。

CLI 和 scripts 的关系是：

- `physical-ai-package ...`：安装后的标准 CLI，是 SDK 的薄封装，用于工程集成和离线验收。
- `scripts/*.py`：兼容入口和开发期生成器，用于生成 synthetic/demo fixture，或在 console entrypoint 尚未安装时调用历史脚本。

Stage 9 的目标是让 B06 的用户入口收敛为 SDK first，而不是把项目包装成独立 Web app、生产 connector 或通用 IoT 平台。

## 当前公开 API

当前公开 API 从 `physical_ai_data` 顶层导入：

```python
from physical_ai_data import (
    validate,
    summarize,
    export_candidates_csv,
    export_training_eval_draft,
    convert_to_rerun,
)
```

典型用途：

- `validate(package_root)`：校验 Physical AI Package，返回 validation result。
- `summarize(package_root)`：读取 package 并返回概要字典。
- `export_candidates_csv(package_root, output_csv=None, min_score=0.5)`：导出候选样本 CSV。
- `export_training_eval_draft(package_root, split="unspecified")`：导出 `physical-ai-training-eval-draft/v0.2` draft sample index。
- `convert_to_rerun(package_root, output_rrd)`：把 package 转换为 Rerun `.rrd`。

这些 API 面向已存在的 Physical AI Package；如果输入仍是 `weld_workcell` Clean Zone，优先使用 pipeline helper 或 importer contract。

## Pipeline Helper

Stage 9 新增 `run_weld_workcell_pipeline`，用于把 Stage 8 `weld_workcell` Clean Zone 一步转成 package 并执行常用导出。

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

print(result.summary)
```

参数：

- `clean_root: str | Path`：`weld_workcell` Clean Zone 根目录。
- `output_dir: str | Path`：输出 Physical AI Package 目录。
- `copy_images: bool = True`：是否复制图片 artifact。
- `export_candidates: bool = True`：是否显式导出 `derived/candidates.csv`。
- `candidate_min_score: float = 0.5`：候选样本导出阈值。
- `training_split: str | None = "unspecified"`：training/evaluation draft 的 split；传 `None` 时跳过 draft 导出。
- `output_rrd: str | Path | None = None`：Rerun `.rrd` 输出路径；传 `None` 时跳过转换。

`PipelineResult` 字段：

- `package_root: Path`
- `validation: ValidationResult`
- `summary: dict[str, object]`
- `candidates_csv: Path | None`
- `training_draft_dir: Path | None`
- `rrd_path: Path | None`

错误前缀：

- `weld_workcell pipeline failed during import`
- `weld_workcell pipeline produced invalid package`

注意：training draft 导出可能会在内部为 sample rows 创建 candidates；但 `PipelineResult.candidates_csv` 只有在 `export_candidates=True`、即显式请求候选样本导出时才会设置。

## Importer Contract

更底层的 importer contract 适合 importer 测试、对接新 Clean Zone 或调试字段映射。

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

`ImportRequest` 字段：

- `source_format: str`
- `source: Mapping[str, object]`
- `output_dir: str | Path`
- `options: Mapping[str, object] = {}`

`run_import(importer, request)` 会检查 `importer.source_format` 是否匹配 `request.source_format`，然后返回 `ImportResult`。

## CLI 和 scripts 的关系

安装开发环境并生成 Stage 8 demo fixture 后，标准 CLI 是：

```bash
python -m pip install -e ".[dev]"
python scripts/generate_stage8_h300_synthetic_demo.py --output-root artifacts/stage8/h300_synthetic_demo --frames 5
physical-ai-package run-weld-workcell \
  --clean-root artifacts/stage8/h300_synthetic_demo/clean/weld_workcell \
  --output-dir artifacts/stage8/h300_synthetic_demo/package \
  --training-split eval \
  --output-rrd artifacts/stage8/h300_synthetic_demo/package.rrd
```

`physical-ai-package` 面向工程集成和离线验收；它不引入新的业务逻辑，主要把命令行参数转交给 SDK。

`python scripts/physical_ai_package.py ...` 仍保留为兼容入口，适用于历史环境或 console entrypoint 尚未安装的情况。`scripts/generate_stage8_h300_synthetic_demo.py` 等生成器仍用于创建 demo fixture 和回归样本。

## 边界

当前 SDK 不包含以下能力：

- production connector。
- DB ingestion 或长期 DB schema。
- Web app 或 Streamlit app。
- H300 field protocol / 现场协议定义。
- plugin system。

Stage 8 H300 数据仍是 synthetic demo/readiness fixture；真实或脱敏 H300 样本到位后，需要按 Stage 8 gap register 逐项替换和验证。
