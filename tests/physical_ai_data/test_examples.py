from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo


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


def test_cli_json_smoke_defaults_to_python_command_when_python_env_is_unset(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    python_wrapper = bin_dir / "python"
    python_wrapper.write_text(f"#!/usr/bin/env bash\nexec {sys.executable!r} \"$@\"\n", encoding="utf-8")
    python_wrapper.chmod(0o755)
    python3_wrapper = bin_dir / "python3"
    python3_wrapper.write_text("#!/usr/bin/env bash\nexit 42\n", encoding="utf-8")
    python3_wrapper.chmod(0o755)

    env = _env()
    env.pop("PYTHON", None)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        [
            "bash",
            str(ROOT / "examples" / "cli_json_smoke.sh"),
            str(tmp_path / "cli_json"),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["validation"]["ok"] is True
    assert payload["summary"]["frame_count"] == 5


def test_sdk_real_data_onboarding_example_runs_stage8_candidate(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "fixture", frame_count=5)
    output_root = tmp_path / "onboarding"

    result = subprocess.run(
        [
            sys.executable,
            "examples/sdk_real_data_onboarding.py",
            "--clean-root",
            str(fixture.clean_root),
            "--raw-root",
            str(fixture.raw_root),
            "--output-root",
            str(output_root),
            "--training-split",
            "eval",
            "--output-rrd",
            str(output_root / "package.rrd"),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["readiness"]["overall_status"] == "review_required"
    assert payload["pipeline"]["validation"]["ok"] is True
    assert payload["pipeline"]["summary"]["frame_count"] == 5
    assert Path(payload["pipeline"]["package_root"]).is_dir()
    assert Path(payload["pipeline"]["candidates_csv"]).is_file()
    assert Path(payload["pipeline"]["training_draft_dir"]).is_dir()
    assert Path(payload["pipeline"]["rrd_path"]).is_file()
    assert payload["output_index"]["package_root"] == payload["pipeline"]["package_root"]
    assert Path(payload["output_index"]["candidates_csv"]).is_file()
    assert Path(payload["output_index"]["training_draft_dir"]).is_dir()
    assert Path(payload["output_index"]["rrd_path"]).is_file()
    assert payload["next_steps"]


def test_sdk_real_data_onboarding_example_blocks_invalid_clean_zone(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "fixture", frame_count=5)
    (fixture.clean_root / "process.csv").unlink()
    output_root = tmp_path / "onboarding"

    result = subprocess.run(
        [
            sys.executable,
            "examples/sdk_real_data_onboarding.py",
            "--clean-root",
            str(fixture.clean_root),
            "--raw-root",
            str(fixture.raw_root),
            "--output-root",
            str(output_root),
            "--training-split",
            "eval",
            "--output-rrd",
            str(output_root / "package.rrd"),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2, result.stderr
    payload = json.loads(result.stdout)
    assert payload["readiness"]["overall_status"] == "blocked"
    assert payload["pipeline"] is None
    assert payload["output_index"] is None
    assert not (output_root / "package").exists()


def test_sdk_real_data_onboarding_example_reports_pipeline_failure_as_json(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "fixture", frame_count=5)
    output_root = tmp_path / "onboarding"

    result = subprocess.run(
        [
            sys.executable,
            "examples/sdk_real_data_onboarding.py",
            "--clean-root",
            str(fixture.clean_root),
            "--raw-root",
            str(fixture.raw_root),
            "--output-root",
            str(output_root),
            "--training-split",
            "invalid-split",
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["readiness"]["overall_status"] == "review_required"
    assert payload["pipeline"] is None
    assert payload["output_index"] is None
    assert "invalid-split" in payload["error"]
    assert "Traceback" not in result.stderr
    assert not (output_root / "package").exists()


def test_sdk_real_data_onboarding_example_removes_failed_rrd_output(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "fixture", frame_count=5)
    output_root = tmp_path / "onboarding"
    output_rrd = tmp_path / "failed-package.rrd"

    result = subprocess.run(
        [
            sys.executable,
            "examples/sdk_real_data_onboarding.py",
            "--clean-root",
            str(fixture.clean_root),
            "--raw-root",
            str(fixture.raw_root),
            "--output-root",
            str(output_root),
            "--training-split",
            "invalid-split",
            "--output-rrd",
            str(output_rrd),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["output_index"] is None
    assert not output_rrd.exists()
