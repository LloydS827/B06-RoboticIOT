# Rerun.io 阶段二本地技术评测报告

## 1. 实验日期

- 日期：2026-06-07
- 阶段：Rerun.io 本地技术评测阶段二
- 基线：Python 3.11+、`rerun-sdk[dataplatform] 0.33.0`

## 2. 实验目标

本阶段目标是在不接入机器人真机、不引入 ROS/Gazebo/MoveIt 的前提下，用可重复生成的焊接工站模拟数据验证 Rerun 对 Physical AI 数据层第一批样板能力的支撑程度。

重点验证问题：

- 能否表达图像、点云、机器人 TCP 位姿、轨迹、事件、工艺参数和模型输出；
- 能否写出可校验的 `.rrd` recording；
- 能否按候选条件导出训练/评测样本；
- 能否形成 external-importer-style 的现场数据包导入原型；
- 能否尝试 Catalog 和 DataFrame/Chunk 查询；
- 能否用一个开源机器人数据小样本做字段结构对照。

## 3. 实验环境

- 项目包：`rerun_stage2`
- 依赖入口：`pyproject.toml`
- 运行说明：`docs/stage2/README.md`
- Viewer/Blueprint 检查清单：`docs/stage2/viewer_blueprint_checklist.md`
- 生成产物目录：`artifacts/stage2/`，该目录不提交到 git。

## 4. 已实现内容

- Python 工程骨架和 pytest 配置。
- 确定性的模拟机器人焊接工站数据生成器。
- 模拟数据包目录结构：`manifest.json`、`frames.csv`、`events.csv`、`quality.json`、`point_cloud.csv`、`images/`。
- Rerun writer：写入坐标系、Transform3D、点云、轨迹、TCP 点、图像、工艺参数、缺陷概率和事件日志。
- 多 timeline：`sim_time`、`robot_tick`、`camera_frame`、`weld_phase`。
- 候选样本 CSV 导出。
- external-importer-style CLI。
- 本地 Catalog 表创建/查询尝试。
- `.rrd` Chunk/DataFrame 查询尝试。
- LeRobot PushT parquet 小样本下载、字段读取和模拟包转换。

## 5. 已验证命令

单元测试：

```bash
PYTHONPATH=src python3 -m pytest -q
```

结果：14 个测试通过。

生成模拟数据和 `.rrd`：

```bash
python3 scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/smoke --frames 12 --write-rrd --output-rrd artifacts/stage2/smoke.rrd
rerun rrd verify artifacts/stage2/smoke.rrd
rerun rrd stats artifacts/stage2/smoke.rrd
```

结果：`rerun rrd verify` 显示 1 个文件校验通过；`stats` 能看到 entity path、Transform3D、Image、Points3D、LineStrips3D、Scalars、TextLog 和多 timeline。

候选样本导出：

```bash
python3 scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/query_smoke --frames 24 --export-candidates --candidate-csv artifacts/stage2/query_smoke_candidates.csv
```

结果：生成高风险候选帧 CSV，样例包含 `porosity_risk` 事件和高于阈值的 `defect_probability`。

Importer 风格 CLI：

```bash
python3 scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/importer_smoke --frames 12
python3 scripts/rerun_importer_sim_weld.py --input-dir artifacts/stage2/importer_smoke --output-rrd artifacts/stage2/importer_smoke.rrd
rerun rrd verify artifacts/stage2/importer_smoke.rrd
```

结果：由已有模拟数据包写出的 `.rrd` 校验通过。

开源机器人数据对照：

```bash
python3 scripts/prepare_open_robot_sample.py --output-dir artifacts/stage2/open_robot_sample
```

结果：成功下载并读取 LeRobot PushT 一个小 parquet 文件，生成 32 行对照样本和 `source_metadata.json`。

Catalog/DataFrame 查询：

```bash
python3 scripts/evaluate_stage2_catalog.py --output-dir artifacts/stage2/catalog_smoke
```

结果：生成 2 个 recording，Catalog 和 Chunk 查询均返回结构化成功结果。

## 6. 模拟数据覆盖范围

模拟数据覆盖了阶段二需要的最小多模态闭环：

- 空间结构：`/station`、`/station/workpiece`、`/station/robot/base`、`/station/robot/base/tcp`、`/station/camera/front`、`/station/workpiece/weld/seam_001`。
- 坐标关系：工站、工件、机器人 base、相机和动态 TCP 位姿。
- 时间关系：仿真时间、机器人 tick、相机帧号和焊接阶段。
- 多模态数据：图像、点云、计划焊缝、实际轨迹、TCP 点、工艺参数、事件和质量标签。
- 质量信号：中段缺陷概率升高，并产生 `porosity_risk` 事件。

## 7. `.rrd` 写入结果

`.rrd` 写入链路已跑通，并通过 Rerun CLI 校验。当前 writer 采用临时文件加原子替换，避免写入失败时覆盖已有可用 recording。

已观察到 Rerun 对当前写入文件提示 legacy/no footer 相关 warning，但 `rerun rrd verify` 和 `rerun.experimental.RrdReader.stream()` 查询均可工作。该 warning 后续需要结合 Rerun SDK 推荐写入方式继续确认，不应在当前阶段解读为阻塞问题。

