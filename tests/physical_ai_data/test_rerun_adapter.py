import shutil
import subprocess
from pathlib import Path

import pytest

from physical_ai_data import rerun_adapter
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


def test_float_helper_rejects_non_finite_values():
    assert rerun_adapter._float_or_none("nan") is None
    assert rerun_adapter._float_or_none("inf") is None
    assert rerun_adapter._float_or_none("-inf") is None
    assert rerun_adapter._float_or_none("1.25") == 1.25


def test_xyz_reader_skips_non_finite_rows(tmp_path: Path):
    xyz = tmp_path / "points.csv"
    xyz.write_text("x,y,z\n1,2,3\nnan,2,3\n1,inf,3\n1,2,-inf\n", encoding="utf-8")

    assert rerun_adapter._read_xyz_csv(xyz) == [(1.0, 2.0, 3.0)]


def test_pose_mapping_degrades_non_finite_values_to_defaults():
    default = {"translation": (0.0, 0.0, 0.0), "quaternion": (0.0, 0.0, 0.0, 1.0)}

    assert rerun_adapter._pose_from_mapping({"x": "nan", "y": "1", "z": "2"}, default) == default
    assert rerun_adapter._pose_from_mapping(
        {"x": "1", "y": "2", "z": "3", "qx": "0", "qy": "inf", "qz": "0", "qw": "1"},
        default,
    ) == {"translation": (1.0, 2.0, 3.0), "quaternion": default["quaternion"]}
