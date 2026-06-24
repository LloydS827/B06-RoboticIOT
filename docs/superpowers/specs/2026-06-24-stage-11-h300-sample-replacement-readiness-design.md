# Stage 11 H300 sample replacement readiness 设计

## 1. 背景

B06 当前已经完成 Stage 8 H300 synthetic demo readiness、Stage 9 SDK productization 和 Stage 10 SDK adoption hardening。项目主入口已经收束为 Python SDK first 的工业物理 AI 数据层工具包，默认可运行路径仍是 Stage 8 synthetic Raw/Clean fixture。Stage 8 的 `h300_synthetic_to_real_gap_register.md` 已列出从 synthetic 到真实/脱敏 H300 样本替换需要关闭、拆分或升级的缺口。

上一阶段建议的下一步是 **Stage 11 H300 sample replacement readiness**，前提是真实或脱敏 H300 最小样本至少到位一条。当前仓库仍不应提交真实现场样本，也不能在无样本情况下宣称 real data pilot 已完成。因此 Stage 11 应把“样本到位后如何替换、如何检查、如何记录 gap 状态”产品化为轻量 readiness 流程，而不是抢先建设生产 connector、DB schema 或 H300 现场协议。

## 2. 假设与边界

本阶段基于以下假设推进：

- Stage 8 synthetic fixture 仍是仓库默认可运行样本。
- 真实或脱敏 H300 样本可能在本地、现场或受控目录中出现，但默认不提交仓库。
- 样本替换优先以 `weld_workcell` Clean Zone 目录为输入，不直接修改 Physical AI Package v0.1 schema。
- Raw Zone 可以作为 source artifacts 和 gap 判断证据，但 Clean Zone contract 仍是默认验收边界。
- Stage 8 gap register 是 Stage 11 readiness 判断的主台账；Stage 11 只补充执行流程、状态口径和自动化检查入口。

本阶段不做：

- 不提交真实或脱敏 H300 原始样本、图片、点云、工单号、内网路径或设备身份信息。
- 不实现 production connector、TCP/IP server、SDK bridge、OPC UA/MES/HMI/PLC 直连或 DB ingestion。
- 不新增长期 DB schema，不修改 Physical AI Package v0.1 schema。
- 不把 synthetic Raw payload 定义为 H300 现场协议。
- 不实现 demo UI、A02 schema、A01 到 A02 自动 converter 或完整数据治理平台。

## 3. 目标

Stage 11 完成后，接入团队应能做到：

1. 从 README 和 `docs/stage11/README.md` 理解真实/脱敏 H300 样本到位后的替换顺序。
2. 使用一个轻量 readiness checker 对本地 `weld_workcell` Clean Zone 目录进行检查，得到可读的 gap 状态建议。
3. 明确哪些 gap 可以直接以现有 Clean Zone contract 继续验证，哪些需要 Raw/source artifact 评审，哪些因脱敏、权限或缺真实样本继续 blocked。
4. 使用 SDK 或 CLI 跑通 readiness 检查，而不改变默认 synthetic demo 链路。
5. 在 `details.md` 中留下 Stage 11 决策、产出物、验证结果和下一阶段建议。

## 4. 方案比较

### 方案 A：只补 Stage 11 文档

只新增 `docs/stage11/README.md` 和 replacement checklist，不新增代码或测试。

优点是改动最小、风险最低。缺点是 Stage 8 gap register 已经具备文档基础，只补文档无法让样本到位后的替换评审更可执行，也无法保护默认流程不退化。

结论：不采用，作为方案 B 的一部分保留。

### 方案 B：文档 + 轻量 readiness checker

新增 Stage 11 文档、gap 状态口径、README/details 更新，以及一个只读取本地 Clean/Raw 目录的 readiness checker。checker 通过 SDK 和 CLI 暴露，输出结构化 JSON，覆盖 `job.json`、`frames.csv`、`process.csv`、`events.csv`、`review_labels.csv`、图片引用和可选 Raw manifest/source artifacts 的存在性检查，并把结果映射到 Stage 8 gap IDs。

