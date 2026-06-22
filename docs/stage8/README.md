# Stage 8 A01 H300 synthetic demo readiness

## 阶段定位

Stage 8 是 **A01 H300 synthetic demo readiness**：在仍无真实或脱敏 H300 样本的前提下，用确定性的 H300-oriented synthetic fixture 展示 B06 现有能力链路，并把后续真实接入需要关闭的缺口整理成 `gap register`。

本阶段展示的是 Raw Zone -> Clean Zone -> Physical AI Package -> Rerun replay -> candidates -> training/evaluation draft -> A02 evidence handoff 的离线闭环。它不是 real data pilot，不代表现场协议、生产接入或长期存储方案已经确定。

## 交付物

- `docs/stage8/README.md`：Stage 8 定位、命令、边界和阅读入口。
- `docs/stage8/capability_visualization_report.md`：能力链路图、H300 synthetic 时间线、字段落点、文件树和状态板。
- `docs/stage8/h300_synthetic_to_real_gap_register.md`：从 synthetic 到真实/脱敏样本替换的可执行 `gap register`。
- `docs/stage8/a02_evidence_demo_example.md`：B06 -> A02 evidence handoff 示例，明确 `synthetic_demo_only: true`。

## 生成命令

从仓库根目录生成 Stage 8 Raw/Clean fixture：

```bash
python scripts/generate_stage8_h300_synthetic_demo.py --output-root artifacts/stage8/h300_synthetic_demo --frames 5
```

生成后主要目录为：

```text
artifacts/stage8/h300_synthetic_demo/
  raw/
  clean/weld_workcell/
```

Raw Zone 中的 H300 story、PCL、模型输出、人工修正和质量结果是 source artifacts，用于展示和缺口评审。Clean Zone 仍只承诺现有 `WeldWorkcellPackageImporter` 可结构化读取的 `weld_workcell` contract。

## Clean Zone -> Package Python 示例

```bash
python - <<'PY'
from pathlib import Path
from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter

run_import(
    WeldWorkcellPackageImporter(),
    ImportRequest(
        source_format="weld_workcell",
        source={"root": Path("artifacts/stage8/h300_synthetic_demo/clean/weld_workcell")},
        output_dir=Path("artifacts/stage8/h300_synthetic_demo/package"),
        options={"copy_images": True},
    ),
)
PY
```

## 后续命令

```bash
python scripts/physical_ai_package.py validate artifacts/stage8/h300_synthetic_demo/package --json
python scripts/physical_ai_package.py summarize artifacts/stage8/h300_synthetic_demo/package --json
python scripts/physical_ai_package.py export-candidates artifacts/stage8/h300_synthetic_demo/package
python scripts/physical_ai_package.py export-training-draft artifacts/stage8/h300_synthetic_demo/package --split eval
python scripts/physical_ai_package.py convert-rerun artifacts/stage8/h300_synthetic_demo/package --output-rrd artifacts/stage8/h300_synthetic_demo/package.rrd
```

这些命令验证的是 Clean Zone offline importer contract、Physical AI Package v0.1、候选样本导出、training/evaluation draft 和 Rerun `.rrd` 适配链路。

## 推荐阅读顺序

1. `docs/stage8/README.md`：确认 Stage 8 的 synthetic 边界和运行方式。
2. `docs/stage8/capability_visualization_report.md`：查看 Raw Zone 到 A02 evidence handoff 的链路图和字段落点。
3. `docs/stage8/h300_synthetic_to_real_gap_register.md`：逐条确认真实/脱敏样本需要补齐的字段、文件、权限和触发条件。
4. `docs/stage8/a02_evidence_demo_example.md`：查看哪些内容可作为 A02 evidence，哪些只能作为 context、attachment reference 或 blocked 项。
5. `docs/stage7/README.md`：回看 Stage 7.1 作为 Clean Zone contract 历史基线的定位。

## 边界

Stage 8 做：

- 生成可提交、可复现的 H300 synthetic Raw/Clean fixture。
- 展示 Raw Zone、Clean Zone、Physical AI Package、Rerun、candidates、training draft 和 A02 evidence handoff 的离线闭环。
- 明确哪些字段是 importer_supported，哪些只是 source_artifact_only，哪些需要真实/脱敏样本替换。
- 用 `gap register` 记录后续真实接入评审的默认下一步。

Stage 8 不做：

- 不把 synthetic Raw payload 当作 H300 现场协议。
- 不实现生产 connector、TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连或 DB ingestion。
- 不设计或修改长期 DB schema。
- 不修改 Physical AI Package v0.1 schema。
- 不定义 A02 schema，也不提供 A01 package 到 A02 技能资产的 converter。
- 不提交客户现场原始文件、未脱敏图像/点云、账号密钥、内网地址、权限配置或商业敏感字段。
