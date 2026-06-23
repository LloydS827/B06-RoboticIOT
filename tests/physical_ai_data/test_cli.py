import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from physical_ai_data.schema import ValidationMessage, ValidationResult


SCRIPT = Path("scripts/physical_ai_package.py")


def test_pyproject_exposes_physical_ai_package_console_script():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["physical-ai-package"] == "physical_ai_data.cli:main"


def _run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
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


def test_cli_export_training_draft(tmp_path: Path):
    package = tmp_path / "weld"

    generate = _run(["generate", "welding", "--output-dir", str(package), "--frames", "8", "--seed", "7"])
    assert generate.returncode == 0, generate.stderr

    export = _run(["export-training-draft", str(package)])

    output_dir = package / "derived" / "training_eval"
    assert export.returncode == 0, export.stderr
    assert f"Wrote training/evaluation draft: {output_dir}" in export.stdout
    assert (output_dir / "training_eval_manifest.json").exists()
    assert (output_dir / "samples.csv").exists()


def test_cli_export_training_draft_custom_output(tmp_path: Path):
    package = tmp_path / "weld"
    output_dir = tmp_path / "drafts" / "train"

    generate = _run(["generate", "welding", "--output-dir", str(package), "--frames", "8", "--seed", "7"])
    assert generate.returncode == 0, generate.stderr

    export = _run(
        [
            "export-training-draft",
            str(package),
            "--output-dir",
            str(output_dir),
            "--split",
            "train",
        ]
    )

    assert export.returncode == 0, export.stderr
    assert f"Wrote training/evaluation draft: {output_dir}" in export.stdout
    manifest = json.loads((output_dir / "training_eval_manifest.json").read_text(encoding="utf-8"))
    assert manifest["split"] == "train"


def test_cli_existing_package_operations_call_sdk_wrappers(monkeypatch, tmp_path: Path):
    from physical_ai_data import cli

    package = tmp_path / "pkg"
    output_csv = tmp_path / "candidates.csv"
    output_rrd = tmp_path / "package.rrd"
    calls = []

    def fake_validate(path: Path) -> ValidationResult:
        calls.append(("validate", path))
        return ValidationResult(summary={"frame_count": 2})

    def fake_summarize(path: Path) -> dict[str, object]:
        calls.append(("summarize", path))
        return {"frame_count": 2}

    def fake_export_candidates_csv(path: Path, output_csv: Path | None = None, *, min_score: float = 0.5) -> Path:
        calls.append(("export_candidates_csv", path, output_csv, min_score))
        return tmp_path / "exported.csv"

    def fake_convert_to_rerun(path: Path, output: Path) -> Path:
        calls.append(("convert_to_rerun", path, output))
        return output

    monkeypatch.setattr(cli, "validate", fake_validate)
    monkeypatch.setattr(cli, "summarize", fake_summarize)
    monkeypatch.setattr(cli, "export_candidates_csv", fake_export_candidates_csv)
    monkeypatch.setattr(cli, "convert_to_rerun", fake_convert_to_rerun)

    assert cli.main(["validate", str(package)]) == 0
    assert cli.main(["summarize", str(package), "--json"]) == 0
    assert cli.main(["export-candidates", str(package), "--output-csv", str(output_csv), "--min-score", "0.8"]) == 0
    assert cli.main(["convert-rerun", str(package), "--output-rrd", str(output_rrd)]) == 0

    assert calls == [
        ("validate", package),
        ("validate", package),
        ("summarize", package),
        ("export_candidates_csv", package, output_csv, 0.8),
        ("convert_to_rerun", package, output_rrd),
    ]