优点是贴合下一阶段真实需求：样本到位后可以马上跑检查、记录差距、决定是否进入 importer 扩展。它仍保持克制，不接生产系统、不扩 schema、不提交真实数据。缺点是不能替代人工字段评审，但这正符合当前前提。

结论：采用。

### 方案 C：直接建设 H300 production connector 或 schema 扩展

基于 Stage 8 synthetic payload 推导现场协议，新增 connector、DB/schema 或 package metadata 扩展。

优点是看似向生产化推进更快。缺点是当前缺少真实/脱敏样本校准，容易把 synthetic 假设固化成错误接口，且超出 B06 当前 SDK-first 离线数据层边界。

结论：不采用。

## 5. 选定设计

Stage 11 采用方案 B：**文档 + 轻量 readiness checker**。

交付物分为四层：

1. **文档层**：新增 `docs/stage11/README.md`，说明 sample replacement readiness 的输入、流程、gap 状态、命令和非目标；更新 README 和 details，把 Stage 11 加入路线和当前状态。
2. **SDK 层**：新增 `physical_ai_data.stage11_readiness`，提供 `assess_h300_sample_readiness(clean_root, raw_root=None)`。该函数只读取本地文件，不联网、不写真实数据、不修改 package。
3. **CLI 层**：新增 `physical-ai-package assess-h300-readiness --clean-root CLEAN [--raw-root RAW] --json`，输出结构化 readiness report；不改变现有 `run-weld-workcell`、validate、summarize 等命令。
4. **验证层**：新增 focused tests，覆盖 Stage 8 synthetic fixture 的 readiness 输出、缺文件状态、图片引用缺失、Raw manifest/source artifacts 存在性和 CLI JSON smoke。最终运行全量 `python -m pytest -q`。

## 6. Readiness report 设计

`assess_h300_sample_readiness` 返回一个轻量 dataclass 或等价结构，包含：

- `clean_root: Path`
- `raw_root: Path | None`
- `overall_status: str`，取值为 `ready_for_pipeline_smoke`、`review_required` 或 `blocked`
- `checks: list[ReadinessCheck]`
- `gap_statuses: list[GapStatus]`
- `summary: dict[str, object]`

`ReadinessCheck` 最小字段：

- `check_id`
- `status`：`pass`、`review` 或 `block`
- `message`
- `path`

`GapStatus` 最小字段：

- `gap_id`
- `status`：`ready_to_review`、`needs_raw_review`、`blocked` 或 `not_applicable`
- `evidence`
- `next_step`

状态含义：

- `ready_for_pipeline_smoke`：Clean Zone 必需文件存在，基础 CSV/JSON 可读，图片引用无明显缺失；可以继续跑 `run_weld_workcell_pipeline` 做离线 smoke。
- `review_required`：Clean Zone 可以进入下一步 smoke，但 Raw/source artifacts、review labels、图片或 gap 证据仍需人工评审。
- `blocked`：缺少必需 Clean Zone 文件、路径不可读、图片引用缺失且未声明为 onsite-only，或没有足够信息判断最小作业窗口。

## 7. 检查规则

第一版 checker 只做可稳定自动化的检查，不解释真实业务含义：

- 必需 Clean Zone 文件：`job.json`、`frames.csv`、`process.csv`、`events.csv`。
- 可选 Clean Zone 文件：`review_labels.csv`。
- `job.json` 必须可解析，并至少包含任务/作业窗口类字段中的一个可用线索。
- `frames.csv` 必须可解析，至少有一行，并包含 `timestamp_s` 与 TCP pose 相关列；如存在 `image_path`，检查相对路径不越界且文件存在。
- `process.csv` 与 `events.csv` 必须可解析，至少检查 header。
- 如提供 `raw_root`，读取 `manifest.raw.json` 和已知 Stage 8 source artifact 路径，作为 G-003、G-004、G-005、G-011、G-012 的评审证据。
- checker 不尝试验证客户字段真实性、脱敏充分性、坐标系数学正确性、时钟同步质量或 A02 evidence 业务可用性。

## 8. Gap 映射

第一版 gap 映射保持显式、可读、保守：

