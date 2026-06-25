# Stage 11.1 SDK real-data onboarding hardening design

## 背景

Stage 9 已把 B06 收束为 Python SDK first，Stage 10 已补齐 SDK adoption 文档、examples 和 CLI smoke，Stage 11 已新增 H300 sample replacement readiness checker。基线能力已经可以让研发人员通过 synthetic fixture 跑通 `weld_workcell` Clean Zone -> Physical AI Package -> candidates/training draft/Rerun 的离线闭环。

当前用户关心的问题更接近产品化验收：工程师拿到真实或脱敏数据后，是否能快速利用现有 SDK 完成数据整理。如果只看代码能力，主链路已完成；如果按工程交付体验判断，仍有不规范之处：

- README 与 SDK docs 说明了 synthetic adoption，但真实/脱敏 Clean Zone 的推荐路径散落在 Stage 8、Stage 10、Stage 11 文档中。
- 顶层 SDK 只暴露已有 package 操作，Stage 11 readiness 仍需从阶段模块导入，和“先评估再整理”的真实数据路径不够一致。
- 当前 examples 主要证明 synthetic demo adoption，缺少一个可直接照搬的“候选 Clean/Raw root -> readiness -> pipeline smoke -> 输出索引”脚本。
- onboarding 文档未显式提醒 editable install 可能指向旧 worktree；本次基线审计中就复现了旧 editable 指针导致 SDK import 失败的问题。
- `PipelineResult` 已包含核心输出路径，但还没有一个稳定的 `to_dict()`/artifact index，CLI JSON 与 examples 各自拼 payload，产品化接口不够统一。

## 目标

Stage 11.1 的目标是强化工程师真实/脱敏数据整理路径，让一个有本地候选 H300 Clean Zone 的工程师可以：

1. 安装并确认当前命令指向本仓库 SDK。
2. 对候选 Clean/Raw roots 执行 readiness check。
3. 在 Clean Zone 未 blocked 时运行最小 pipeline smoke。
4. 获得 package、validation、summary、candidates、training draft、Rerun `.rrd` 的统一输出索引。
5. 知道哪些问题应修 Clean Zone、哪些应回到 Stage 8 gap register、哪些需要人工脱敏/权限评审。

## 非目标

本阶段不实现 Stage 12 first de-identified H300 sample replacement pilot，因为尚未确认至少一条脱敏 H300 最小作业窗口样本的访问和提交边界。

本阶段也不实现 production connector、TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连、DB ingestion、长期 DB schema、Web/demo UI、H300 现场协议、A02 converter 或 Physical AI Package v0.1 schema changes。

## 方案比较

### 方案 A：只更新文档

优点是风险低、改动小；缺点是无法减少 SDK/API 使用上的分散感，也不能用测试锁住工程师真实数据整理路径。它适合补充说明，但不足以回答“SDK 化是否完成”。

### 方案 B：新增轻量 onboarding 层（推荐）

在现有 SDK/CLI 之上做小范围产品化硬化：

- 顶层 SDK 暴露 `assess_h300_sample_readiness` 和 report 类型。
- `PipelineResult` 提供 `to_dict()`，CLI JSON、examples 和文档复用同一输出口径。
- 新增真实/脱敏候选样本 onboarding example，串起 readiness 和 pipeline smoke。
- 新增 SDK doctor 或环境检查命令，帮助工程师确认当前 import path、console entrypoint 和可选依赖状态。
- 新增一页式真实数据整理指南，并同步 README/details。

该方案不改变主数据结构，不扩展现场接入范围，但显著降低工程师从真实数据到整理结果的操作摩擦。

### 方案 C：直接做 connector/平台化重构

优点是看起来更接近完整产品；缺点是没有真实样本和现场协议时会过早固化边界，容易把 synthetic/readiness 口径误扩成生产接入。当前不采用。

## 决策

采用方案 B，阶段名为 **Stage 11.1 SDK real-data onboarding hardening**。

这个阶段承认 SDK 化主链路已经完成，但产品化易用性还需要一层薄而稳定的工程 onboarding。它不抢占 Stage 12 样本替换试点，也不把系统推进到 connector/DB/UI。成功标准是：真实/脱敏样本到位后，工程师能按一个短路径完成 readiness、pipeline smoke 和输出交付物索引；如果失败，也能快速定位是安装环境、Clean Zone contract、Raw evidence、脱敏权限还是 gap register 问题。

## 设计

### SDK public surface

顶层 `physical_ai_data` 和 `physical_ai_data.sdk` 增加稳定导出：

- `assess_h300_sample_readiness(clean_root, raw_root=None)`
- `H300ReadinessReport`
- `ReadinessCheck`
- `GapStatus`

