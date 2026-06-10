# Stage 4.1 LeRobot 真实数据 Smoke 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用项目独立 `uv` 环境，把真实 LeRobot PushT 与 ALOHA 数据跑通到 Physical AI Package 的导入、校验、候选导出、Rerun 转换和 `.rrd` 验证链路。

**Architecture:** Stage 4.1 作为现有 Stage 4 adapter 之上的真实数据验证与映射校准层。使用 `uv` 隔离真实 LeRobot 依赖，先跑 quick real-data smoke，只有真实字段证明不兼容时才最小修补 loader/profile/Rerun 兼容性。默认测试和默认非 LeRobot workflow 必须保持可用。

**Tech Stack:** Python 3.11+、`uv`、现有 `physical_ai_data` package、可选 `lerobot`、Hugging Face dataset access、`rerun-sdk`、`pytest`、stdlib `json/csv/pathlib/subprocess`。

---

## 0. Spec 与范围

Spec：

- `docs/superpowers/specs/2026-06-09-lerobot-real-data-smoke-design.md`

现有 Stage 4 参考文件：

- `docs/stage4/README.md`
- `docs/research/06-lerobot开放数据样板链路记录.md`
- `docs/research/06-lerobot到physical-ai-package映射.md`
- `src/physical_ai_data/lerobot_loader.py`
- `src/physical_ai_data/lerobot_adapter.py`
- `src/physical_ai_data/lerobot_profiles.py`
- `src/physical_ai_data/rerun_adapter.py`
- `scripts/physical_ai_package.py`

完成口径是严格的：

- PushT quick smoke 必须实际通过完整共享验证链路。
- ALOHA representative smoke 必须实际通过完整共享验证链路，并保持多相机代表性。
- PushT full acceptance 在资源允许时尝试，但不是完成所必需。
- PushT quick 或 ALOHA smoke 的外部阻塞需要记录，但不能算完成。

## 1. 文件结构

可能新增：

- `uv.lock`：由 `uv sync` 生成的项目锁文件。

可能修改：

- `pyproject.toml`：仅当真实依赖解析需要保守调整 LeRobot/版本范围时修改。
- `src/physical_ai_data/lerobot_loader.py`：真实 LeRobot API/字段兼容修补。
- `src/physical_ai_data/lerobot_adapter.py`：仅修补真实 LeRobot 写包暴露的问题。
- `src/physical_ai_data/lerobot_profiles.py`：仅做保守 profile 校准。
- `src/physical_ai_data/rerun_adapter.py`：仅修补真实多相机 `.rrd` 回放问题。
- `tests/physical_ai_data/test_lerobot_loader.py`：为真实字段/API 差异补 fake fixture 测试。
- `tests/physical_ai_data/test_lerobot_adapter.py`：必要时补写包回归测试。
- `tests/physical_ai_data/test_rerun_adapter.py`：必要时补多相机 Rerun 回归测试。
- `docs/stage4/README.md`：命令或环境说明变化时更新。
- `docs/research/06-lerobot开放数据样板链路记录.md`：记录环境、命令、结果和失败。
- `docs/research/06-lerobot到physical-ai-package映射.md`：根据真实字段校准 mapping。
- `details.md`：记录 Stage 4.1 状态和下一步。

不要提交：

- `.venv/`
- `artifacts/`
- 下载的数据集
- `.rrd`
- 截图或生成的候选 CSV
- Hugging Face 或 LeRobot cache

## Task 1: 建立 `uv` 环境与基线

**Files:**

- Create: `uv.lock`
- Modify: `docs/research/06-lerobot开放数据样板链路记录.md`
- Modify: `details.md`
- Modify: `.gitignore` only if generated cache paths appear inside the repo and are not already ignored.

- [ ] **Step 1: 检查当前工作区**

Run:

```bash
git status --short
```

Expected: 工作区干净，或只有明确已知的用户改动。不要回滚无关改动。

- [ ] **Step 2: 确认 `uv` 可用**

Run:

```bash
command -v uv
uv --version
```

Expected: 两个命令都通过。把 `uv` 版本记录到 `docs/research/06-lerobot开放数据样板链路记录.md`。

- [ ] **Step 3: 创建或刷新项目环境**

Run:

```bash
uv sync --extra dev --extra lerobot
```

Expected: `.venv/` 存在，`uv.lock` 创建或更新。如果依赖解析失败，记录准确命令和错误，然后把本任务标记为阻塞；不要标记 Stage 4.1 完成。

- [ ] **Step 4: 记录运行版本、真实 cache 路径和磁盘状态**

Run:

