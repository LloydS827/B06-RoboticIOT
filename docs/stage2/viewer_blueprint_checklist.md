# Viewer 与 Blueprint 检查清单

本文档用于记录阶段二 `.rrd` 在 Rerun Viewer 中的人工检查步骤。若当前环境无法打开 GUI，应记录为待人工检查，不冒充已完成。

## 准备 `.rrd`

```bash
python scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/sim_weld_001 --frames 120 --write-rrd --output-rrd artifacts/stage2/sim_weld_001.rrd
```

## 打开 Viewer

```bash
rerun artifacts/stage2/sim_weld_001.rrd
```

## 检查项

- 图像是否随时间变化。
- 点云是否显示工件和焊缝。
- 以下路径是否存在：
  - `/world`
  - `/station`
  - `/station/workpiece`
  - `/station/robot/base`
  - `/station/robot/base/tcp`
  - `/station/camera/front`
  - `/station/workpiece/weld/seam_001`
- 工艺参数曲线是否存在，包括焊接电流、焊接电压、送丝速度和焊接速度。
- `porosity_risk` 事件附近的 defect probability 是否升高。
- `sim_time`、`robot_tick`、`camera_frame`、`weld_phase` 是否可用于定位和跳转。
- 保存或记录 Blueprint 使用方式，包括视图布局、时间轴选择、关键路径展开状态和后续复现步骤。

## 记录要求

- 能打开 GUI 时，记录实际观察结果、Rerun 版本、`.rrd` 文件路径和 Blueprint 使用方式。
- 无法打开 GUI 时，记录“待人工检查”及原因，例如远程环境无图形界面或本机未安装 Rerun Viewer。
- 不用命令行测试通过结果替代 Viewer 视觉检查。