## 8. Viewer/Blueprint 检查状态

本轮已生成可供 Viewer 打开的 `.rrd`，并提供人工检查清单：

- `docs/stage2/viewer_blueprint_checklist.md`

当前尚未在 GUI Viewer 中完成视觉检查，因此不能声明 Blueprint 布局、3D 视图构图和多 timeline 交互已经人工验收。下一步需要按清单打开 `.rrd`，记录截图、布局保存结果和任何显示异常。

## 9. CSV 候选样本导出结果

候选样本导出已实现并验证。导出列包括：

`sim_time_s`、`robot_tick`、`camera_frame`、`weld_phase`、`tcp_x`、`tcp_y`、`tcp_z`、`weld_current`、`weld_voltage`、`wire_feed_speed`、`weld_speed`、`defect_probability`、`event`、`quality_label`、`image_file`。

该导出可作为后续人工复核、缺陷样本整理、模型评测样本筛选的最小入口。

## 10. Catalog 尝试结果

本地 Catalog 尝试结果为成功：

- 创建本地 Catalog table：`stage2_catalog_candidates`
- 查询返回行数：8
- 运行时服务地址示例：`rerun+http://127.0.0.1:51614`

当前结论仅限于本地单机实验。Catalog 的持久化、协作、多用户权限、远程部署和长期数据治理仍需后续单独验证。

## 11. DataFrame/Chunk 查询尝试结果

Rerun experimental RrdReader stream 查询结果为成功：

- 输入 `.rrd`：2 个
- 读取 chunks：21 个
- 查询返回行数：239

这说明本阶段可以从 `.rrd` 进入列式 chunk 查询路径。该能力仍属于实验验证结果，后续需要继续评估 API 稳定性、查询语义、性能边界和与训练导出流程的适配方式。

## 12. External Importer 原型结果

`scripts/rerun_importer_sim_weld.py` 已实现 external-importer-style 原型，功能包括：

- 校验输入目录存在；
- 校验 `manifest.json`、`frames.csv`、`point_cloud.csv`；
- 调用项目内 `write_rrd(input_dir, output_rrd)`；
- 输出可被 `rerun rrd verify` 校验的 `.rrd`。

本阶段没有实现 Rerun 完整 external importer 协议。当前脚本更适合作为自有现场数据包转 recording 的最小原型。

## 13. 开源机器人数据对照状态

本阶段选择 LeRobot PushT 作为公开机器人数据对照源：

- 数据集入口：`https://huggingface.co/datasets/lerobot/pusht`
- 实际下载文件：`data/train-00000-of-00001.parquet`
- 固定 revision：`aa68ad28f20ffd4c4b6fc0af7fde6e29d003bfdf`
- 读取行数：32
- 字段包括：`observation.image`、`observation.state`、`action`、`episode_index`、`frame_index`、`timestamp`、`next.reward`、`next.done`、`next.success`、`index`

该数据不是焊接数据，但可以作为机器人状态、动作、图像、时间戳字段组织方式的对照。真实焊接轨迹、工艺参数和质量标签仍需要后续寻找或自造更贴近业务的数据源。

## 14. 风险与限制

- 本阶段没有接入真机，不能验证现场采集、网络、时钟同步、控制器协议和工艺系统接口。
- Viewer GUI 和 Blueprint 尚未完成人工视觉验收。
- Catalog 结果仅限本地临时环境，不代表产品级数据管理能力。
- DataFrame/Chunk 查询路径涉及 experimental API，后续需要关注兼容性。
- LeRobot PushT 只能作为结构对照，不能代表机器人焊接业务。
- 当前尚未完成性能冒烟或压测，仅完成小规模功能验证；大规模点云、长视频、高频控制和多作业数据集仍需后续验证。

## 15. 对二次开发路线的影响

阶段二结果支持继续采用“先外围封装、暂不 fork Rerun”的路线：

- Python SDK、`.rrd`、Viewer、entity path、timeline、Transform、基础 archetype 值得继续直接复用；
- candidate CSV、数据包目录、external-importer-style CLI 适合沉淀为自有规范；
- Catalog 和 DataFrame/Chunk 查询值得继续验证，但暂不应作为产品级治理能力的唯一依赖；
- 工艺语义、质量标签、权限审计、数据分级、客户现场脱敏和长期数据资产管理仍应按自有数据层设计。

## 16. 下一步

1. 按 `docs/stage2/viewer_blueprint_checklist.md` 完成 Viewer/Blueprint 人工检查。
2. 补充阶段二性能冒烟，至少覆盖更长帧数、较大点云、图像序列写入、`.rrd` 文件体积和打开体验。
3. 补充一个更接近焊接或工业机器人的公开数据源；若找不到，则扩展模拟数据覆盖工艺异常和传感器噪声。
4. 设计 CavLAB 自有数据包 schema 草案，包括任务上下文、设备、工件、工艺、事件、质量和数据血缘。
5. 将 importer 原型升级为可配置的数据包转换器，但继续保持 Rerun 依赖隔离在外围。
6. 进入阶段三真实样板场景数据链路设计前，明确最小现场字段清单和验收样例。