```bash
uv run python --version
uv run python - <<'PY'
import os
from importlib import import_module, metadata
from pathlib import Path

for package in ("lerobot", "rerun-sdk", "datasets", "huggingface_hub"):
    try:
        print(f"{package}=={metadata.version(package)}")
    except metadata.PackageNotFoundError:
        print(f"{package}: not installed")

for path in (
    "lerobot.datasets.lerobot_dataset",
    "lerobot.common.datasets.lerobot_dataset",
):
    try:
        module = import_module(path)
        print(f"LeRobotDataset import path OK: {path} -> {module.LeRobotDataset}")
    except Exception as exc:
        print(f"LeRobotDataset import path failed: {path}: {type(exc).__name__}: {exc}")

for env_name in ("HF_HOME", "HF_HUB_CACHE", "HF_DATASETS_CACHE", "LEROBOT_HOME", "LEROBOT_DATA_HOME"):
    print(f"{env_name}={os.environ.get(env_name, '')}")

cache_paths = []
try:
    from huggingface_hub.constants import HF_HOME, HF_HUB_CACHE
    print(f"huggingface_hub.HF_HOME={HF_HOME}")
    print(f"huggingface_hub.HF_HUB_CACHE={HF_HUB_CACHE}")
    cache_paths.extend([Path(HF_HOME), Path(HF_HUB_CACHE)])
except Exception as exc:
    print(f"huggingface_hub cache constants unavailable: {type(exc).__name__}: {exc}")

try:
    import datasets.config as datasets_config
    print(f"datasets.HF_DATASETS_CACHE={datasets_config.HF_DATASETS_CACHE}")
    cache_paths.append(Path(datasets_config.HF_DATASETS_CACHE))
except Exception as exc:
    print(f"datasets cache constants unavailable: {type(exc).__name__}: {exc}")

for env_name in ("HF_HOME", "HF_HUB_CACHE", "HF_DATASETS_CACHE", "LEROBOT_HOME", "LEROBOT_DATA_HOME"):
    value = os.environ.get(env_name)
    if value:
        cache_paths.append(Path(value))

cache_paths.extend([Path.home() / ".cache" / "huggingface", Path.home() / ".cache" / "lerobot"])
seen = set()
for path in cache_paths:
    resolved = path.expanduser()
    key = str(resolved)
    if key in seen:
        continue
    seen.add(key)
    print(f"CACHE_PATH\t{resolved}\texists={resolved.exists()}")
PY
df -h .
```

Expected: 能看到 Python 版本、LeRobot 版本、Rerun SDK 版本、至少一个可用的 `LeRobotDataset` import path、真实解析出的 Hugging Face/LeRobot cache 路径，以及当前磁盘可用性。把结果记录到 Stage 4 链路记录。

- [ ] **Step 5: 探测 Hugging Face 网络与数据集 metadata 可访问性**

Run:

```bash
uv run python - <<'PY'
from huggingface_hub import HfApi

api = HfApi()
for repo_id in ("lerobot/pusht", "lerobot/aloha_sim_transfer_cube_human"):
    try:
        info = api.dataset_info(repo_id)
        siblings = getattr(info, "siblings", []) or []
        print(f"HF_DATASET_OK\t{repo_id}\tsha={getattr(info, 'sha', '')}\tfiles={len(siblings)}")
    except Exception as exc:
        print(f"HF_DATASET_FAILED\t{repo_id}\t{type(exc).__name__}: {exc}")
PY
```

Expected: 两个 repo 的 metadata 查询至少能返回明确结果。若网络、权限或上游不可用，记录 exact error；PushT quick/ALOHA smoke 仍未实际通过前，Stage 4.1 不能完成。

- [ ] **Step 6: 在 `uv` 环境内运行默认回归测试**

Run:

```bash
uv run python -m pytest -q
```

Expected: 所有现有测试通过。如果因为真实 LeRobot 改变了可选依赖行为导致失败，先写 focused failing test，再改生产代码。

- [ ] **Step 7: 验证默认非 LeRobot 开发路径仍可用**

Use the system/default Python path, not `.venv`, to confirm the default workflow still does not require LeRobot:

```bash
python3 -m pip install -e ".[dev]"
PYTHONPATH=src python3 -m pytest -q
```

Expected: 默认安装不安装 `lerobot` extra 也能成功，测试套件不依赖网络或 LeRobot 也能通过。如果本机系统环境受外部管理导致命令失败，记录准确原因并运行最接近的非 LeRobot 检查；不要把默认依赖改成包含 LeRobot。

- [ ] **Step 8: 按真实解析路径统计 sync 后 cache/环境占用**

Run:

```bash
uv run python - <<'PY' > /tmp/stage4_1_cache_paths.txt
import os
from pathlib import Path

paths = []
try:
    from huggingface_hub.constants import HF_HOME, HF_HUB_CACHE
    paths.extend([Path(HF_HOME), Path(HF_HUB_CACHE)])
except Exception:
    pass
try:
    import datasets.config as datasets_config
    paths.append(Path(datasets_config.HF_DATASETS_CACHE))
except Exception:
    pass
for env_name in ("HF_HOME", "HF_HUB_CACHE", "HF_DATASETS_CACHE", "LEROBOT_HOME", "LEROBOT_DATA_HOME"):
    value = os.environ.get(env_name)
    if value:
        paths.append(Path(value))
paths.extend([Path.home() / ".cache" / "huggingface", Path.home() / ".cache" / "lerobot"])
for path in dict.fromkeys(str(path.expanduser()) for path in paths):
    print(path)
PY
while IFS= read -r cache_path; do
  test -n "$cache_path" && du -sh "$cache_path" 2>/dev/null || true
done < /tmp/stage4_1_cache_paths.txt
du -sh .venv 2>/dev/null || true
df -h .
```

Expected: 命令按真实解析出的 cache 路径报告占用；路径不存在时不报错。记录已有路径的占用、缺失路径和磁盘状态。

- [ ] **Step 9: 更新环境基线文档**

Edit `docs/research/06-lerobot开放数据样板链路记录.md`:

- 新增 `Stage 4.1 uv 环境` 小节。
- 记录 `uv` 版本、Python 版本、LeRobot 版本、Rerun 版本、可用 `LeRobotDataset` import path、Hugging Face dataset metadata 网络探测结果、真实解析 cache 路径、cache/`.venv` 占用、磁盘可用性、默认非 LeRobot workflow 结果和 `uv` 测试结果。
- 说明 `.venv/`、下载数据和 cache 都是本地生成状态，不提交。

Edit `details.md`:

- Add a Stage 4.1 in-progress note.
- Mention that the project now uses an independent `uv` environment for real LeRobot smoke.

- [ ] **Step 10: 提交**

Run:

```bash
git add uv.lock docs/research/06-lerobot开放数据样板链路记录.md details.md
git status --short
git commit -m "Set up uv environment for LeRobot real data smoke"
```

Expected: commit succeeds. Include `.gitignore` or `pyproject.toml` only if they were intentionally changed.

## Task 2: Run Real LeRobot Loader Preflight and Patch Compatibility

**Files:**

- Modify: `src/physical_ai_data/lerobot_loader.py` if real API/field differences require it.
- Modify: `src/physical_ai_data/lerobot_adapter.py` only if real package writing fails.
- Modify: `tests/physical_ai_data/test_lerobot_loader.py`
- Modify: `tests/physical_ai_data/test_lerobot_adapter.py` only if package writing fails.
- Modify: `docs/research/06-lerobot到physical-ai-package映射.md`
- Modify: `docs/research/06-lerobot开放数据样板链路记录.md`

- [ ] **Step 1: Add a temporary preflight command, not committed**

Run:

```bash
uv run python - <<'PY'
from physical_ai_data.lerobot_loader import load_lerobot_episode

for repo_id, profile, max_frames in [
    ("lerobot/pusht", "pusht", 3),
    ("lerobot/aloha_sim_transfer_cube_human", "aloha", 2),
]:
    print(f"=== {repo_id} ===")
    episode = load_lerobot_episode(
        repo_id=repo_id,
        episode_index=0,
        profile=profile,
        max_frames=max_frames,
    )
    print("fps:", episode.fps)
    print("profile:", episode.profile)
    print("task:", episode.task_name)
    print("features keys:", sorted(str(key) for key in episode.features)[:20])
    print("stats keys:", sorted(str(key) for key in episode.stats)[:20])
    print("frames:", len(episode.frames))
    if episode.frames:
        frame = episode.frames[0]
        print("frame_index:", frame.frame_index)
        print("timestamp_s:", frame.timestamp_s)
        print("image cameras:", sorted(frame.images))
        print("state dims:", len(frame.state))
        print("action dims:", len(frame.action))
PY
```

Expected: both repos load a small number of frames. If either fails, capture the full error and continue with TDD fixes.

- [ ] **Step 2: If loader fails, write the smallest fake-fixture test**

Modify `tests/physical_ai_data/test_lerobot_loader.py`.

Example patterns:

```python
def test_loader_handles_real_lerobot_episode_dict_shape(monkeypatch):
    # Build a fake dataset row that matches the real failing shape.
    # Assert load_lerobot_episode returns LeRobotFrame with expected timestamp/state/action/images.
```

