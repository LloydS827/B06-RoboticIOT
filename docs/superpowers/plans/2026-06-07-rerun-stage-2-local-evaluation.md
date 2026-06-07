# Rerun 阶段二本地技术评测实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立阶段二 Rerun.io 本地技术评测闭环，用 Python 生成模拟机器人焊接工站数据，写入 Rerun `.rrd`，验证 Viewer、坐标系、多 timeline、Catalog/DataFrame 查询、external-importer-style 导入和开源机器人数据对照。

**Architecture:** 第一轮只使用 Python 本地实现，不引入 ROS/Gazebo/MoveIt，不接真机。`rerun_stage2` 包负责生成确定性的模拟数据、写出本地数据包、调用 Rerun SDK 写 `.rrd`、导出候选训练/评测样本、尝试本地 Catalog/DataFrame 查询、下载并转换一个真实公开机器人数据小文件作为对照；`scripts/` 提供可运行 CLI；`docs/` 记录真实验证结果和限制。

**Tech Stack:** Python 3.11+、`pytest`、`numpy`、`pillow`、`pyarrow`、`rerun-sdk[dataplatform]>=0.33.0`、标准库 `csv/json/pathlib/subprocess`.

---

## 0. 上下文与边界

设计文档：`docs/superpowers/specs/2026-06-07-rerun-stage-2-local-evaluation-design.md`

项目要求：

- 计划、方案和项目文档使用中文。
- 保持最小可验证闭环，不做 speculative 平台化。
- 不接机器人真机。
- 不引入 ROS/Gazebo/MoveIt 作为第一轮依赖。
- Python 行为代码遵循 TDD：先写失败测试，再实现。
- 生成的 `.rrd`、PNG、CSV 输出放入 `artifacts/`，不提交到 git。
- 如果当前环境无法打开 Rerun Viewer 图形界面，必须记录“已生成 `.rrd`，Viewer 视觉检查待人工打开验证”，但仍要提供明确的 Viewer/Blueprint 检查清单和命令。

## 1. 文件结构

新增：

- `pyproject.toml`：项目元数据、依赖、pytest 配置。
- `src/rerun_stage2/__init__.py`：包版本。
- `src/rerun_stage2/sim_data.py`：模拟焊接工站数据模型、帧生成、点云生成、图片和数据包写入。
- `src/rerun_stage2/rerun_writer.py`：Rerun SDK 写入适配器，负责 `.rrd`、多 timeline、坐标系、点云、图像、轨迹、工艺参数和事件。
- `src/rerun_stage2/query_export.py`：从数据包导出训练/评测候选 CSV。
- `src/rerun_stage2/catalog_eval.py`：本地 Rerun Catalog 注册与查询尝试；Catalog 不可用时继续尝试 Rerun 原生 DataFrame/Chunk 查询路径；若二者均不可用，输出结构化失败记录。
- `src/rerun_stage2/open_dataset.py`：下载并转换一个真实公开机器人数据小文件，优先使用 LeRobot `pusht` parquet；网络或上游不可用时输出结构化失败记录。
- `scripts/generate_stage2_simulation.py`：生成模拟焊接数据包，可选写 `.rrd`、导出候选 CSV。
- `scripts/rerun_importer_sim_weld.py`：external-importer-style CLI，将已有数据包转为 `.rrd`。
- `scripts/evaluate_stage2_catalog.py`：生成两个 recording，尝试 Catalog 注册/查询，并在 Catalog 不可用时继续尝试 Rerun 原生 DataFrame/Chunk 查询路径。
- `scripts/prepare_open_robot_sample.py`：准备开源机器人对照样例包。
- `tests/rerun_stage2/test_sim_data.py`：模拟数据测试。
- `tests/rerun_stage2/test_query_export.py`：候选导出测试。
- `tests/rerun_stage2/test_cli_contracts.py`：CLI contract 测试。
- `tests/rerun_stage2/test_open_dataset.py`：开源数据对照元数据测试。
- `docs/stage2/README.md`：阶段二运行说明。
- `docs/stage2/viewer_blueprint_checklist.md`：Viewer 和 Blueprint 人工/半自动验证清单。
- `docs/research/04-rerun阶段二本地技术评测报告.md`：阶段二评测报告。

