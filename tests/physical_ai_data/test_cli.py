import json
import subprocess
from pathlib import Path


SCRIPT = Path("scripts/physical_ai_package.py")


def test_cli_generate_validate_summarize_and_export(tmp_path: Path):
    package = tmp_path / "weld"

    generate = subprocess.run(
        ["python3", str(SCRIPT), "generate", "welding", "--output-dir", str(package), "--frames", "8", "--seed", "7"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert generate.returncode == 0, generate.stderr

    validate = subprocess.run(
        ["python3", str(SCRIPT), "validate", str(package), "--json"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert validate.returncode == 0, validate.stderr
    payload = json.loads(validate.stdout)
    assert payload["ok"] is True

    summarize = subprocess.run(
        ["python3", str(SCRIPT), "summarize", str(package), "--json"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert summarize.returncode == 0, summarize.stderr
    assert json.loads(summarize.stdout)["frame_count"] == 8

    export = subprocess.run(
        ["python3", str(SCRIPT), "export-candidates", str(package)],
        check=False,
        text=True,
        capture_output=True,
    )
    assert export.returncode == 0, export.stderr
    assert (package / "derived" / "candidates.csv").exists()


def test_cli_convert_rerun(tmp_path: Path):
    package = tmp_path / "pick"
    output_rrd = tmp_path / "pick.rrd"

    subprocess.run(
        ["python3", str(SCRIPT), "generate", "pick-sort", "--output-dir", str(package), "--frames", "8", "--seed", "11"],
        check=True,
        text=True,
        capture_output=True,
    )
    convert = subprocess.run(
        ["python3", str(SCRIPT), "convert-rerun", str(package), "--output-rrd", str(output_rrd)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert convert.returncode == 0, convert.stderr
    assert output_rrd.exists()


def test_cli_invalid_package_returns_nonzero(tmp_path: Path):
    validate = subprocess.run(
        ["python3", str(SCRIPT), "validate", str(tmp_path)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert validate.returncode != 0
    assert "missing_manifest" in validate.stdout or "missing_manifest" in validate.stderr