or:

```python
def test_loader_accepts_real_lerobot_dataset_constructor_signature(monkeypatch):
    # Build a fake LeRobotDataset class with the real constructor behavior.
    # Assert load_lerobot_episode can open it.
```

Expected: the new test fails before production changes.

- [ ] **Step 3: Run the focused failing test**

Run:

```bash
uv run python -m pytest tests/physical_ai_data/test_lerobot_loader.py -q
```

Expected: FAIL for the new real-field incompatibility.

- [ ] **Step 4: Implement the minimal compatibility fix**

Modify `src/physical_ai_data/lerobot_loader.py` only enough to pass the new test and preserve existing fake tests.

Allowed fix areas:

- Current or legacy `LeRobotDataset` import path.
- Constructor signature fallback.
- Real `hf_dataset` row keys for episode index, frame index, timestamp, task, state, action, image fields.
- Real image values as PIL image, numpy/torch arrays, path strings, decoded video frames, or path-like objects.
- Metadata normalization for `features`, `stats`, `episodes`, and `tasks`.

Do not infer success/failure labels, robot calibration, camera extrinsics, or ALOHA dual-arm semantics.

- [ ] **Step 5: Re-run tests**

Run:

```bash
uv run python -m pytest tests/physical_ai_data/test_lerobot_loader.py tests/physical_ai_data/test_lerobot_adapter.py -q
uv run python -m pytest -q
```

Expected: all pass.

- [ ] **Step 6: Re-run preflight**

Run the same preflight command from Step 1.

Expected: both PushT and ALOHA load at least one real frame with usable timestamp/state/action and any available image cameras. Record observed field names and dimensions in the mapping document.

- [ ] **Step 7: Update mapping and chain record**

Edit `docs/research/06-lerobot到physical-ai-package映射.md`:

- Add observed real field names for PushT and ALOHA.
- Add any real differences from fake tests.
- Keep “不推断字段” conservative.

Edit `docs/research/06-lerobot开放数据样板链路记录.md`:

- Add preflight command result.
- Include repo id, episode index, max frames, frame count, camera names, state/action dimensions, and any fix made.

- [ ] **Step 8: Commit**

Run:

```bash
git add src/physical_ai_data/lerobot_loader.py src/physical_ai_data/lerobot_adapter.py tests/physical_ai_data/test_lerobot_loader.py tests/physical_ai_data/test_lerobot_adapter.py docs/research/06-lerobot到physical-ai-package映射.md docs/research/06-lerobot开放数据样板链路记录.md
git status --short
git commit -m "Calibrate LeRobot loader against real dataset fields"
```

Expected: commit includes only files that actually changed.

## Task 3: PushT Quick Smoke Full Verification

**Files:**

- Modify: `src/physical_ai_data/lerobot_loader.py` only if PushT exposes a new focused compatibility bug.
- Modify: `src/physical_ai_data/lerobot_adapter.py` only if package writing fails on real PushT data.
- Modify: `tests/physical_ai_data/test_lerobot_loader.py` or `tests/physical_ai_data/test_lerobot_adapter.py` for any code fix.
- Modify: `docs/research/06-lerobot开放数据样板链路记录.md`
- Modify: `docs/research/06-lerobot到physical-ai-package映射.md` if mapping changes.

- [ ] **Step 1: Remove old generated PushT quick artifacts**

Run:

```bash
rm -rf artifacts/stage4/pusht_quick_episode_0000 artifacts/stage4/pusht_quick_episode_0000.rrd
```

Expected: no committed files are removed because `artifacts/` is generated output.

- [ ] **Step 2: Run PushT quick import**

Run:

```bash
uv run python scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/pusht \
  --episode-index 0 \
  --output-dir artifacts/stage4/pusht_quick_episode_0000 \
  --profile pusht \
  --max-frames 120
```

Expected: command exits 0 and writes `artifacts/stage4/pusht_quick_episode_0000/physical_ai_manifest.json`.

- [ ] **Step 3: If PushT import fails, reproduce with a unit test**

If failure is due to code compatibility, add or update a fake-fixture test in `tests/physical_ai_data/`.

Run the focused test and confirm it fails:

```bash
uv run python -m pytest tests/physical_ai_data/test_lerobot_loader.py -q
```

Expected: FAIL before code fix.

- [ ] **Step 4: Patch the smallest PushT compatibility issue**

Modify only the file required by the failure:

- loader issue: `src/physical_ai_data/lerobot_loader.py`
- package writing issue: `src/physical_ai_data/lerobot_adapter.py`
- candidate export issue: only if real PushT exposes an existing `export-candidates` bug, add a focused test in `tests/physical_ai_data/test_candidates.py` and then patch `src/physical_ai_data/candidates.py`
- Rerun issue discovered later: `src/physical_ai_data/rerun_adapter.py`