修改：

- `.gitignore`：忽略 `artifacts/`、`.rrd`、`.rbl`。
- `README.md`：补充阶段二实验入口。
- `details.md`：记录执行进展。
- `docs/research/03-rerun二次开发路线判断矩阵.md`：新增阶段二验证状态。

## Task 1：Python 工程骨架与模拟焊接数据模型

**Files:**

- Create: `pyproject.toml`
- Create: `src/rerun_stage2/__init__.py`
- Create: `src/rerun_stage2/sim_data.py`
- Create: `tests/rerun_stage2/test_sim_data.py`
- Modify: `.gitignore`

- [ ] **Step 1：写失败测试**

创建 `tests/rerun_stage2/test_sim_data.py`：

```python
from pathlib import Path

from rerun_stage2.sim_data import RecordingConfig, generate_frames, generate_point_cloud, write_simulation_package


def test_generate_frames_is_deterministic_and_contains_required_timelines():
    config = RecordingConfig(frame_count=8, random_seed=42)

    first = generate_frames(config)
    second = generate_frames(config)

    assert len(first) == 8
    assert [f.tcp_position for f in first] == [f.tcp_position for f in second]
    assert [f.weld_current for f in first] == [f.weld_current for f in second]
    assert first[0].event == "arc_start"
    assert any(frame.event == "porosity_risk" for frame in first)
    assert first[-1].event == "arc_end"
    assert {f.weld_phase for f in first} >= {"approach", "welding", "finish"}
    assert all(isinstance(f.robot_tick, int) for f in first)
    assert all(isinstance(f.camera_frame, int) for f in first)


def test_generate_point_cloud_is_deterministic_and_non_empty():
    config = RecordingConfig(frame_count=8, random_seed=42)

    points_a = generate_point_cloud(config)
    points_b = generate_point_cloud(config)

    assert points_a == points_b
    assert len(points_a) >= 40
    assert all(len(point) == 3 for point in points_a)


def test_write_simulation_package_creates_manifest_tables_images_and_point_cloud(tmp_path: Path):
    config = RecordingConfig(frame_count=6, random_seed=7)

    package = write_simulation_package(tmp_path / "sim_weld_001", config)

    assert package.root.exists()
    assert (package.root / "manifest.json").exists()
    assert (package.root / "frames.csv").exists()
    assert (package.root / "events.csv").exists()
    assert (package.root / "quality.json").exists()
    assert (package.root / "point_cloud.csv").exists()
    assert (package.root / "images").is_dir()
    assert len(list((package.root / "images").glob("*.png"))) == 6
```

- [ ] **Step 2：运行测试并确认失败**

Run:

```bash
python3 -m pytest tests/rerun_stage2/test_sim_data.py -q
```

Expected: FAIL，原因是 `rerun_stage2.sim_data` 不存在。

- [ ] **Step 3：新增工程配置**

