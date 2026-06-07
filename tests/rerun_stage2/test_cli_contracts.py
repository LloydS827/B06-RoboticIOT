import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from rerun_stage2.sim_data import RecordingConfig, write_simulation_package
from rerun_stage2.rerun_writer import write_rrd


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


def test_write_rrd_uses_rerun_033_set_time_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    package = write_simulation_package(tmp_path / "sim", RecordingConfig(frame_count=2))
    fake_rr = _FakeRerun()
    monkeypatch.setitem(sys.modules, "rerun", fake_rr)

    write_rrd(package.root, tmp_path / "sim.rrd")

    assert ("sim_time", {"duration": 0.0}) in fake_rr.time_calls
    assert ("robot_tick", {"sequence": 0}) in fake_rr.time_calls
    assert ("camera_frame", {"sequence": 0}) in fake_rr.time_calls
    assert ("weld_phase", {"sequence": 0}) in fake_rr.time_calls


def test_write_rrd_removes_output_when_rerun_logging_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    package = write_simulation_package(tmp_path / "sim", RecordingConfig(frame_count=1))
    output_rrd = tmp_path / "sim.rrd"
    fake_rr = _FakeRerun(fail_on_log=True)
    monkeypatch.setitem(sys.modules, "rerun", fake_rr)

    with pytest.raises(RuntimeError, match="simulated log failure"):
        write_rrd(package.root, output_rrd)

    assert not output_rrd.exists()


class _FakeArchetype:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class _FakeRerun(SimpleNamespace):
    Transform3D = _FakeArchetype
    Points3D = _FakeArchetype
    LineStrips3D = _FakeArchetype
    Image = _FakeArchetype
    Scalars = _FakeArchetype
    TextLog = _FakeArchetype
    Quaternion = _FakeArchetype

    def __init__(self, fail_on_log: bool = False):
        super().__init__()
        self.fail_on_log = fail_on_log
        self.time_calls: list[tuple[str, dict[str, float | int]]] = []

    def init(self, *args, **kwargs):
        return None

    def save(self, path):
        Path(path).write_bytes(b"partial rrd")

    def set_time(self, timeline, **kwargs):
        self.time_calls.append((timeline, kwargs))

    def log(self, *args, **kwargs):
        if self.fail_on_log:
            raise RuntimeError("simulated log failure")
