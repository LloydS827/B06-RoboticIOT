from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHON"] = sys.executable
    return env


def test_sdk_pipeline_stage8_example_runs(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "examples/sdk_pipeline_stage8.py",
            "--output-root",
            str(tmp_path / "stage8_sdk_example"),
            "--frames",
            "5",
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["validation_ok"] is True
    assert payload["summary"]["frame_count"] == 5
    assert Path(payload["package_root"]).is_dir()
    assert Path(payload["candidates_csv"]).is_file()
    assert Path(payload["training_draft_dir"]).is_dir()
    assert Path(payload["rrd_path"]).is_file()


def test_sdk_existing_package_ops_example_runs(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "examples/sdk_existing_package_ops.py",
            "--output-root",
            str(tmp_path / "existing_ops"),
            "--frames",
            "8",
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["validation_ok"] is True
    assert payload["summary"]["frame_count"] == 8
    assert Path(payload["candidates_csv"]).is_file()
    assert Path(payload["training_draft_dir"]).is_dir()
    assert Path(payload["rrd_path"]).is_file()


def test_sdk_low_level_importer_example_runs(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "examples/sdk_low_level_importer.py",
            "--output-root",
            str(tmp_path / "low_level"),
            "--frames",
            "5",
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["source_format"] == "weld_workcell"
    assert payload["frame_count"] == 5
    assert Path(payload["package_root"]).is_dir()


def test_cli_json_smoke_example_runs(tmp_path: Path):
    result = subprocess.run(
        [
            "bash",
            "examples/cli_json_smoke.sh",
            str(tmp_path / "cli_json"),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["validation"]["ok"] is True
    assert payload["summary"]["frame_count"] == 5
    assert Path(payload["package_root"]).is_dir()


def test_cli_json_smoke_example_runs_from_non_repo_cwd(tmp_path: Path):
    result = subprocess.run(
        [
            "bash",
            str(ROOT / "examples" / "cli_json_smoke.sh"),
            str(tmp_path / "cli_json"),
        ],
        cwd=tmp_path,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["validation"]["ok"] is True
    assert payload["summary"]["frame_count"] == 5
    assert Path(payload["package_root"]).is_dir()