创建 `pyproject.toml`，必须包含：

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "b06-physical-ai-data-layer"
version = "0.1.0"
description = "Stage 2 local Rerun evaluation for Physical AI data layer"
requires-python = ">=3.11"
dependencies = [
  "numpy>=1.26",
  "pillow>=10",
  "pyarrow>=16",
  "rerun-sdk[dataplatform]>=0.33.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

创建 `src/rerun_stage2/__init__.py`：

```python
"""Stage 2 local Rerun evaluation utilities."""

__version__ = "0.1.0"
```

- [ ] **Step 4：实现 `sim_data.py`**

实现以下对象和函数：

- `RecordingConfig` dataclass：
  - `frame_count: int = 120`
  - `duration_s: float = 12.0`
  - `random_seed: int = 42`
  - `image_width: int = 320`
  - `image_height: int = 180`
  - `workpiece_id: str = "wp_demo_001"`
  - `seam_id: str = "seam_001"`
  - `batch_id: str = "batch_stage2_demo"`
- `FrameSample` dataclass，至少包含：
  - `sim_time_s`
  - `robot_tick`
  - `camera_frame`
  - `weld_phase`
  - `tcp_position`
  - `tcp_quaternion`
  - `weld_current`
  - `weld_voltage`
  - `wire_feed_speed`
  - `weld_speed`
  - `defect_probability`
  - `event`
  - `quality_label`
  - `image_file`
- `SimulationPackage` dataclass：
  - `root`
  - `manifest_path`
  - `frames_csv`
  - `events_csv`
  - `quality_json`
  - `point_cloud_csv`
- `generate_frames(config) -> list[FrameSample]`
- `generate_point_cloud(config) -> list[tuple[float, float, float]]`
- `write_simulation_package(root, config) -> SimulationPackage`

行为要求：

- TCP 沿 x=-0.4 到 x=0.4 的微弯焊缝移动。
- `weld_phase` 至少包含 `approach`、`welding`、`finish`。
- 中间窗口出现更高 `defect_probability`，并产生 `porosity_risk` 事件。
- 首帧事件为 `arc_start`，末帧事件为 `arc_end`。
- 生成简化工件/焊缝点云 `point_cloud.csv`。
- 生成 PNG 图片，包含焊缝线和风险标记。
- `manifest.json` 必须写入 entity path 和坐标系约定：
  - `/world`
  - `/station`
  - `/station/workpiece`
  - `/station/robot/base`
  - `/station/robot/base/tcp`
  - `/station/camera/front`
  - `/station/workpiece/weld/seam_001`

- [ ] **Step 5：更新 `.gitignore`**

加入：

```gitignore
# Stage 2 generated artifacts
artifacts/
*.rrd
*.rbl
```

- [ ] **Step 6：运行测试并确认通过**

Run:

```bash
python3 -m pytest tests/rerun_stage2/test_sim_data.py -q
```

Expected: PASS.

- [ ] **Step 7：提交**

```bash
git add pyproject.toml .gitignore src/rerun_stage2/__init__.py src/rerun_stage2/sim_data.py tests/rerun_stage2/test_sim_data.py
git commit -m "Add stage 2 simulation data model"
```

## Task 2：Rerun 写入器、坐标系、多 timeline 与生成 CLI

**Files:**

- Create: `src/rerun_stage2/rerun_writer.py`
- Create: `scripts/generate_stage2_simulation.py`
- Create: `tests/rerun_stage2/test_cli_contracts.py`

- [ ] **Step 1：写失败测试**

创建 `tests/rerun_stage2/test_cli_contracts.py`：

```python
import os
import subprocess
import sys


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    return subprocess.run(
        [sys.executable, *args],
        check=False,
        text=True,
        capture_output=True,
        env=env,
    )


def test_generate_cli_help_runs():
    result = run_script("scripts/generate_stage2_simulation.py", "--help")

    assert result.returncode == 0
    assert "--output-dir" in result.stdout
    assert "--write-rrd" in result.stdout
    assert "--export-candidates" in result.stdout
```

- [ ] **Step 2：运行测试并确认失败**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/rerun_stage2/test_cli_contracts.py::test_generate_cli_help_runs -q
```

Expected: FAIL，原因是脚本不存在。

- [ ] **Step 3：实现 `rerun_writer.py`**

实现 `write_rrd(package_root: Path, output_rrd: Path) -> Path`。

要求：

- 函数内 lazy import `rerun as rr`，避免普通数据测试强依赖 Rerun import。
- 读取 `manifest.json`、`frames.csv`、`point_cloud.csv`。
- 调用：
  - `rr.init("b06_stage2_sim_weld", spawn=False)`
  - `rr.save(str(output_rrd))`
- 对每帧设置 timeline：
  - `rr.set_time_seconds("sim_time", frame.sim_time_s)`
  - `rr.set_time_sequence("robot_tick", frame.robot_tick)`
  - `rr.set_time_sequence("camera_frame", frame.camera_frame)`
  - `rr.set_time_sequence("weld_phase", phase_index)`
- 必须使用 `rr.Transform3D` 记录明确坐标树，不能只创建 entity path 或只记录点：
  - `/station` 相对 `/world` 的静态 transform；
  - `/station/workpiece` 相对 `/station` 的静态 transform；
  - `/station/robot/base` 相对 `/station` 的静态 transform；
  - `/station/camera/front` 相对 `/station` 的静态 transform；
  - `/station/workpiece/weld/seam_001` 相对 `/station/workpiece` 的静态 transform；
  - `/station/robot/base/tcp` 相对 `/station/robot/base` 的动态 transform，随每帧 TCP 位姿变化。
- Transform 验收标准：
  - `.rrd` 写入逻辑中至少包含上述 6 条 transform 路径；
  - `/station/robot/base/tcp` 每帧更新；
  - 如果 Rerun SDK 的 `Transform3D` 参数名与计划描述不同，worker 必须查询当前已安装 SDK 或官方 API 文档后使用正确参数；
  - 不得把“记录 TCP 点”当作 Transform 验证的替代。
- 必须记录：
  - 工件/焊缝简化点云：`rr.Points3D`
  - 规划/实际焊缝轨迹：`rr.LineStrips3D`
  - TCP 当前点或轨迹：`rr.Points3D` 或 `rr.LineStrips3D`
  - 相机图像：`rr.Image`
  - 工艺参数：`rr.Scalars`
  - 缺陷概率：`rr.Scalars`
  - 事件文本：`rr.TextLog` 或可用的最近似文本 archetype
- 如果某个 Rerun archetype 在当前 SDK 中不可用，使用最接近的稳定 archetype，并在代码注释和报告中记录限制。

- [ ] **Step 4：实现生成 CLI**

创建 `scripts/generate_stage2_simulation.py`。

要求：

- 脚本开头加入项目 `src` 路径，使 fresh checkout 中 `python scripts/...` 可运行：

```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
```

- 参数：
  - `--output-dir`
  - `--frames`
  - `--seed`
  - `--write-rrd`
  - `--output-rrd`
  - `--export-candidates`
  - `--candidate-csv`
- 先只调用 `write_simulation_package` 和可选 `write_rrd`；`--export-candidates` 在 Task 3 接通。
- 若用户传了 `--export-candidates` 但 Task 3 尚未实现，输出清晰错误并返回非零。

- [ ] **Step 5：运行测试和 smoke**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/rerun_stage2/test_cli_contracts.py::test_generate_cli_help_runs -q
python3 scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/smoke --frames 12
python3 scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/smoke --frames 12 --write-rrd --output-rrd artifacts/stage2/smoke.rrd
```

Expected:

- CLI help 测试 PASS。
- `artifacts/stage2/smoke` 数据包存在。
- 若 `rerun-sdk` 可用，`artifacts/stage2/smoke.rrd` 存在。
- 若 Rerun SDK/API 失败，记录错误，保持非 Rerun 数据生成可用。

- [ ] **Step 6：提交**

```bash
git add src/rerun_stage2/rerun_writer.py scripts/generate_stage2_simulation.py tests/rerun_stage2/test_cli_contracts.py
git commit -m "Add stage 2 Rerun recording writer"
```

## Task 3：候选样本导出与生成 CLI 接通

**Files:**

- Create: `src/rerun_stage2/query_export.py`
- Create: `tests/rerun_stage2/test_query_export.py`
- Modify: `scripts/generate_stage2_simulation.py`

- [ ] **Step 1：写失败测试**

创建 `tests/rerun_stage2/test_query_export.py`：

```python
import csv
from pathlib import Path

from rerun_stage2.query_export import export_candidate_rows
from rerun_stage2.sim_data import RecordingConfig, write_simulation_package


def test_export_candidate_rows_selects_high_risk_window(tmp_path: Path):
    package = write_simulation_package(
        tmp_path / "sim_weld_001",
        RecordingConfig(frame_count=20, random_seed=4),
    )
    output_csv = tmp_path / "candidate_rows.csv"

    written = export_candidate_rows(package.root, output_csv, min_defect_probability=0.55)

    rows = list(csv.DictReader(written.open(newline="", encoding="utf-8")))
    assert written == output_csv
    assert rows
    assert all(float(row["defect_probability"]) >= 0.55 for row in rows)
    assert {"sim_time_s", "tcp_x", "weld_current", "defect_probability", "event"}.issubset(rows[0])
```

- [ ] **Step 2：运行测试并确认失败**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/rerun_stage2/test_query_export.py -q
```

Expected: FAIL，原因是 `rerun_stage2.query_export` 不存在。

- [ ] **Step 3：实现 `query_export.py`**

实现 `export_candidate_rows(package_root: Path, output_csv: Path, min_defect_probability: float = 0.5) -> Path`：

- 读取 `frames.csv`。
- 过滤 `defect_probability >= min_defect_probability`。
- 写出稳定 CSV 列：
  - `sim_time_s`
  - `robot_tick`
  - `camera_frame`
  - `weld_phase`
  - `tcp_x`
  - `tcp_y`
  - `tcp_z`
  - `weld_current`
  - `weld_voltage`
  - `wire_feed_speed`
  - `weld_speed`
  - `defect_probability`
  - `event`
  - `quality_label`
  - `image_file`
- 只用标准库。文档中说明这是 Catalog/DataFrame 查询前的 CSV 候选样本导出基线。

- [ ] **Step 4：接通生成 CLI**

修改 `scripts/generate_stage2_simulation.py`：

- `--export-candidates` 调用 `export_candidate_rows`。
- `--candidate-csv` 默认 `artifacts/stage2/candidate_rows.csv`。

- [ ] **Step 5：运行测试和 smoke**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/rerun_stage2/test_query_export.py -q
python3 scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/query_smoke --frames 24 --export-candidates --candidate-csv artifacts/stage2/query_smoke_candidates.csv
```

Expected: tests PASS；candidate CSV 存在。

- [ ] **Step 6：提交**

```bash
git add src/rerun_stage2/query_export.py tests/rerun_stage2/test_query_export.py scripts/generate_stage2_simulation.py
git commit -m "Add stage 2 candidate query export"
```

## Task 4：External Importer 风格 CLI 与阶段二运行文档

**Files:**

- Create: `scripts/rerun_importer_sim_weld.py`
- Create: `docs/stage2/README.md`
- Create: `docs/stage2/viewer_blueprint_checklist.md`
- Modify: `tests/rerun_stage2/test_cli_contracts.py`
- Modify: `README.md`
- Modify: `details.md`

- [ ] **Step 1：写失败测试**

在 `tests/rerun_stage2/test_cli_contracts.py` 增加：

```python
def test_importer_cli_help_runs():
    result = run_script("scripts/rerun_importer_sim_weld.py", "--help")

    assert result.returncode == 0
    assert "--input-dir" in result.stdout
    assert "--output-rrd" in result.stdout
```

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/rerun_stage2/test_cli_contracts.py::test_importer_cli_help_runs -q
```

Expected: FAIL，原因是 importer 脚本不存在。

- [ ] **Step 2：实现 importer CLI**

创建 `scripts/rerun_importer_sim_weld.py`：

- 脚本开头加入 `src` 到 `sys.path`。
- 参数：
  - `--input-dir`
  - `--output-rrd`
- 校验 `manifest.json`、`frames.csv`、`point_cloud.csv` 存在。
- 调用 `write_rrd(input_dir, output_rrd)`。
- 缺文件时返回非零并打印清晰错误。

说明：本任务不实现 Rerun 完整 external importer 协议，只实现 external-importer-style 原型。

- [ ] **Step 3：写阶段二运行文档**

创建 `docs/stage2/README.md`，用中文说明：

- 阶段二目标；
- 安装：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

- 测试：

```bash
python -m pytest
```

- 生成模拟数据包：

```bash
python scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/sim_weld_001 --frames 120
```

- 写 `.rrd`：

```bash
python scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/sim_weld_001 --frames 120 --write-rrd --output-rrd artifacts/stage2/sim_weld_001.rrd
```

- 导出候选样本：

```bash
python scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/sim_weld_001 --export-candidates --candidate-csv artifacts/stage2/candidate_rows.csv
```

- importer 风格 CLI：

```bash
python scripts/rerun_importer_sim_weld.py --input-dir artifacts/stage2/sim_weld_001 --output-rrd artifacts/stage2/imported_sim_weld_001.rrd
```

- 已知限制：无真机、无 ROS/Gazebo、Catalog 和 Viewer 检查需按实际环境记录。

- [ ] **Step 4：写 Viewer/Blueprint 检查清单**

创建 `docs/stage2/viewer_blueprint_checklist.md`，用中文列出可执行检查：

- 生成 `.rrd`。
- 打开 Viewer：

```bash
rerun artifacts/stage2/sim_weld_001.rrd
```

- 检查：
  - 图像是否随时间变化；
  - 点云是否显示工件/焊缝；
  - `/world`、`/station`、`/station/workpiece`、`/station/robot/base`、`/station/robot/base/tcp`、`/station/camera/front`、`/station/workpiece/weld/seam_001` 路径是否存在；
  - 工艺参数曲线是否存在；
  - `porosity_risk` 事件附近 defect probability 是否升高；
  - `sim_time`、`robot_tick`、`camera_frame`、`weld_phase` 是否可用于定位；
  - 保存或记录 Blueprint 使用方式。
- 如果当前环境无法 GUI 打开，记录待人工检查，不冒充已完成。

- [ ] **Step 5：更新 README 和 details**

- README 文档目录加入 `docs/stage2/README.md`。
- details 记录 stage 2 implementation 已进入执行。

- [ ] **Step 6：运行测试并提交**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/rerun_stage2/test_cli_contracts.py -q
```

Expected: PASS.

Commit:

```bash
git add scripts/rerun_importer_sim_weld.py docs/stage2/README.md docs/stage2/viewer_blueprint_checklist.md tests/rerun_stage2/test_cli_contracts.py README.md details.md
git commit -m "Add stage 2 importer CLI and docs"
```

## Task 5：本地 Catalog/DataFrame 尝试与开源机器人对照样例

**Files:**

- Create: `src/rerun_stage2/catalog_eval.py`
- Create: `src/rerun_stage2/open_dataset.py`
- Create: `scripts/evaluate_stage2_catalog.py`
- Create: `scripts/prepare_open_robot_sample.py`
- Create: `tests/rerun_stage2/test_open_dataset.py`

- [ ] **Step 1：写失败测试**

创建 `tests/rerun_stage2/test_open_dataset.py`：

```python
import json
from pathlib import Path

from rerun_stage2.open_dataset import write_open_robot_sample


def test_write_open_robot_sample_creates_source_metadata_and_attempt_record(tmp_path: Path):
    sample = write_open_robot_sample(tmp_path / "open_robot_sample")

    metadata = json.loads((sample / "source_metadata.json").read_text(encoding="utf-8"))
    assert metadata["purpose"] == "stage2_open_robot_comparison"
    assert metadata["robot_family"]
    assert metadata["source_attempt"]["url"]
    assert metadata["source_attempt"]["status"] in {"downloaded", "not_available"}
    assert (sample / "frames.csv").exists()
    assert (sample / "images").is_dir()
```

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/rerun_stage2/test_open_dataset.py -q
```

Expected: FAIL，原因是 `rerun_stage2.open_dataset` 不存在。

- [ ] **Step 2：实现开源机器人对照样例**

实现 `src/rerun_stage2/open_dataset.py`：

- `write_open_robot_sample(root: Path) -> Path`
- 必须尝试下载一个真实公开机器人数据小文件，优先使用 LeRobot `pusht` parquet：
  - `https://huggingface.co/datasets/lerobot/pusht/resolve/aa68ad28f20ffd4c4b6fc0af7fde6e29d003bfdf/data/train-00000-of-00001.parquet`
  - 该文件约 736 KB，适合作为阶段二的小型真实机器人/操作数据结构对照。
- 下载成功时：
  - 将文件保存到 `source/lerobot_pusht_train-00000-of-00001.parquet`；
  - 使用 `pyarrow.parquet` 读取 schema 和前 32 行；
  - 从真实 parquet 中抽取可用的 time/index、state-like、action-like 字段，写入 `frames.csv`；
  - 若字段名与预期不同，worker 必须从 parquet schema 中选择最接近的数值/list 数值列并在 `source_metadata.json` 中记录映射；
  - 在 `source_metadata.json` 中记录 `source_attempt.status = "downloaded"`、原始 URL、schema 字段、字段映射和行数。
- 下载或读取失败时：
  - 将异常类型和消息写入 `source_metadata.json`，记录 `source_attempt.status = "not_available"`；
  - 失败不能静默吞掉；
  - 仍可生成占位 `frames.csv` 以保持命令可运行，但必须在 metadata 和报告中标记“真实开源数据对照未完成”。
- 生成对照样例包：
  - `source_metadata.json` 记录：
    - `purpose`
    - `robot_family`
    - `candidate_sources`，包含至少：
      - LeRobot pusht dataset: `https://huggingface.co/datasets/lerobot/pusht`
      - PickNik UR10e welding demo: `https://github.com/PickNikRobotics/UR10e_welding_demo`
      - LeRobot project/datasets: `https://github.com/huggingface/lerobot`
    - `source_attempt`
    - `limitation`: 第一轮只下载一个公开小型 parquet，不下载完整大数据集；焊接真实轨迹数据仍需后续补充。
  - `frames.csv` 包含真实来源的 timestamp/index、state-like 字段、action-like 字段；只有下载失败时才允许占位数据。
  - `images/` 包含少量生成图片。

实现 `scripts/prepare_open_robot_sample.py`：

- 脚本开头加入 `src` 到 `sys.path`。
- 参数 `--output-dir`。
- 调用 `write_open_robot_sample`。

- [ ] **Step 3：实现 Catalog 尝试脚本**

实现 `src/rerun_stage2/catalog_eval.py`：

- `run_catalog_smoke(root: Path) -> dict`
- 生成两个 simulated packages。
- 尝试使用 `rerun` 的本地 server/catalog API 注册或读取。参考官方文档中的 `rr.server.Server()`、`rr.catalog.CatalogClient(...)`、dataset/segment/query API；worker 必须以当前安装的 `rerun-sdk` 实际 API 为准。
- 如果 Catalog API 不可用或环境不支持，继续尝试 Rerun 原生 DataFrame/Chunk 查询路径：
  - 优先尝试从已生成 `.rrd` 或数据包中通过 Rerun SDK / DataFrame API 获取结构化 rows；
  - 如果当前 SDK 没有可用 DataFrame API，则记录 exact error；
  - 不允许只返回 CSV fallback 而不尝试 Rerun 原生查询路径。
- 返回结构必须包含 `catalog_attempt` 和 `dataframe_attempt` 两段。
- 如果 Catalog 或 DataFrame 任一成功，整体 status 为 `ok`：

```python
{
  "status": "ok",
  "catalog_attempt": {"status": "ok" | "not_available", "reason": "..."},
  "dataframe_attempt": {"status": "ok" | "not_available", "reason": "..."},
  "segments": 2,
  "queried_rows": ...
}
```

- 如果二者都不可用，返回：

```python
{
  "status": "not_available",
  "catalog_attempt": {"status": "not_available", "reason": "...exact error..."},
  "dataframe_attempt": {"status": "not_available", "reason": "...exact error..."},
  "fallback": "csv_candidate_export_verified"
}
```

实现 `scripts/evaluate_stage2_catalog.py`：

- 脚本开头加入 `src` 到 `sys.path`。
- 参数 `--output-dir`。
- 调用 `run_catalog_smoke`。
- 将结果写到 `catalog_eval_result.json`。

- [ ] **Step 4：运行测试和 smoke**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/rerun_stage2/test_open_dataset.py -q
python3 scripts/prepare_open_robot_sample.py --output-dir artifacts/stage2/open_robot_sample
python3 scripts/evaluate_stage2_catalog.py --output-dir artifacts/stage2/catalog_smoke
```

Expected:

- 测试 PASS。
- 开源机器人对照样例包存在。
- Catalog 结果 JSON 存在，状态为 `ok` 或 `not_available`，且必须包含 `catalog_attempt` 与 `dataframe_attempt`。
- 开源机器人对照样例必须包含 `source_attempt`；若网络可用，应下载真实 LeRobot `pusht` parquet 小文件并记录 schema/字段映射。

- [ ] **Step 5：提交**

```bash
git add src/rerun_stage2/catalog_eval.py src/rerun_stage2/open_dataset.py scripts/evaluate_stage2_catalog.py scripts/prepare_open_robot_sample.py tests/rerun_stage2/test_open_dataset.py
git commit -m "Add stage 2 catalog and open dataset probes"
```

## Task 6：评测报告、路线矩阵更新与最终验证

**Files:**

- Create: `docs/research/04-rerun阶段二本地技术评测报告.md`
- Modify: `docs/research/03-rerun二次开发路线判断矩阵.md`
- Modify: `details.md`

- [ ] **Step 1：写阶段二评测报告**

创建 `docs/research/04-rerun阶段二本地技术评测报告.md`，必须包含：

- 实验日期；
- 实验目标；
- 实验环境；
- 已实现内容；
- 已验证命令；
- 模拟数据覆盖范围；
- `.rrd` 写入结果；
- Viewer/Blueprint 检查结果或待人工检查说明；
- CSV 候选样本导出结果；
- Catalog 尝试结果；
- Rerun DataFrame/Chunk 查询尝试结果；
- external importer 原型结果；
- 开源机器人数据对照状态；
- 风险与限制；
- 对二次开发路线的影响；
- 下一步。

只写实际运行过的结论。没有跑通的能力必须写成“待验证”或“失败原因”，不能包装成完成。

- [ ] **Step 2：更新路线矩阵**

修改 `docs/research/03-rerun二次开发路线判断矩阵.md`，新增：

```markdown
## 7. 阶段二验证状态
```

至少记录：

- 模拟焊接工站数据模型：验证中/已验证；
- `.rrd` 写入：按实际结果记录；
- Viewer/Blueprint：按实际结果记录；
- CSV/DataFrame 候选样本导出：按实际结果记录；
- Catalog：按实际结果记录；
- DataFrame/Chunk 查询：按实际结果记录；
- External importer-style CLI：按实际结果记录；
- 开源机器人对照：按实际结果记录；
- 仍需阶段三真机/真实场景校正的内容。

- [ ] **Step 3：更新 details**

记录：

- 已完成的阶段二任务；
- 实际通过的验证命令；
- 下一步仍需处理的事项。

- [ ] **Step 4：最终验证**

Run:

```bash
PYTHONPATH=src python3 -m pytest -q
python3 scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/final_smoke --frames 16 --export-candidates --candidate-csv artifacts/stage2/final_smoke_candidates.csv
python3 scripts/generate_stage2_simulation.py --output-dir artifacts/stage2/final_smoke --frames 16 --write-rrd --output-rrd artifacts/stage2/final_smoke.rrd
python3 scripts/rerun_importer_sim_weld.py --input-dir artifacts/stage2/final_smoke --output-rrd artifacts/stage2/final_importer_smoke.rrd
python3 scripts/prepare_open_robot_sample.py --output-dir artifacts/stage2/final_open_robot_sample
python3 scripts/evaluate_stage2_catalog.py --output-dir artifacts/stage2/final_catalog_smoke
```

Expected:

- pytest PASS。
- 数据包存在。
- candidate CSV 存在。
- `.rrd` 存在，除非 Rerun SDK/API 在环境中失败；失败时报告必须记录 exact error。
- importer 输出 `.rrd` 存在，或记录同一 Rerun 失败原因。
- open robot sample 存在。
- catalog eval JSON 存在，状态为 `ok` 或 `not_available`。
- catalog eval JSON 必须显示 Catalog 和 DataFrame/Chunk 两条路径都尝试过。
- open robot sample 必须显示真实公开 demo 小文件下载成功，或记录 exact failure。

- [ ] **Step 5：提交**

```bash
git add docs/research/04-rerun阶段二本地技术评测报告.md docs/research/03-rerun二次开发路线判断矩阵.md details.md
git commit -m "Document stage 2 evaluation results"
```

## 最终集成要求

- [ ] 不提交 `artifacts/`、`.rrd`、`.rbl`、生成 PNG 或候选 CSV。
- [ ] Run:

```bash
git status --short --branch
PYTHONPATH=src python3 -m pytest -q
```

- [ ] 确认所有实现提交都在 `main`。
- [ ] 推送到 `origin/main`。