这些 API 仍复用 `physical_ai_data.stage11_readiness` 的实现，不迁移业务逻辑。这样做的意图是把“真实数据替换前检查”提升为 SDK adoption 的常规步骤，同时避免重写 Stage 11 checker。

`PipelineResult` 增加 `to_dict()`，输出字段与当前 CLI JSON 保持兼容：

- `package_root`
- `validation`
- `summary`
- `candidates_csv`
- `training_draft_dir`
- `rrd_path`

`validation` 内继续包含 `ok`、`summary`、`errors`、`warnings`。CLI `_pipeline_payload()` 改为调用 `result.to_dict()`，避免 CLI 与 SDK example 重复维护 payload 结构。

### SDK doctor

新增轻量 `physical_ai_data.environment` 模块，提供：

- `inspect_sdk_environment() -> SdkEnvironmentReport`
- `SdkEnvironmentReport.to_dict()`

检查内容保持最小：

- 当前 `physical_ai_data` import path。
- 当前 package version。
- 当前 Python executable。
- 当前 working directory。
- `physical-ai-package` console entrypoint 是否可解析。
- console entrypoint 路径是否存在。
- 可选依赖 `rerun`、`lerobot` 是否可 import。

新增 CLI：

```bash
physical-ai-package doctor --json
```

文本输出用于人工快速判断，JSON 用于 onboarding smoke 和文档记录。doctor 不联网、不读取真实数据、不修改环境；它只报告当前运行状态。若发现 package import path 指向不存在路径，CLI 返回非零；可选依赖缺失不作为失败。

### Real-data onboarding example

新增 `examples/sdk_real_data_onboarding.py`：

```bash
python examples/sdk_real_data_onboarding.py \
  --clean-root path/to/candidate/clean/weld_workcell \
  --raw-root path/to/candidate/raw \
  --output-root /tmp/b06_h300_candidate_onboarding \
  --training-split eval \
  --output-rrd /tmp/b06_h300_candidate_onboarding/package.rrd
```

脚本行为：

1. 调用 `assess_h300_sample_readiness`。
2. 若 readiness `overall_status=blocked`，输出 JSON report，并返回 exit 2。
3. 若不是 blocked，调用 `run_weld_workcell_pipeline`。
4. 输出统一 JSON，包括 readiness report、pipeline result 和建议的 next steps。

它仍可用 Stage 8 synthetic fixture 做测试输入，但文案明确这是“候选真实/脱敏 Clean Zone 的运行模板”，不是新的 synthetic demo。

### 文档结构

新增 `docs/sdk/real_data_onboarding.md`，作为工程师拿到真实/脱敏样本后的主入口。内容包括：

- 先运行 `physical-ai-package doctor --json`。
- 准备 `weld_workcell` Clean Zone 的最小文件和不可提交边界。
- 运行 readiness。
- 解释 blocked/review_required/ready_for_pipeline_smoke。
- 运行 SDK onboarding example 或 CLI pipeline smoke。
- 查看输出索引。
- 失败分流：安装环境、Clean Zone contract、Raw evidence、脱敏权限、Stage 8 gap register。

更新 `README.md` 和 `docs/sdk/README.md`，把真实数据整理路径从历史阶段文档中提升为 SDK adoption 的主流程之一。

更新 `details.md`，记录 Stage 11.1 的完成内容、验证命令和下一步仍回到 Stage 12 样本替换 gate。

### 测试

新增或更新测试：

- 顶层 SDK 导出 readiness API 和类型，且仍不导入 CLI/LeRobot。
- `PipelineResult.to_dict()` 输出与 CLI JSON payload 一致。
- `physical-ai-package doctor --json` 可运行，返回 import path、version、python executable 和 console entrypoint 信息。
- doctor 在当前 package path 存在时返回 exit 0。
- `examples/sdk_real_data_onboarding.py` 可用 Stage 8 fixture 作为候选输入跑通，输出 readiness + pipeline result。
- onboarding example 在 Clean Zone blocked 时返回 exit 2，并不写 package。

保留 full suite 作为最终验收。

## 成功标准

- 工程师可以从 `docs/sdk/real_data_onboarding.md` 独立完成“环境检查 -> readiness -> pipeline smoke -> 输出索引”。
- README 的推荐路径明确：synthetic baseline 是默认可运行路径；真实/脱敏样本进入前先走 Stage 11/11.1 readiness/onboarding；Stage 12 仍等待真实样本 gate。
- 顶层 SDK 能直接导入 readiness checker，pipeline result 有稳定 dict 表示。
- CLI 有 `doctor` 命令帮助定位旧 editable install、命令路径和可选依赖状态。
- examples 和 tests 覆盖真实数据 onboarding 的 happy path 与 blocked path。
- 不引入 connector、DB、UI、schema changes 或真实数据提交。
