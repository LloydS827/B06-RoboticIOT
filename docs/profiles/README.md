# B06 Project Data Profiles

## 定位

B06 profile 是 A01、A02、B08、S01 等项目之间的数据 contract，用来说明一类数据包应包含什么上下文、证据、引用和边界。它不是一次性完整 schema 实现，也不是生产 connector、DB schema 或现场协议。

Profile 的作用是让项目团队在真实样本、脱敏样本和仿真样本之间保持同一套语义边界：哪些内容可以进入 Raw Zone，哪些内容应整理到 Clean Zone，哪些内容能派生为 Physical AI Package、回放、候选样本或训练评测 draft。

## 阅读顺序

1. `a01_weld_workcell_job_window.md`：先理解 A01 H300 最小焊接作业窗口。
2. `b06_to_a02_evidence_handoff.md`：再看 B06 如何把 A01 作业窗口中的证据交给 A02。
3. `a02_manipulation_skill_asset_evidence.md`：理解 A02 `ManipulationSkillAsset` 所需 evidence。
4. `b08_equipment_timeseries_observation_package.md`：理解设备时序观测 profile。
5. `s01_manufacturing_event_context_package.md`：理解系统级制造事件上下文 profile。

## 共同边界

- Profile 是跨项目沟通 contract，不代表已经实现代码级完整 schema。
- Profile 不等于生产 connector；本目录不定义 TCP/IP server、SDK bridge、OPC UA、MES、HMI、PLC 直连或数据库写入。
- Raw Zone 保留来源 payload、文件和引用；Clean Zone 做字段、时间、坐标、对象和质量语义整理；Package 层用于回放、候选样本和训练评测 draft。
- 未脱敏真实数据不可提交到仓库，包括客户现场原始文件、未脱敏图像/点云、账号密钥、内部网络地址、权限配置和商业敏感字段。
- 脱敏数据仍需确认可提交边界；默认先按 onsite-only 或本地 artifact 处理。
- 仿真数据可以作为默认可运行样本，但不能被写成生产协议。
- 临时 artifact 例如 `.rrd`、candidates、training draft、Raw/Clean 输出应放在 `artifacts/` 或 `/tmp`，默认不提交。
- B08 和 S01 保持独立 profile，不强行映射到机器人 workcell 作业结构。
- Rerun 是可替换 replay backend，不是 profile 的主数据结构。
