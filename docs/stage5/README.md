# Stage 5 业务接入与交付文档

Stage 5 的定位是把 Stage 2 到 Stage 4.4 的技术可行性成果，转换为工程、机器人、算法和数据团队可以理解、准备、试用和验收的业务交付材料。本阶段关注“如何把一次业务导出接入 Physical AI Package，并形成可复盘、可筛选、可训练评估准备的产物”，而不是新增真实生产 connector。

## 面向对象

- 项目负责人：确认当前系统边界、验收路径和下一阶段业务接入风险。
- 工程团队：准备离线导出目录、字段、图片和事件数据。
- 机器人团队：确认时间戳、TCP 位姿、工艺参数、报警事件和图像/视频导出方式。
- 算法/数据团队：使用统一 package 做复盘、候选筛选、训练评估 draft 和 Rerun 回放。

## 推荐阅读顺序

1. 根目录 `README.md`：先理解项目定位、默认安装、测试和常用命令。
2. `engineering_handoff.md`：再按工程对接 contract 准备 `weld_workcell` 源目录。
3. `docs/stage4/README.md`：需要追溯 importer、training draft、Rerun adapter 和 Stage 4 验收链路时阅读。
4. `docs/superpowers/specs/2026-06-11-stage-5-handoff-docs-design.md` 与 `docs/superpowers/plans/2026-06-11-stage-5-handoff-docs.md`：需要了解 Stage 5 设计取舍和实施计划时阅读。

## 系统产出物

- Physical AI Package：统一的 package 目录，包含 manifest、frames、events、labels、metrics 和 artifacts。
- validation summary：`validate` 和 `summarize` 输出的结构化校验与统计结果。
- `derived/candidates.csv`：从 package 中导出的候选样本索引。
- training/evaluation draft：`derived/training_eval/` 下的 draft manifest 和 `samples.csv`。
- Rerun `.rrd`：可用于本地回放和技术评测的 Rerun 数据文件。

## 最小验收流程

1. 默认测试通过：`python -m pytest -q`。
2. package 可校验：`validate` 输出无 error。
3. summary 能读出 frame、event、label、metric count。
4. candidates 可导出：生成 `derived/candidates.csv`。
5. training draft 可导出：生成 `derived/training_eval/`。
6. Rerun 可转换：生成 `.rrd` 文件。

## Stage 5 不做什么

- 不新增真实生产 connector。
- 不做 native GUI 人工验收。
- 不扩展 Physical AI Package schema。
- 不引入真实客户数据或现场敏感数据。
