# Stage 11 H300 sample replacement readiness

## 阶段定位

Stage 11 是 **H300 sample replacement readiness**：在 Stage 8 synthetic fixture、Stage 9 SDK-first 入口和 Stage 10 adoption path 之后，提供真实/脱敏 H300 样本替换前的检查流程、命令入口和 `gap register` 状态口径。

本阶段不是 real data pilot 完成态，不表示仓库中已经存在真实 H300 样本，也不表示 H300 现场协议、生产接入、长期存储或 A02 转换流程已经完成。Stage 11 的职责是把候选样本到位后的第一轮检查做成可执行门禁：先确认 Clean Zone 是否能替换 Stage 8 synthetic 输入，再判断哪些 gap 可以进入人工评审、哪些仍需 Raw/source artifact evidence、哪些继续 blocked。

## 输入边界

- 必需输入：一个 `weld_workcell` Clean Zone root，目录中应包含现有 `WeldWorkcellPackageImporter` contract 需要的 `job.json`、`frames.csv`、`process.csv` 和 `events.csv`。
- 可选输入：Raw Zone root，用于提供 source artifact evidence，例如点云、PCL 输出、模型输出、质量结果、HMI/TCP JSON、坐标系或标定说明。Raw Zone evidence 只帮助评审 gap，不替代 Clean Zone contract。
- 真实/脱敏样本边界：真实或脱敏 H300 样本应保留在 local/onsite controlled directories，不提交仓库；客户现场原始文件、未确认可提交的图像/点云、工单、人员、设备身份、内网路径、权限配置和商业敏感字段默认不可提交。

## 推荐流程

1. 先生成并运行 Stage 8 synthetic fixture，作为 SDK/CLI baseline。
2. 将 SDK 或 CLI readiness checker 指向候选 Clean/Raw roots。
3. 如果 `overall_status=blocked`，先修复 Clean Zone replacement，再进入 pipeline smoke。
4. 如果返回 `review_required`，运行 `physical-ai-package run-weld-workcell` smoke，并人工复核 gap statuses。
5. 手动关闭、拆分或升级 Stage 8 `gap register` 中的 gap；checker 只给出下一步建议，不自动关闭 gap。

## SDK 示例

```python
from physical_ai_data.stage11_readiness import assess_h300_sample_readiness

report = assess_h300_sample_readiness(
    clean_root="path/to/candidate/clean/weld_workcell",
    raw_root="path/to/candidate/raw",
)

print(report.overall_status)
print(report.to_dict())
```

如果候选样本暂时只有 Clean Zone，也可以省略 `raw_root`。这种情况下，Clean Zone contract 相关 gap 仍可进入评审，但依赖 Raw/source artifact evidence 的 gap 通常会保持 `needs_raw_review` 或 `blocked`。

## CLI 示例

```bash
physical-ai-package assess-h300-readiness \
  --clean-root path/to/candidate/clean/weld_workcell \
  --raw-root path/to/candidate/raw \
  --json
```

文本输出用于人工快速阅读，`--json` 用于评审记录、脚本和回归测试。该命令是 assessment tool：当检查本身成功执行时，即使报告中出现 `overall_status=blocked`，也应作为可记录的评估结果处理，而不是代表 CLI 执行失败。

通过 readiness 后，继续运行最小 pipeline smoke：

```bash
physical-ai-package run-weld-workcell \
  --clean-root path/to/candidate/clean/weld_workcell \
  --output-dir /tmp/h300_candidate_package \
  --training-split eval \
  --output-rrd /tmp/h300_candidate_package.rrd
```

## 状态解释

`overall_status` 面向流程门禁：

- `ready_for_pipeline_smoke`：Clean Zone 最小 contract 通过，自动化检查未发现 block/review 项；可以继续跑 pipeline smoke，但仍需人工确认业务含义。
- `review_required`：Clean Zone 可以进入 smoke，但 Raw/source artifacts、review labels、权限、脱敏或某些 gap evidence 仍需人工复核。
- `blocked`：缺少必需 Clean Zone 文件、JSON/CSV 不可读、关键列不足、非空图片引用缺失或路径越界；应先修复 Clean Zone replacement。

`gap_statuses` 面向 Stage 8 `gap register`：

- `ready_to_review`：已有足够 Clean Zone 线索，可进入人工评审；不等于 gap 已关闭。
- `needs_raw_review`：需要 Raw Zone source artifact evidence、字段说明、脱敏证明或 A01/A02 共同判断。
- `blocked`：缺少必要样本、字段、文件、权限或脱敏边界，暂不能进入有效评审。
- `not_applicable`：当前候选样本或路径不适用该 gap；仍需在评审记录中说明原因。

## 非目标

Stage 11 不实现 production connector，不实现 TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连或 DB ingestion；不新增长期 DB/schema；不修改 Physical AI Package v0.1 schema；不实现 demo UI；不实现 A02 converter；不确定 H300 field protocol。Stage 11 也不把 Stage 8 synthetic Raw payload 升级为现场协议。

## Stage 12 gate

Stage 12 建议定义为 first de-identified H300 sample replacement pilot，但只有在至少一条脱敏 H300 最小作业窗口样本已经完成访问边界、提交边界和受控目录确认后才启动。Stage 12 应基于 Stage 11 readiness report 和 Stage 8 `gap register`，逐条关闭、拆分或升级 gap，并且只在真实样本证明必要时再评估 importer、metadata 或流程扩展。
