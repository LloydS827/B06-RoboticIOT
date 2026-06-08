# Physical AI 数据包阶段三实施记录

## 1. 阶段目标

阶段三目标是在 simulation-first 路线下，把 Physical AI 数据层从 Rerun 技术评测推进到自有数据包原型：定义 CavLAB Physical AI package v0.1，提供可运行的 schema/validator、两个仿真样例、候选样本导出、Rerun adapter 和 CLI，形成后续样板场景闭环的默认入口。

本阶段不接真机，不引入 ROS/Gazebo/MoveIt，不把 Rerun 作为业务 schema，只把它作为开发期观察和回放的 adapter backend。

## 2. 已实现能力

- 新增 `physical_ai_data` Python package，承载 Stage 3 数据包 schema、IO、validator、样例生成、候选导出、Rerun adapter 和 CLI。
- 定义 `physical-ai-package/v0.1`，支持 `robot_welding_station` 和 `arm_pick_sort` 两类仿真场景。
- 实现开发期 validator，检查 manifest、表结构、时间戳、引用文件、坐标系、timeline、对象引用和推荐 artifact 目录。
- 实现机器人焊接工站仿真样例和机械臂抓取/分拣仿真样例。
- 实现候选样本导出，默认写入 `derived/candidates.csv`。
- 实现 Rerun adapter，将通过校验的数据包转换为 `.rrd`。
- 实现 `scripts/physical_ai_package.py` CLI，覆盖 generate、validate、summarize、export-candidates 和 convert-rerun。

## 3. 验证命令

安装：

```bash
python3 -m pip install -e ".[dev]"
```

单元测试：

```bash
PYTHONPATH=src python3 -m pytest -q
```

最终 smoke 命令：

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py generate welding --output-dir artifacts/stage3/final_weld --frames 24
PYTHONPATH=src python3 scripts/physical_ai_package.py generate pick-sort --output-dir artifacts/stage3/final_pick_sort --frames 24
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage3/final_weld --json
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage3/final_pick_sort --json
PYTHONPATH=src python3 scripts/physical_ai_package.py summarize artifacts/stage3/final_weld --json
PYTHONPATH=src python3 scripts/physical_ai_package.py summarize artifacts/stage3/final_pick_sort --json
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage3/final_weld
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage3/final_pick_sort
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage3/final_weld --output-rrd artifacts/stage3/final_weld.rrd
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage3/final_pick_sort --output-rrd artifacts/stage3/final_pick_sort.rrd
rerun rrd verify artifacts/stage3/final_weld.rrd
rerun rrd verify artifacts/stage3/final_pick_sort.rrd
```

smoke 结果：待最终烟测后更新。

## 4. 两个仿真样例说明

`robot_welding_station` 是阶段三主样例，用于表达机器人焊接工站中的任务、设备、工件、坐标系、TCP 轨迹、图像、事件、质量标签和过程指标。它承接阶段二焊接工站模拟数据，但以 CavLAB 自有 package schema 组织。

`arm_pick_sort` 是轻量对照样例，用于验证 schema 是否能表达不同作业类型。该样例覆盖机械臂抓取/分拣过程中的帧、对象状态、事件、标签、指标和图像引用，避免阶段三模型过早固化为焊接专用格式。

## 5. validator 结果

validator 已实现为开发期诊断入口，覆盖缺失 manifest、schema version、必需字段、必需表列、非数值/非有限数值、缺失 artifact 引用、缺失 `sim_time`、坐标系引用、对象引用和推荐目录 warning 等检查。

已知单元测试覆盖 validator 的正常包和多类失败路径。最终 smoke 中两个样例包的实际 `validate --json` 输出待最终烟测后更新。

## 6. Rerun adapter 结果

Rerun adapter 已实现为 backend adapter：输入通过 validator 的 CavLAB package，输出 `.rrd`，用于开发期回放和观察。它不改变 CavLAB package schema，也不把 Rerun 数据模型作为业务数据模型。

`.rrd` 文件生成和 `rerun rrd verify` 的最终结果待最终烟测后更新。Viewer/Blueprint 人工检查尚未完成，本文不声明 GUI 视觉验收结果。

## 7. 候选导出结果

候选导出已实现，默认输出 `PACKAGE/derived/candidates.csv`。导出逻辑从事件、标签和指标中整理候选帧，合并同一帧的多来源原因，为人工复核、训练样本筛选和评测样本整理提供最小入口。

两个最终样例包的候选 CSV 文件存在性、行数和样例内容待最终烟测后更新。

## 8. 风险与限制

- 当前阶段没有接入真实机器人硬件，不能验证控制器协议、现场网络、时钟同步和真实工艺系统接入。
- 当前阶段没有 ROS/Gazebo/MoveIt，不代表完整机器人仿真栈能力。
- Rerun 仅作为 adapter backend，后续仍需保持 CavLAB schema 与可视化后端解耦。
- validator 是开发期诊断，不是生产级数据治理、权限审计、脱敏、质量追溯或长期数据资产管理系统。
- Viewer/Blueprint 人工检查尚未完成。
- 性能冒烟尚未完成，长作业、大图像、高频控制、大点云和多包批处理仍需单独验证。

## 9. 下一步

1. 执行最终 smoke，并回填 validator、Rerun adapter 和候选导出的实际结果。
2. 按真实输出校准 Stage 3 文档，避免运行说明和 CLI 行为漂移。
3. 补充 Viewer/Blueprint 人工检查，记录 GUI 观察结果、截图和布局问题。
4. 补充性能冒烟，覆盖更长帧数、更大 artifact 和 `.rrd` 体积。
5. 进入阶段四，围绕自有规范、SDK wrapper、importer 边界、数据包目录规范和后端替换边界继续收敛。
