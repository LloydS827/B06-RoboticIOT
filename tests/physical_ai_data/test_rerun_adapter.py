import shutil
import subprocess
from pathlib import Path

import pytest

from physical_ai_data.rerun_adapter import write_rrd
from physical_ai_data.samples import generate_pick_sort_package, generate_welding_package


def _verify_rrd(output: Path) -> None:
    if shutil.which("rerun") is None:
        pytest.skip("rerun CLI is not installed")

    verify = subprocess.run(["rerun", "rrd", "verify", str(output)], check=False, text=True, capture_output=True)
    assert verify.returncode == 0, verify.stderr + verify.stdout


def test_write_welding_rrd_and_verify(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=8, random_seed=8)
    output = tmp_path / "weld.rrd"

    result = write_rrd(package, output)

    assert result == output
    assert output.exists()
    _verify_rrd(output)


def test_write_pick_sort_rrd_and_verify(tmp_path: Path):
    package = generate_pick_sort_package(tmp_path / "pick", frame_count=8, random_seed=9)
    output = tmp_path / "pick.rrd"

    result = write_rrd(package, output)

    assert result == output
    assert output.exists()
    _verify_rrd(output)


def test_invalid_package_raises_validator_summary(tmp_path: Path):
    with pytest.raises(ValueError, match="missing_manifest: Missing physical_ai_manifest.json"):
        write_rrd(tmp_path, tmp_path / "invalid.rrd")
