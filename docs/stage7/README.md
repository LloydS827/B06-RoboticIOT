# Stage 7.1 A01 H300 最小焊接作业窗口数据试点

## 阶段定位

Stage 7.1 承接 Stage 7 simulated Raw/Clean fixture，也为未来真实/脱敏样本进入 Raw Zone、Clean Zone 和 Physical AI Package 链路做准备。当前还没有真机接入条件，因此本阶段不假设已有现场协议，不把仿真 payload 当成生产接口。

第一样板收束到 A01 H300 最小焊接作业窗口：先沿用确定性的 simulated Raw/Clean fixture 作为当前无真机条件下的默认可运行替代输入，再用真实或脱敏 H300 样本逐步替换 Raw Zone。`WeldWorkcellPackageImporter` 是 Clean Zone offline importer contract，不是生产 connector。

## 为什么从仿真做起

Stage 6 已经明确了真机数据链路、字段优先级、Raw Zone / Clean Zone / Physical AI Package 的职责边界，但 A01 H300 的真实 SDK、TCP JSON、文件同步样例或 DB 样例尚未到位。

从仿真做起可以先确认最小数据窗口、目录边界、脱敏要求和验收链路，同时避免在没有真实 payload、错误模型和权限边界时过早实现生产接入。Stage 7 不实现生产 connector、server、DB 或 schema 变更。

## 最小焊接作业窗口

Stage 7.1 的 A01 H300 最小窗口只覆盖一个小焊接片段，不代表完整工单生命周期：

- 一个 `job_window_id`、`work_order_id`、`task_id`、`part_id` 和 `seam_id`。
- 建议 3 到 10 秒窗口，覆盖 approach、weld、cooldown 或等价阶段。
- 至少 1 条点云引用和至少 1 张图像引用。
- 至少 3 帧机器人位姿。
- 至少 1 组相机位姿/标定说明。
- 至少 1 条工艺参数记录。
- 至少 1 条 PCL 或上游感知模型输出。
- 至少 1 条模型输出和人工修正记录。
- 至少 1 条执行事件、异常或报警记录。
- 至少 1 条质量结果或质量评审记录。
- 必须记录时间戳来源、字段单位、坐标系假设和脱敏状态。

## 推荐阅读顺序

1. `docs/stage7/README.md`：了解 Stage 7 定位、边界和默认命令。
2. `docs/stage7/sample_request_checklist.md`：查看真实/脱敏样本需要提供哪些材料。
3. `docs/stage7/raw_clean_zone_pilot.md`：查看 Raw Zone、Clean Zone 目录约定和后续决策表。
4. `docs/stage7/h300_weld_workcell_field_alignment.md`：查看 H300 字段如何落到 Clean Zone contract。
5. `docs/profiles/a01_weld_workcell_job_window.md`：对齐 A01 最小焊接作业窗口画像。
6. `docs/profiles/b06_to_a02_evidence_handoff.md`：对齐 B06 到 A02 的证据交付边界。
7. `docs/stage6/README.md`：回看 Stage 6 真机数据接入与数据资产化主线。
8. `docs/stage6/real_data_field_mapping.md`：回看第一轮字段优先级和待确认问题。
9. `docs/superpowers/specs/2026-06-16-stage-7-simulated-small-job-window-pilot-design.md`：需要追溯 Stage 7 设计取舍时阅读。

## 默认命令

生成 Stage 7 simulated Raw/Clean fixture，作为当前无 A01 H300 真机接入条件下的默认可运行替代输入：

```bash
python scripts/generate_stage7_sim_window.py --output-root artifacts/stage7/sim_weld_window --frames 5
```

生成后，Clean Zone 目录位于：

```text
artifacts/stage7/sim_weld_window/clean/weld_workcell/
```

该目录可以通过现有 `WeldWorkcellPackageImporter` 导入 Physical AI Package。这里验证的是 Clean Zone offline importer contract，不是生产 connector、在线 server 或 DB ingestion。

## 当前产出物

- Stage 7 设计说明：`docs/superpowers/specs/2026-06-16-stage-7-simulated-small-job-window-pilot-design.md`。
- Stage 7 实施计划：`docs/superpowers/plans/2026-06-16-stage-7-simulated-small-job-window-pilot.md`。
- Stage 7.1 A01 H300 总览：`docs/stage7/README.md`。
- A01 H300 真实/脱敏样本请求清单：`docs/stage7/sample_request_checklist.md`。
- A01 H300 Raw/Clean Zone 试点约定：`docs/stage7/raw_clean_zone_pilot.md`。
- H300 字段对齐：`docs/stage7/h300_weld_workcell_field_alignment.md`。
- 仿真小作业窗口生成脚本：`scripts/generate_stage7_sim_window.py`。

## MVP 边界

本阶段做：

- 定义 A01 H300 最小焊接作业窗口。
- 生成可替换为真实/脱敏输入的 Raw/Clean fixture。
- 让 Clean Zone 对齐现有 `weld_workcell` importer contract。
- 记录真实/脱敏样本请求、脱敏边界和后续评审口径。

本阶段不做：

- 不实现生产 connector。
- 不实现 TCP/IP server、SDK bridge、OPC UA/MES/HMI 直连或 DB ingestion。
- 不设计或修改长期 DB schema。
- 不修改 Physical AI Package v0.1 schema。
- 不把仿真 payload 定义为现场协议。
- 不提交未脱敏真实数据。

## 验收方式

文档层验收：

- 新读者能理解 Stage 7.1 是连接 Stage 7 simulated fixture 与 A01 H300 真实/脱敏样本的最小作业窗口试点。
- 工程和机器人团队能知道应提供哪些样本、哪些说明和哪些脱敏确认。
- Raw Zone、Clean Zone、Physical AI Package 的边界清楚。
- `WeldWorkcellPackageImporter` 的角色清楚：它导入 Clean Zone，不是生产 connector。

系统层验收：

- 默认命令可以生成 Raw/Clean fixture。
- Clean Zone 可导入 Physical AI Package。
- 生成的 package 可继续进入 validate、summarize、candidate export、training draft 和 Rerun adapter 链路。

## 下一步

下一步应进入 A01 H300 真实/脱敏样本替换与缺口评审：用一个真实或脱敏焊接作业窗口替换 Stage 7 simulated Raw Zone，记录字段、时间戳、单位、坐标系、存储路径、权限和脱敏缺口。只有真实样本证明必要时，才考虑 importer 演进、connector skeleton、DB schema 或 package schema 扩展。
