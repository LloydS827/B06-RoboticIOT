# B06 -> A02 Evidence Handoff

## 定位

本文定义 B06 从 A01 `weld_workcell_job_window` 中向 A02 `ManipulationSkillAsset` 交付 evidence 的边界。它不是 A02 资产库 schema，也不是自动转换器设计。B06 只交付可追溯、已脱敏或 onsite-only 的 evidence/context/attachment/reference。

## Handoff 分类

| B06/A01 field group | Handoff category | A02 use |
| --- | --- | --- |
| confirmed TCP trajectory / path points | evidence | 作为 `ManipulationSkillAsset` 的候选轨迹和路径点依据。 |
| human correction / expert review | evidence | 作为审查记录、可信度和人工修正依据。 |
| quality result | evidence | 作为 outcome label、成功/失败判断和复用边界。 |
| failure phase / exception summary | evidence | 作为失败边界、技能适用条件和迁移评测线索。 |
| workpiece / seam / tool / frame context | context | 说明技能发生的对象、坐标系、TCP 和工艺语义。 |
| model output before confirmation | context | 只作为假设或候选线索，不能直接成为技能标签。 |
| point cloud / image / raw logs / PCL files | attachment | 作为 source evidence 或复盘附件，不进入核心技能字段。 |
| process parameters | context | 说明技能执行条件；是否进入 evidence 取决于 A02 资产定义和审查结论。 |
| work order / customer / device identity | blocked or context after desensitization | 未脱敏时不可交付；脱敏后只作为上下文，不作为技能内容。 |
| onsite-only source files | blocked or attachment reference | 默认不复制，只保留权限受控的 source reference。 |

## Acceptance Checklist

- [ ] 数据已经脱敏，或明确标记为 onsite-only，不复制不可提交数据。
- [ ] 轨迹、TCP、路径点和上下文都有 source refs。
- [ ] 坐标系、tool frame、TCP 假设和标定版本已说明。
- [ ] 质量标签有 reviewer、检测系统或质量记录来源。
- [ ] 专家审查结论说明该片段是否允许作为 `ManipulationSkillAsset` 候选 evidence。
- [ ] 失败边界已描述，包括失败阶段、异常原因或不适用条件。
- [ ] 点云、图像、PCL 中间文件和原始日志默认保持 attachment reference，除非明确允许复制。
- [ ] 未确认模型输出只作为 context，不作为最终标签或技能资产依据。

## 非目标

- 不把完整 A01 H300 原始数据自动转成 A02 技能资产。
- 不定义 A02 `ManipulationSkillAsset` 的完整字段和存储实现。
- 不承诺生产 connector 或自动同步链路。