- G-001：由 `job.json` 中作业窗口/任务/工单字段线索决定是否 `ready_to_review`。
- G-002：由 `frames.csv` 时间戳和 TCP pose 列决定是否 `ready_to_review`。
- G-003、G-004、G-005、G-011、G-012：若 `raw_root` 中存在对应 source artifacts，则为 `needs_raw_review`；否则 `blocked` 或 `not_applicable`。
- G-006：若存在 `review_labels.csv`，为 `ready_to_review`；否则 `needs_raw_review`。
- G-007：若 `process.csv` 可读，为 `ready_to_review`。
- G-008：若 `events.csv` 可读，为 `ready_to_review`。
- G-009：若 `review_labels.csv` 或 Raw quality result 存在，为 `needs_raw_review`；否则 `blocked`。
- G-010：始终需要人工路径/权限矩阵评审，状态为 `needs_raw_review` 或 `blocked`，不由本地文件自动关闭。

checker 不关闭 gap；它只给出“下一步该评审什么”的建议。真正关闭、拆分或升级 gap 仍需要人工在 Stage 8/Stage 11 文档和后续任务中记录。

## 9. CLI 与 SDK 用法

SDK：

```python
from physical_ai_data.stage11_readiness import assess_h300_sample_readiness

report = assess_h300_sample_readiness(
    clean_root="artifacts/stage8/h300_synthetic_demo/clean/weld_workcell",
    raw_root="artifacts/stage8/h300_synthetic_demo/raw",
)

print(report.overall_status)
print(report.to_dict())
```

CLI：

```bash
physical-ai-package assess-h300-readiness \
  --clean-root artifacts/stage8/h300_synthetic_demo/clean/weld_workcell \
  --raw-root artifacts/stage8/h300_synthetic_demo/raw \
  --json
```

默认文本输出可以简洁列出 overall status、blocked checks 和 gap next steps；`--json` 用于测试、脚本和评审记录。

## 10. 测试与验证

本阶段测试策略：

- Stage 8 synthetic fixture + `raw_root` 应得到非 blocked 的 readiness report，并包含 G-001 至 G-012 的 gap status。
- 删除必需 Clean Zone 文件应使 overall status 为 `blocked`，并指出具体文件。
- 删除图片引用目标应 blocked，避免把缺图样本误判为 ready。
- 只提供 Clean Zone、不提供 Raw Zone 时，Clean contract 相关 gap 可 `ready_to_review`，Raw/source artifact gap 保持 `blocked` 或 `needs_raw_review`。
- CLI JSON smoke 应可从 repo root 运行，并返回 `overall_status`、`checks`、`gap_statuses`。
- 文档扫描确认 README、details、docs/stage11 覆盖 Stage 11、sample replacement readiness、gap register 和非目标。
- 最终验证运行 `python -m pytest -q`。

## 11. 成功标准

Stage 11 完成时应满足：

- 新增 Stage 11 spec、plan、stage docs 和 readiness checker。
- README 和 `details.md` 记录 Stage 11 的定位、边界、产出物、验证结果和下一阶段建议。
- SDK/CLI 可以对 Stage 8 synthetic fixture 生成 readiness report。
- readiness checker 不写入真实数据，不提交真实样本，不修改 package schema。
- focused tests 和全量测试通过。
- 没有新增 production connector、DB/schema、H300 现场协议、demo UI 或 A02 converter。

## 12. 下一阶段衔接

Stage 11 之后，建议进入 **Stage 12 first de-identified H300 sample replacement pilot**，但只有在至少一条脱敏 H300 最小作业窗口样本已通过访问和提交边界确认后启动。Stage 12 应基于 Stage 11 readiness report：

- 选择一条脱敏样本在受控目录跑 readiness checker 和 pipeline smoke。
- 逐条关闭、拆分或升级 Stage 8 gap register。
- 只对真实样本证明无法表达、且影响 candidates、training draft、A02 evidence 或审计复盘的字段，启动 importer 或 metadata 扩展。
- demo UI 仍只在 SDK examples 稳定采用且确有评审展示需求后再评估。
