import json
import os
import subprocess
from pathlib import Path


SCRIPT = Path("scripts/physical_ai_package.py")


def _run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        check=False,
        text=True,
        capture_output=True,
        **kwargs,
    )


def test_cli_generate_validate_summarize_and_export(tmp_path: Path):
    package = tmp_path / "weld"

    generate = _run(["generate", "welding", "--output-dir", str(package), "--frames", "8", "--seed", "7"])
    assert generate.returncode == 0, generate.stderr

    validate = _run(["validate", str(package), "--json"])
    assert validate.returncode == 0, validate.stderr
    payload = json.loads(validate.stdout)
    assert payload["ok"] is True

    summarize = _run(["summarize", str(package), "--json"])
    assert summarize.returncode == 0, summarize.stderr
    assert json.loads(summarize.stdout)["frame_count"] == 8

    export = _run(["export-candidates", str(package)])
    assert export.returncode == 0, export.stderr
    assert (package / "derived" / "candidates.csv").exists()


def test_cli_convert_rerun(tmp_path: Path):
    package = tmp_path / "pick"
    output_rrd = tmp_path / "pick.rrd"

    generate = _run(["generate", "pick-sort", "--output-dir", str(package), "--frames", "8", "--seed", "11"])
    assert generate.returncode == 0, generate.stderr
    convert = _run(["convert-rerun", str(package), "--output-rrd", str(output_rrd)])

    assert convert.returncode == 0, convert.stderr
    assert output_rrd.exists()


def test_cli_invalid_package_returns_nonzero(tmp_path: Path):
    validate = _run(["validate", str(tmp_path)])

    assert validate.returncode != 0
    assert "missing_manifest" in validate.stdout or "missing_manifest" in validate.stderr


def test_cli_human_success_output_includes_key_paths(tmp_path: Path):
    package = tmp_path / "weld"

    generate = _run(["generate", "welding", "--output-dir", str(package), "--frames", "8"])
    assert generate.returncode == 0, generate.stderr
    assert str(package) in generate.stdout

    validate = _run(["validate", str(package)])
    assert validate.returncode == 0, validate.stderr
    assert str(package) in validate.stdout

    export = _run(["export-candidates", str(package)])
    assert export.returncode == 0, export.stderr
    assert str(package / "derived" / "candidates.csv") in export.stdout


def test_cli_bad_args_return_argparse_exit_code():
    result = _run(["generate", "welding", "--frames", "8"])

    assert result.returncode == 2
    assert "usage:" in result.stderr


def test_cli_invalid_validate_json_is_machine_readable(tmp_path: Path):
    validate = _run(["validate", str(tmp_path), "--json"])

    assert validate.returncode == 1
    payload = json.loads(validate.stdout)
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "missing_manifest"


def test_cli_wrapper_runs_without_pythonpath(tmp_path: Path):
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}

    help_result = _run(["--help"], env=env)
    assert help_result.returncode == 0, help_result.stderr
    assert "Physical AI Package" in help_result.stdout

    validate = _run(["validate", str(tmp_path)], env=env)
    assert validate.returncode == 1
    assert "missing_manifest" in validate.stderr


def test_cli_invalid_summarize_json_is_machine_readable(tmp_path: Path):
    summarize = _run(["summarize", str(tmp_path), "--json"])

    assert summarize.returncode == 1
    payload = json.loads(summarize.stdout)
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "missing_manifest"
