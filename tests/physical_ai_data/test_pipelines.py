from __future__ import annotations

import json
from pathlib import Path

import pytest

from physical_ai_data.schema import ValidationMessage, ValidationResult
from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo


def test_run_weld_workcell_pipeline_generates_package_outputs(tmp_path: Path):
    from physical_ai_data.pipelines import PipelineResult, run_weld_workcell_pipeline

    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    package_root = tmp_path / "package"
    output_rrd = tmp_path / "package.rrd"

    result = run_weld_workcell_pipeline(
        clean_root=str(fixture.clean_root),
        output_dir=str(package_root),
        training_split="eval",
        output_rrd=str(output_rrd),
    )

    assert isinstance(result, PipelineResult)
    assert result.package_root == package_root
    assert result.validation.ok
    assert result.summary["frame_count"] == 5
    assert result.candidates_csv == package_root / "derived" / "candidates.csv"
    assert result.candidates_csv.is_file()
    assert result.training_draft_dir == package_root / "derived" / "training_eval"
    assert (result.training_draft_dir / "training_eval_manifest.json").is_file()
    manifest_path = result.training_draft_dir / "training_eval_manifest.json"
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    assert manifest["split"] == "eval"
    assert result.rrd_path == output_rrd
    assert result.rrd_path.is_file()


def test_pipeline_result_to_dict_matches_cli_payload_contract(tmp_path: Path):
    from physical_ai_data.pipelines import run_weld_workcell_pipeline

    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    package_root = tmp_path / "package"
    output_rrd = tmp_path / "package.rrd"

    result = run_weld_workcell_pipeline(
        clean_root=fixture.clean_root,
        output_dir=package_root,
        training_split="eval",
        output_rrd=output_rrd,
    )

    payload = result.to_dict()
    assert payload["package_root"] == str(package_root)
    assert payload["validation"]["ok"] is True
    assert payload["summary"]["frame_count"] == 5
    assert payload["candidates_csv"] == str(package_root / "derived" / "candidates.csv")
    assert payload["training_draft_dir"] == str(package_root / "derived" / "training_eval")
    assert payload["rrd_path"] == str(output_rrd)


def test_run_weld_workcell_pipeline_can_skip_optional_outputs(tmp_path: Path):
    from physical_ai_data.pipelines import run_weld_workcell_pipeline

    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    package_root = tmp_path / "package"

    result = run_weld_workcell_pipeline(
        clean_root=fixture.clean_root,
        output_dir=package_root,
        export_candidates=False,
        training_split=None,
    )

    assert result.validation.ok
    assert result.candidates_csv is None
    assert result.training_draft_dir is None
    assert result.rrd_path is None
    assert not (package_root / "derived" / "candidates.csv").exists()
    assert not (package_root / "derived" / "training_eval").exists()


def test_run_weld_workcell_pipeline_wraps_import_failures(tmp_path: Path):
    from physical_ai_data.pipelines import run_weld_workcell_pipeline

    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    (fixture.clean_root / "process.csv").unlink()

    with pytest.raises(
        ValueError,
        match="weld_workcell pipeline failed during import",
    ) as exc_info:
        run_weld_workcell_pipeline(clean_root=fixture.clean_root, output_dir=tmp_path / "package")

    assert exc_info.value.__cause__ is not None
    assert "process.csv" in str(exc_info.value)


def test_run_weld_workcell_pipeline_import_error_includes_clean_root(tmp_path: Path):
    from physical_ai_data.pipelines import run_weld_workcell_pipeline

    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    (fixture.clean_root / "process.csv").unlink()

    with pytest.raises(ValueError) as exc_info:
        run_weld_workcell_pipeline(clean_root=fixture.clean_root, output_dir=tmp_path / "package")

    message = str(exc_info.value)
    assert "weld_workcell pipeline failed during import" in message
    assert str(fixture.clean_root) in message
    assert "process.csv" in message


def test_run_weld_workcell_pipeline_reports_defensive_validation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import physical_ai_data.pipelines as pipelines
    from physical_ai_data.pipelines import run_weld_workcell_pipeline

    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")

    def fake_validate(package_root: str | Path) -> ValidationResult:
        return ValidationResult(
            errors=[
                ValidationMessage(
                    "forced_invalid",
                    "forced validation failure",
                    "frames.csv",
                ),
            ],
            summary={"frame_count": 0},
        )

    monkeypatch.setattr(pipelines, "validate", fake_validate)

    with pytest.raises(
        ValueError,
        match="weld_workcell pipeline produced invalid package",
    ) as exc_info:
        run_weld_workcell_pipeline(clean_root=fixture.clean_root, output_dir=tmp_path / "package")

    assert "forced_invalid" in str(exc_info.value)
    assert "forced validation failure" in str(exc_info.value)
    assert str(tmp_path / "package") in str(exc_info.value)
    assert "frames.csv" in str(exc_info.value)


def test_run_weld_workcell_pipeline_does_not_report_training_candidate_dependency_as_candidate_export(
    tmp_path: Path,
):
    from physical_ai_data.pipelines import run_weld_workcell_pipeline

    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    package_root = tmp_path / "package"

    result = run_weld_workcell_pipeline(
        clean_root=fixture.clean_root,
        output_dir=package_root,
        export_candidates=False,
    )

    assert result.validation.ok
    assert result.candidates_csv is None
    assert result.training_draft_dir == package_root / "derived" / "training_eval"
    assert (result.training_draft_dir / "samples.csv").is_file()
    assert (package_root / "derived" / "candidates.csv").is_file()