Expected: no schema expansion and no speculative profile logic.

- [ ] **Step 5: Re-run PushT import and tests**

Run:

```bash
uv run python -m pytest -q
uv run python scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/pusht \
  --episode-index 0 \
  --output-dir artifacts/stage4/pusht_quick_episode_0000 \
  --profile pusht \
  --max-frames 120
```

Expected: tests pass and PushT quick import exits 0.

- [ ] **Step 6: Validate PushT package**

Run:

```bash
uv run python scripts/physical_ai_package.py validate artifacts/stage4/pusht_quick_episode_0000 --json
```

Expected: JSON contains `"ok": true`.

- [ ] **Step 7: Summarize PushT package**

Run:

```bash
uv run python scripts/physical_ai_package.py summarize artifacts/stage4/pusht_quick_episode_0000 --json
```

Expected: JSON summary includes `scenario_type: open_robot_manipulation` and `frame_count: 120`.

- [ ] **Step 8: Export PushT candidates**

Run:

```bash
uv run python scripts/physical_ai_package.py export-candidates artifacts/stage4/pusht_quick_episode_0000
```

Expected: command exits 0 and writes `artifacts/stage4/pusht_quick_episode_0000/derived/candidates.csv`.

- [ ] **Step 9: Convert PushT package to Rerun**

Run:

```bash
uv run python scripts/physical_ai_package.py convert-rerun \
  artifacts/stage4/pusht_quick_episode_0000 \
  --output-rrd artifacts/stage4/pusht_quick_episode_0000.rrd
```

Expected: command exits 0 and writes `artifacts/stage4/pusht_quick_episode_0000.rrd`.

- [ ] **Step 10: Verify PushT `.rrd`**

Run:

```bash
uv run rerun rrd verify artifacts/stage4/pusht_quick_episode_0000.rrd
```

Expected: verification exits 0.

- [ ] **Step 11: Inspect PushT package structure**

Run:

```bash
uv run python - <<'PY'
import csv, json
from pathlib import Path

root = Path("artifacts/stage4/pusht_quick_episode_0000")
manifest = json.loads((root / "physical_ai_manifest.json").read_text())
frames = list(csv.DictReader((root / "frames.csv").open()))
metrics = list(csv.DictReader((root / "metrics.csv").open()))
print("source_dataset:", manifest["source_dataset"])
print("frame_count:", len(frames))
print("first_frame:", frames[0])
print("metric_names:", sorted({row["metric_name"] for row in metrics}))
PY
```

Expected: source metadata points to `lerobot/pusht`, first frame has real refs, metric names include `action_norm`, `state_norm`, `action_delta`, and `image_available`.

- [ ] **Step 12: Update docs**

Edit `docs/research/06-lerobot开放数据样板链路记录.md`:

- Replace the previous “PushT Quick Smoke 未运行” status.
- Record exact commands and pass/fail summaries.
- Record package path and `.rrd` path.
- Record frame count, camera names, state/action dimensions, candidate count if easily available, and `rerun rrd verify` result.

Edit `docs/research/06-lerobot到physical-ai-package映射.md` if PushT real fields require mapping updates.

- [ ] **Step 13: Commit**

Run:

```bash
git add src/physical_ai_data tests/physical_ai_data docs/research/06-lerobot开放数据样板链路记录.md docs/research/06-lerobot到physical-ai-package映射.md
git status --short
git commit -m "Verify PushT real data quick smoke"
```

Expected: commit succeeds. Generated `artifacts/` and `.rrd` files are not staged.

## Task 4: ALOHA Representative Smoke 完整验证

**Files:**

- Modify: `src/physical_ai_data/lerobot_loader.py` only if ALOHA exposes a focused compatibility bug.
- Modify: `src/physical_ai_data/lerobot_profiles.py` only for conservative ALOHA profile calibration.
- Modify: `src/physical_ai_data/rerun_adapter.py` only if multi-camera logging fails.
- Modify: `src/physical_ai_data/candidates.py` only if real ALOHA exposes an existing candidate export bug and a focused test is added first.
- Modify: `tests/physical_ai_data/test_lerobot_loader.py`
- Modify: `tests/physical_ai_data/test_lerobot_profiles.py` if profile changes.
- Modify: `tests/physical_ai_data/test_rerun_adapter.py` if Rerun multi-camera changes.
- Modify: `tests/physical_ai_data/test_candidates.py` if candidate export changes.
- Modify: `docs/research/06-lerobot开放数据样板链路记录.md`
- Modify: `docs/research/06-lerobot到physical-ai-package映射.md`
- Modify: `docs/stage4/README.md` only if repo id, camera option, or command changes.

