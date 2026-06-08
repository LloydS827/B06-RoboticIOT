# 阶段三运行说明

本文档记录 Stage 3 simulation-first Physical AI 数据包原型的默认运行路径。阶段三目标是在不接入真机、不引入 ROS/Gazebo/MoveIt 的前提下，形成 CavLAB Physical AI 数据包 v0.1 的 runnable package、开发期 validator、Rerun adapter、两个仿真样例、候选样本导出和 CLI 原型。

## 安装

```bash
python3 -m pip install -e ".[dev]"
```

## 生成机器人焊接工站样例

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py generate welding --output-dir artifacts/stage3/weld_demo --frames 24
```

该命令生成 `robot_welding_station` 样例包，用于覆盖机器人焊接工站的任务上下文、设备、工件、坐标系、帧、事件、标签、指标和图像等最小数据结构。

## 生成机械臂抓取/分拣样例

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py generate pick-sort --output-dir artifacts/stage3/pick_sort_demo --frames 24
```

该命令生成 `arm_pick_sort` 轻量对照样例包，用于验证 schema 不只绑定焊接场景，也能表达另一类机械臂作业闭环。

## 校验数据包

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage3/weld_demo --json
PYTHONPATH=src python3 scripts/physical_ai_package.py validate artifacts/stage3/pick_sort_demo --json
```

`validate` 返回开发期诊断结果，包括错误、警告和基础 summary。返回码为 `0` 表示没有 error，返回码为 `1` 表示存在 error。

## 汇总数据包

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py summarize artifacts/stage3/weld_demo --json
PYTHONPATH=src python3 scripts/physical_ai_package.py summarize artifacts/stage3/pick_sort_demo --json
```

`summarize` 输出 package id、场景类型、帧数、事件数、标签数、指标数和候选样本数等概要信息。

## 导出候选样本

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage3/weld_demo
PYTHONPATH=src python3 scripts/physical_ai_package.py export-candidates artifacts/stage3/pick_sort_demo
```

默认输出为 `PACKAGE/derived/candidates.csv`。候选样本用于人工复核、问题定位、训练样本筛选和评测样本整理。

## 转换为 Rerun `.rrd`

```bash
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage3/weld_demo --output-rrd artifacts/stage3/weld_demo.rrd
PYTHONPATH=src python3 scripts/physical_ai_package.py convert-rerun artifacts/stage3/pick_sort_demo --output-rrd artifacts/stage3/pick_sort_demo.rrd
```

该命令通过 Rerun adapter backend 将 CavLAB 自有数据包转换为 `.rrd`，便于继续使用 Rerun Viewer 和 CLI 做开发期观察。

## 已知限制

- 当前阶段没有接入机器人硬件。
- 当前阶段没有引入 ROS、Gazebo 或 MoveIt。
- Rerun 只是 adapter backend，不是 CavLAB 业务 schema 本身。
- validator 是开发期诊断工具，不是生产级数据治理、权限审计或质量追溯系统。
- Viewer/Blueprint 人工检查和性能冒烟需要后续按实际环境补充记录。
