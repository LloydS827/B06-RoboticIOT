# Demo UI evaluation

Stage 10 不实现 demo UI。当前优先级是把 SDK、CLI JSON smoke、示例脚本和 Stage 8 synthetic fixture 做成稳定 adoption 路径；在没有真实或脱敏 H300 最小样本前，UI 容易把 synthetic demo 误读成平台或生产接入。

## 为什么本阶段不做 UI

- 还没有一条可公开评审的真实或脱敏 H300 样本。
- SDK examples 和 CLI smoke 已覆盖当前验收链路：Clean Zone -> package -> summary/candidates/training draft/`.rrd`。
- UI 会引入新的展示状态、数据权限、部署和维护问题，但这些不是 Stage 10 adoption 的主要风险。
- 当前边界明确排除 Web app、平台、production connector、DB schema 和 H300 field protocol。

## 候选用户和展示面

未来若触发 UI 评估，候选用户包括：

- A01/H300 工艺或机器人评审人员：需要看 summary、关键帧、候选样本和回放引用。
- 数据平台工程师：需要确认 Clean Zone 输入、package 输出和文件路径。
- A02 evidence 消费方：需要知道哪些内容可作为 evidence handoff，哪些仍是 gap。

可展示的最小 surface：

- package summary 和 validation 状态。
- candidates CSV 的少量行预览。
- training draft 输出目录和 split。
- `.rrd` 文件路径或 Rerun 打开说明。
- Stage 8 gap register 中尚未关闭的替换项。

## 未来最小 UI 形态

如果触发条件满足，优先考虑只读、本地、轻量的 demo surface：

- 输入：一个已生成 package 目录，或一个符合 contract 的 Clean Zone 目录。
- 动作：调用现有 SDK helper，不复制业务逻辑。
- 输出：summary、validation errors/warnings、关键输出路径和少量候选样本预览。
- 运行方式：本地演示，不默认接入认证、数据库或远程服务。

UI 仍应把 Stage 8 synthetic fixture 标为 demo/readiness，不把它包装成真实生产接入。

## 触发条件

满足以下条件后，再重新评估 demo UI：

- 至少有一条经过脱敏和授权的 H300 最小作业窗口样本。
- `examples/sdk_pipeline_stage8.py`、`examples/sdk_existing_package_ops.py`、`examples/sdk_low_level_importer.py` 和 `examples/cli_json_smoke.sh` 稳定通过。
- 评审方明确需要可视化 surface，而不是仅需要 SDK/CLI 输出。
- Stage 8 gap register 已说明该样本仍有哪些字段、权限或语义缺口。

## 非目标

- 不做完整 Web platform。
- 不做 auth、用户、权限或多租户。
- 不做 DB schema 或长期存储。
- 不做 production connector。
- 不定义 H300 field protocol。
- 不变更 package schema。