- [ ] **Step 1: Remove old generated ALOHA artifacts**

Run:

```bash
rm -rf artifacts/stage4/aloha_smoke_episode_0000 artifacts/stage4/aloha_smoke_episode_0000.rrd
```

Expected: no committed files are removed.

- [ ] **Step 2: Run ALOHA import**

Run:

```bash
uv run python scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/aloha_sim_transfer_cube_human \
  --episode-index 0 \
  --output-dir artifacts/stage4/aloha_smoke_episode_0000 \
  --profile aloha \
  --max-frames 60
```

Expected: command exits 0 and writes `artifacts/stage4/aloha_smoke_episode_0000/physical_ai_manifest.json`.

- [ ] **Step 3: 如果 repo 不可用或不具备多相机代表性，选择等价公开 ALOHA repo**

如果指定 repo 缺失、不可访问、重命名，或真实导入后只暴露单相机而无法满足 ALOHA 多相机代表性：

1. 使用 LeRobot/Hugging Face search 或 LeRobot 官方示例寻找公开 ALOHA 多相机数据集。
2. 用替换后的 `--repo-id` 重新运行 import。
3. 在 `docs/stage4/README.md` 和链路记录中写明替换原因。
4. 如果找不到公开且可访问的多相机 ALOHA 数据集，Stage 4.1 不能标记完成。

Expected: 替换 repo 仍属于 ALOHA-family 公开数据集，并暴露多相机或足够明确的多视角图像字段。

- [ ] **Step 4: If ALOHA import fails due to code, write a focused test**

Modify fake fixtures to match the real failing field shape.

Run:

```bash
uv run python -m pytest tests/physical_ai_data/test_lerobot_loader.py tests/physical_ai_data/test_lerobot_profiles.py -q
```

Expected: FAIL before production fix.

- [ ] **Step 5: Patch minimal ALOHA compatibility**

Allowed fixes:

- loader image/camera key handling
- loader state/action extraction for real ALOHA fields
- conservative ALOHA profile phase/object metadata
- Rerun multi-camera extra image logging
- candidate export issue: only if real ALOHA exposes an existing `export-candidates` bug, add a focused test in `tests/physical_ai_data/test_candidates.py` and then patch `src/physical_ai_data/candidates.py`

Not allowed:

- guessing dual-arm joint names
- inventing success/failure labels
- adding a dedicated importer for one ALOHA repo
- broad schema changes

- [ ] **Step 6: Re-run tests and ALOHA import**

Run:

```bash
uv run python -m pytest -q
uv run python scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/aloha_sim_transfer_cube_human \
  --episode-index 0 \
  --output-dir artifacts/stage4/aloha_smoke_episode_0000 \
  --profile aloha \
  --max-frames 60
```

If a replacement repo was selected, use that repo id consistently.

Expected: tests pass and ALOHA import exits 0.

- [ ] **Step 7: Validate ALOHA package**

Run:

```bash
uv run python scripts/physical_ai_package.py validate artifacts/stage4/aloha_smoke_episode_0000 --json
```

Expected: JSON contains `"ok": true`.

- [ ] **Step 8: Summarize ALOHA package**

Run:

```bash
uv run python scripts/physical_ai_package.py summarize artifacts/stage4/aloha_smoke_episode_0000 --json
```

Expected: JSON summary includes `scenario_type: open_robot_manipulation` and `frame_count: 60`.

- [ ] **Step 9: Export ALOHA candidates**

Run:

```bash
uv run python scripts/physical_ai_package.py export-candidates artifacts/stage4/aloha_smoke_episode_0000
```

Expected: command exits 0 and writes `artifacts/stage4/aloha_smoke_episode_0000/derived/candidates.csv`. If it fails due to a code bug, first add a focused test in `tests/physical_ai_data/test_candidates.py`, confirm failure, then make the smallest `src/physical_ai_data/candidates.py` fix.

- [ ] **Step 10: Convert ALOHA package to Rerun**

Run:

```bash
uv run python scripts/physical_ai_package.py convert-rerun \
  artifacts/stage4/aloha_smoke_episode_0000 \
  --output-rrd artifacts/stage4/aloha_smoke_episode_0000.rrd
```

Expected: command exits 0 and writes `artifacts/stage4/aloha_smoke_episode_0000.rrd`.

- [ ] **Step 11: Verify ALOHA `.rrd`**

Run:

```bash
uv run rerun rrd verify artifacts/stage4/aloha_smoke_episode_0000.rrd
```

Expected: verification exits 0.

- [ ] **Step 12: Inspect ALOHA multi-camera refs**

Run:

```bash
uv run python - <<'PY'
import csv, json
from pathlib import Path

root = Path("artifacts/stage4/aloha_smoke_episode_0000")
frames = list(csv.DictReader((root / "frames.csv").open()))
image_ref_sets = [json.loads(row.get("image_refs_json") or "{}") for row in frames]
cameras = sorted({camera for refs in image_ref_sets for camera in refs})
print("frame_count:", len(frames))
print("cameras:", cameras)
print("first_image_ref:", frames[0].get("image_ref", ""))
print("first_image_refs_json:", image_ref_sets[0] if image_ref_sets else {})
PY
```

Expected: frame count is 60, `cameras` contains more than one entry, and `image_refs_json` records the multi-camera refs. If only one camera is exposed, do not mark ALOHA smoke as passed; return to Step 3 and select an equivalent public multi-camera ALOHA repo. If no such repo is available, Stage 4.1 remains incomplete or blocked.

- [ ] **Step 13: Update docs**

Edit `docs/research/06-lerobot开放数据样板链路记录.md`:

- Replace the previous “ALOHA Smoke 未通过” status.
- Record repo id, episode index, max frames, package path, `.rrd` path, command outcomes, cameras, state/action dimensions, and `rerun rrd verify` result.
- Explicitly state whether ALOHA multi-camera refs were observed. Do not claim Stage 4.1 completion unless more than one camera was imported and recorded.

Edit `docs/research/06-lerobot到physical-ai-package映射.md`:

- Update ALOHA observed field mapping.
- Keep ALOHA semantic limitations explicit.

Edit `docs/stage4/README.md` only if command changes were necessary.

- [ ] **Step 14: Commit**

Run:

```bash
git add src/physical_ai_data tests/physical_ai_data docs/research/06-lerobot开放数据样板链路记录.md docs/research/06-lerobot到physical-ai-package映射.md docs/stage4/README.md
git status --short
git commit -m "Verify ALOHA real data representative smoke"
```

Expected: commit succeeds. Generated packages and `.rrd` files remain untracked/ignored.

## Task 5: PushT Full Acceptance 尝试与 Viewer 检查

**Files:**

- Modify: `docs/research/06-lerobot开放数据样板链路记录.md`
- Modify: `docs/stage4/README.md` only if commands change.
- Modify: `details.md`

- [ ] **Step 1: Check disk before full acceptance**

Run:

```bash
df -h .
du -sh artifacts/stage4 2>/dev/null || true
```

Expected: enough local space for another generated package and `.rrd`. Record if space is tight.

- [ ] **Step 2: Attempt PushT full import**

Run:

```bash
uv run python scripts/physical_ai_package.py import-lerobot \
  --repo-id lerobot/pusht \
  --episode-index 0 \
  --output-dir artifacts/stage4/pusht_episode_0000 \
  --profile pusht
```

Expected: command exits 0 if resources allow. If it fails due to resource or external issues, record exact error and continue to Viewer check using quick smoke artifacts.

- [ ] **Step 3: If full import succeeds, run shared verification**

Run:

```bash
uv run python scripts/physical_ai_package.py validate artifacts/stage4/pusht_episode_0000 --json
uv run python scripts/physical_ai_package.py summarize artifacts/stage4/pusht_episode_0000 --json
uv run python scripts/physical_ai_package.py export-candidates artifacts/stage4/pusht_episode_0000
uv run python scripts/physical_ai_package.py convert-rerun artifacts/stage4/pusht_episode_0000 --output-rrd artifacts/stage4/pusht_episode_0000.rrd
uv run rerun rrd verify artifacts/stage4/pusht_episode_0000.rrd
```

Expected: all commands pass if full import succeeded.

- [ ] **Step 4: Run lightweight `.rrd` file checks**

Run:

```bash
ls -lh artifacts/stage4/*episode_0000*.rrd
uv run rerun rrd verify artifacts/stage4/pusht_quick_episode_0000.rrd
uv run rerun rrd verify artifacts/stage4/aloha_smoke_episode_0000.rrd
```

Expected: quick PushT and ALOHA `.rrd` files exist and verify.

- [ ] **Step 5: Perform manual Viewer check when GUI is available**

Run:

```bash
uv run rerun artifacts/stage4/pusht_quick_episode_0000.rrd
uv run rerun artifacts/stage4/aloha_smoke_episode_0000.rrd
```

Expected manual observations:

