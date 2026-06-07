# 阶段二运行说明

本文档记录阶段二 Rerun.io 本地技术评测的默认运行路径。阶段二目标是在不接入真机、不引入 ROS/Gazebo/MoveIt 的前提下，用可重复生成的焊接工站模拟数据验证图像、点云、位姿、轨迹、事件、工艺参数、模型输出和候选样本导出的最小闭环。

## 安装

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 测试

```bash
python -m pytest
```

## 生成模拟数据包

```bash
python scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/sim_weld_001 --frames 120
```

该命令会生成阶段二模拟焊接数据包，包括 `manifest.json`、`frames.csv`、`point_cloud.csv` 和图像序列。

## 写 `.rrd`

```bash
python scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/sim_weld_001 --frames 120 --write-rrd --output-rrd artifacts/stage2/sim_weld_001.rrd
```

该命令会在生成模拟数据包后调用 Rerun writer，输出可用 Rerun Viewer 打开的 `.rrd` recording。

## 导出候选样本

```bash
python scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/sim_weld_001 --export-candidates --candidate-csv artifacts/stage2/candidate_rows.csv
```

候选样本用于快速筛选高风险帧，便于后续人工复核、标注和训练样本整理。

## Importer 风格 CLI

```bash
python scripts/rerun_importer_sim_weld.py --input-dir artifacts/stage2/sim_weld_001 --output-rrd artifacts/stage2/imported_sim_weld_001.rrd
```

该脚本是 external-importer-style 原型：它校验模拟数据包中的 `manifest.json`、`frames.csv`、`point_cloud.csv`，然后调用项目内的 `write_rrd(input_dir, output_rrd)` 写出 `.rrd`。本阶段不实现 Rerun 完整 external importer 协议。

## 已知限制

- 当前阶段不接入真机。
- 当前阶段不引入 ROS、Gazebo 或 MoveIt。
- Catalog 验证需要结合实际 Rerun 环境记录结果。
- Viewer 和 Blueprint 检查需要按实际 GUI 环境人工记录，不能用命令行测试结果替代人工观察。
