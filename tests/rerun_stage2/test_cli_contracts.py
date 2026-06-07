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