- PushT image frames are visible.
- Timeline scrubbing updates images.
- Metrics/events/labels are visible enough for inspection.
- ALOHA main camera is visible.
- ALOHA extra cameras appear under additional image paths. If ALOHA only shows one camera, do not mark Viewer check or Stage 4.1 as complete; return to Task 4 Step 3 to select an equivalent public multi-camera ALOHA repo.

If GUI cannot be used in the current environment, record the reason and keep `.rrd verify` as the machine-check evidence.

- [ ] **Step 6: Update docs**

Edit `docs/research/06-lerobot开放数据样板链路记录.md`:

- Add PushT full acceptance attempt result.
- Add Viewer/Blueprint manual check section.
- Add `.rrd verify` results for quick PushT and ALOHA.
- Add current `df -h .` and generated `artifacts/stage4` size observations after real smokes.
- Re-run the resolved-cache `du -sh` command from Task 1 Step 8 after real smoke downloads, and record actual Hugging Face/LeRobot cache footprint after dataset access.
- Record any GUI limitation honestly.

Edit `docs/stage4/README.md` if full/quick command wording or environment instructions changed.

Edit `details.md`:

- Record which real smokes passed.
- Record whether PushT full acceptance passed or was resource-limited.
- Update next steps to Stage 4.2 only after quick PushT and ALOHA pass.

- [ ] **Step 7: Commit**

Run:

```bash
git add docs/research/06-lerobot开放数据样板链路记录.md docs/stage4/README.md details.md
git status --short
git commit -m "Document LeRobot real data verification results"
```

Expected: commit succeeds.

## Task 6: 最终回归与完成审计

**Files:**

- Modify: `README.md` only if current-status text needs correction.
- Modify: `details.md` if final status wording needs correction.
- Modify: `docs/research/06-lerobot开放数据样板链路记录.md` if final command evidence is incomplete.

- [ ] **Step 1: Run regression checks without relying on generated artifacts**

Run:

```bash
uv run python -m pytest -q
PYTHONPATH=src python3 -m pytest -q
```

Expected: both test commands pass. The second command verifies the default non-LeRobot source-tree workflow still works without invoking LeRobot extras or network.

- [ ] **Step 2: Re-run required Stage 4.1 machine checks**

Run:

```bash
uv run python scripts/physical_ai_package.py validate artifacts/stage4/pusht_quick_episode_0000 --json
uv run python scripts/physical_ai_package.py validate artifacts/stage4/aloha_smoke_episode_0000 --json
uv run rerun rrd verify artifacts/stage4/pusht_quick_episode_0000.rrd
uv run rerun rrd verify artifacts/stage4/aloha_smoke_episode_0000.rrd
```

Expected: all four commands pass.

- [ ] **Step 3: Check generated files are not staged**

Run:

```bash
git status --short
```

Expected: no `artifacts/`, `.venv/`, dataset cache, `.rrd`, or screenshots are staged. If generated files appear as untracked and are not ignored, update `.gitignore` narrowly.

- [ ] **Step 4: Audit documentation against spec**

Open and verify:

- `docs/research/06-lerobot开放数据样板链路记录.md` includes uv environment, PushT quick, ALOHA smoke, PushT full attempt, shared checks, `.rrd verify`, and Viewer/manual check.
- `docs/research/06-lerobot开放数据样板链路记录.md` includes Hugging Face/LeRobot resolved cache path observations, network metadata probe results, disk availability, generated artifact size, and post-real-smoke cache size observations.
- `docs/research/06-lerobot开放数据样板链路记录.md` proves ALOHA imported more than one camera. If it does not, Stage 4.1 is not complete.
- `docs/research/06-lerobot到physical-ai-package映射.md` reflects observed real PushT/ALOHA fields.
- `details.md` does not claim full acceptance passed unless it did.
- `README.md` current status is not misleading.

Expected: docs match actual command evidence.

- [ ] **Step 5: Commit any final doc cleanup**

If files changed:

```bash
git add README.md details.md docs/research/06-lerobot开放数据样板链路记录.md docs/research/06-lerobot到physical-ai-package映射.md .gitignore
git status --short
git commit -m "Finalize Stage 4.1 LeRobot smoke documentation"
```

Expected: commit succeeds, or no commit is needed.

- [ ] **Step 6: Final evidence summary**

Prepare a short final summary with:

- `uv` version.
- Python version.
- LeRobot version.
- Rerun version.
- `pytest` result.
- PushT quick import/validate/summarize/export/convert/verify result.
- ALOHA import/validate/summarize/export/convert/verify result.
- PushT full acceptance result or reason it remained an attempt.
- Viewer check result.

Expected: the summary proves Stage 4.1 completion under the strict spec.