def test_cli_run_weld_workcell_maps_args_to_pipeline(monkeypatch, tmp_path: Path, capsys):
    from physical_ai_data import cli
    from physical_ai_data.pipelines import PipelineResult

    calls = []

    def fake_pipeline(**kwargs):
        calls.append(kwargs)
        package_root = tmp_path / "package"
        return PipelineResult(
            package_root=package_root,
            validation=ValidationResult(summary={"frame_count": 5}),
            summary={"package_id": "pkg", "frame_count": 5},
            candidates_csv=package_root / "derived" / "candidates.csv",
            training_draft_dir=package_root / "derived" / "training_eval",
            rrd_path=tmp_path / "package.rrd",
        )

    monkeypatch.setattr(cli, "run_weld_workcell_pipeline", fake_pipeline)

    result = cli.main(
        [
            "run-weld-workcell",
            "--clean-root",
            str(tmp_path / "clean" / "weld_workcell"),
            "--output-dir",
            str(tmp_path / "package"),
            "--no-copy-images",
            "--candidate-min-score",
            "0.8",
            "--training-split",
            "eval",
            "--output-rrd",
            str(tmp_path / "package.rrd"),
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert calls == [
        {
            "clean_root": tmp_path / "clean" / "weld_workcell",
            "output_dir": tmp_path / "package",
            "copy_images": False,
            "export_candidates": True,
            "candidate_min_score": 0.8,
            "training_split": "eval",
            "output_rrd": tmp_path / "package.rrd",
        }
    ]
    assert "Wrote Physical AI Package" in captured.out
    assert str(tmp_path / "package") in captured.out


def test_cli_run_weld_workcell_json_handles_disabled_outputs(monkeypatch, tmp_path: Path, capsys):
    from physical_ai_data import cli
    from physical_ai_data.pipelines import PipelineResult

    calls = []

    def fake_pipeline(**kwargs):
        calls.append(kwargs)
        return PipelineResult(
            package_root=tmp_path / "package",
            validation=ValidationResult(summary={"frame_count": 5}),
            summary={"frame_count": 5},
            candidates_csv=None,
            training_draft_dir=None,
            rrd_path=None,
        )

    monkeypatch.setattr(cli, "run_weld_workcell_pipeline", fake_pipeline)

    result = cli.main(
        [
            "run-weld-workcell",
            "--clean-root",
            str(tmp_path / "clean"),
            "--output-dir",
            str(tmp_path / "package"),
            "--no-candidates",
            "--training-split",
            "none",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert result == 0
    assert calls[0]["export_candidates"] is False
    assert calls[0]["training_split"] is None
    assert payload["package_root"] == str(tmp_path / "package")
    assert payload["candidates_csv"] is None
    assert payload["training_draft_dir"] is None
    assert payload["rrd_path"] is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", None),
        (" none ", None),
        ("NULL", None),
        (" eval ", "eval"),
    ],
)
def test_cli_normalizes_training_split(value, expected):
    from physical_ai_data import cli

    assert cli._normalize_training_split(value) == expected


def test_cli_run_weld_workcell_stage8_smoke(tmp_path: Path):
    from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo

    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    package_root = tmp_path / "package"
    output_rrd = tmp_path / "package.rrd"

    result = _run(
        [
            "run-weld-workcell",
            "--clean-root",
            str(fixture.clean_root),
            "--output-dir",
            str(package_root),
            "--training-split",
            "eval",
            "--output-rrd",
            str(output_rrd),
        ]
    )

    assert result.returncode == 0, result.stderr
    assert (package_root / "physical_ai_manifest.json").is_file()
    assert (package_root / "derived" / "candidates.csv").is_file()
    assert (package_root / "derived" / "training_eval" / "training_eval_manifest.json").is_file()
    assert output_rrd.is_file()


def test_cli_summarize_json_invalid_package_uses_sdk_validate(monkeypatch, tmp_path: Path):
    from physical_ai_data import cli

    package = tmp_path / "pkg"
    calls = []

    def fake_validate(path: Path) -> ValidationResult:
        calls.append(("validate", path))
        return ValidationResult(errors=[ValidationMessage("missing_manifest", "missing manifest")])

    def fail_summarize(path: Path) -> dict[str, object]:
        raise AssertionError(f"summarize should not be called for invalid package: {path}")

    monkeypatch.setattr(cli, "validate", fake_validate)
    monkeypatch.setattr(cli, "summarize", fail_summarize)

    result = cli.main(["summarize", str(package), "--json"])

    assert result == 1
    assert calls == [("validate", package)]


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
