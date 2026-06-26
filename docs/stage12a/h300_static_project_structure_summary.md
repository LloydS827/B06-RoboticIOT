# H300 Static Project Redacted Structure Summary

本摘要只记录 Stage 12A 可提交的脱敏结构事实。原始工程包位于本地受控目录 `data/H300/<local-project-run>`，不进入仓库；真实 URL/IP/port、真实工程 basename、真实 operator/author 值、真实时间戳、图片、点云、Lua 和工程 JSON 内容均不在本文出现。

## Root

```text
data/H300/<local-project-run>/
```

该目录应被视为 Raw/source artifact root。仓库文档只引用这个占位路径，不引用真实目录名。

## Observed Structure

```text
data/H300/<local-project-run>/
  campcd_json/
    project_<redacted>.json
    project_<redacted>_campcd.json
  project_<redacted>_image/
    project_<redacted>_part_<index>.jpg
  project_<redacted>_point_cloud/
    project_<redacted>_part_<index>.pcd
  point_cloud/
    project_<redacted>.txt
  weld_seam/
    recipe_<redacted>.json
  <redacted>_lua_script/
    <program_id>.lua
  <redacted>_weld_config/
    <program_id>_flow.json
```

## Asset Counts

| Asset type | Redacted path pattern | Observed count / structure |
| --- | --- | --- |
| 工程主 JSON | `campcd_json/project_<redacted>.json` | 1 个，包含 `info`、`calibration`、`camera`、`photoPoses`、`pathPlan`、`extractPathPlan`、`processes`、`robot`、`runtime` 等对象 |
| 相机/点云索引 JSON | `campcd_json/project_<redacted>_campcd.json` | 1 个，包含 3 组 `pcdWithCam` 图像、点云和相机位姿引用，以及 ROI |
| 图片 | `project_<redacted>_image/project_<redacted>_part_<index>.jpg` | 3 张 1440x1080 RGB JPEG |
| PCD 点云 | `project_<redacted>_point_cloud/project_<redacted>_part_<index>.pcd` | 3 个 binary PCD 分片，header 字段为 `x y z`，合计约 135 万点 |
| 文本点云 | `point_cloud/project_<redacted>.txt` | 1 个裸 xyz 文本点云文件 |
| 焊缝 recipe | `weld_seam/recipe_<redacted>.json` | 1 个，包含 11 条 `weld_seams` |
| 规划数据 | `campcd_json/project_<redacted>.json` | `pathPlan` 11 条，`extractPathPlan` 11 条 |
| 程序文件 | `<redacted>_lua_script/<program_id>.lua` | Lua/ABB RAPID 风格程序，包含运动、焊接动作和目标点/工艺数据定义 |
| Flow config | `<redacted>_weld_config/<program_id>_flow.json` | 1 个，包含 22 个 flow step |

## Program Semantics

程序文件只作为结构摘要观察，不提交源码内容。允许记录的计数和类别包括：

- 运动指令类别：`MoveAbsJ`、`MoveL`。
- 焊接动作类别：`ArcMPL`，代表实际焊接动作。
- 控制指令类别：`Stop`。
- 目标点和工艺数据类别：`ROBTARGET`、`JOINTTARGET`、`SEAMDATA`、`WELDDATA`、`WEAVEDATA`、`MULTIPASSDATA`。

任何原始程序文本、真实程序编号、真实工程名或业务时间戳都应继续 local-only。

## Sensitivity Notes

Stage 12A inspector 和人工摘要应把以下内容视为不可提交或需 review：

- 真实工程 basename、目录名、业务时间戳或工单追踪线索。
- operator、author、reviewer 或 person-like 字段值。
- URL、IP、port、server、device id 和内部路径。
- Windows 或 POSIX 绝对路径。
- 图片内容、点云坐标、Lua 原文和工程 JSON 原始 payload。

提交物只能保留 risk type、field name、redacted path pattern、数量和结构类别。

## Gap Mapping Observations

| Gap | Stage 12A observation |
| --- | --- |
| G-001 | 工程主键、project name 和时间类字段只能作为追溯线索，不能等同工单主键。 |
| G-003 | PCD 分片和裸 xyz 点云存在，可为点云/PCL review 提供 source artifact，但需评审坐标系、标定版本和提交边界。 |
| G-004 | 图片、相机参数、手眼/标定字段存在，可为视觉 evidence 提供上下文，但图片和标定细节需脱敏策略确认。 |
| G-005 | 工程 JSON 或 recipe 中的模型/算法输出线索应先作为 source artifact，不直接结构化为 package 字段。 |
| G-006 | 如存在人工拖拽示教、微调或 review 信息，应先标记为 review，不结构化为 labels。 |
| G-007 | 焊接工艺配置和程序中的工艺数据能提供静态模板，不代表实时工艺采样。 |
| G-008 | 程序指令序列和 flow steps 可作为执行计划事件线索，不等同实时事件日志。 |
| G-010 | 离线下载、本地目录或控制面板线索提示部署存储边界，后续需要权限和保留策略。 |
| G-012 | 坐标系、TCP、相机位姿、工件 frame 和单位约定是 Stage 12A/12B 的重点决策输入。 |

## Stage 12A Conclusion

H300 静态工程包不是单纯作业窗口过程采样，而是一组连接视觉建模、点云、焊缝提取、路径规划、工艺配置和执行程序的工程模板资产。Stage 12A 应先输出 redacted-safe inspection JSON 与本文这类脱敏结构摘要；Stage 12B/13 再分别处理 Clean Zone draft readiness 和 realtime API readiness。
