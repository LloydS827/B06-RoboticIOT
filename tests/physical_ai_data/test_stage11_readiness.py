from __future__ import annotations

import csv
from pathlib import Path

from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo
from physical_ai_data.stage11_readiness import assess_h300_sample_readiness


def _gap_status(report, gap_id: str):
    return next(gap for gap in report.gap_statuses if gap.gap_id == gap_id)


def _fill_empty_image_paths(clean_root: Path):
    frames_path = clean_root / "frames.csv"
    rows = list(csv.DictReader(frames_path.open(newline="", encoding="utf-8")))
    for row in rows:
        if not row["image_path"]:
            row["image_path"] = "images/front_0000.png"
    with frames_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_stage11_readiness_stage8_fixture_with_raw_is_review_required(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    _fill_empty_image_paths(fixture.clean_root)

    report = assess_h300_sample_readiness(fixture.clean_root, raw_root=fixture.raw_root)

    assert report.overall_status == "review_required"
    assert report.summary["clean_required_files_present"] is True
    assert report.summary["frame_count"] == 5
    assert len(report.gap_statuses) == 12
    assert all(check.status != "block" for check in report.checks)
    assert _gap_status(report, "G-001").status == "ready_to_review"
    assert _gap_status(report, "G-002").status == "ready_to_review"
    assert _gap_status(report, "G-003").status == "needs_raw_review"
    assert _gap_status(report, "G-004").status == "needs_raw_review"
    assert _gap_status(report, "G-005").status == "needs_raw_review"
    assert _gap_status(report, "G-010").status == "needs_raw_review"
    assert _gap_status(report, "G-011").status == "needs_raw_review"
    assert _gap_status(report, "G-012").status == "needs_raw_review"
    payload = report.to_dict()
    assert payload["overall_status"] == "review_required"
    assert payload["gap_statuses"][0]["gap_id"] == "G-001"


def test_stage11_readiness_blocks_missing_required_clean_file(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    (fixture.clean_root / "process.csv").unlink()

    report = assess_h300_sample_readiness(fixture.clean_root, raw_root=fixture.raw_root)

    assert report.overall_status == "blocked"
    assert any(check.check_id == "clean_required:process.csv" and check.status == "block" for check in report.checks)


def test_stage11_readiness_blocks_missing_image_reference(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    _fill_empty_image_paths(fixture.clean_root)
    (fixture.clean_root / "images" / "front_0000.png").unlink()

    report = assess_h300_sample_readiness(fixture.clean_root, raw_root=fixture.raw_root)

    assert report.overall_status == "blocked"
    assert any(check.check_id == "frames:image_path" and check.status == "block" for check in report.checks)


def test_stage11_readiness_blocks_empty_image_reference(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    frames_path = fixture.clean_root / "frames.csv"
    rows = list(csv.DictReader(frames_path.open(newline="", encoding="utf-8")))
    for row in rows:
        row["image_path"] = "images/front_0000.png"
    rows[0]["image_path"] = ""
    with frames_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    report = assess_h300_sample_readiness(fixture.clean_root, raw_root=fixture.raw_root)

    assert report.overall_status == "blocked"
    assert any(check.check_id == "frames:image_path" and check.status == "block" for check in report.checks)


def test_stage11_readiness_clean_only_keeps_raw_gaps_blocked_without_blocking_overall(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    _fill_empty_image_paths(fixture.clean_root)

    report = assess_h300_sample_readiness(fixture.clean_root)

    assert report.overall_status == "review_required"
    assert _gap_status(report, "G-003").status == "blocked"
    assert _gap_status(report, "G-004").status == "blocked"
    assert _gap_status(report, "G-005").status == "blocked"
    assert _gap_status(report, "G-010").status == "needs_raw_review"
    assert _gap_status(report, "G-011").status == "blocked"
    assert _gap_status(report, "G-012").status == "blocked"


def test_stage11_readiness_raw_artifact_gaps_do_not_block_pipeline_smoke(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    _fill_empty_image_paths(fixture.clean_root)
    (fixture.raw_root / "manifest.raw.json").unlink()
    (fixture.raw_root / "files" / "model_outputs.json").unlink()

    report = assess_h300_sample_readiness(fixture.clean_root, raw_root=fixture.raw_root)

    assert report.overall_status == "review_required"
    assert _gap_status(report, "G-005").status == "blocked"
    assert any(check.check_id == "raw:manifest.raw.json" and check.status == "review" for check in report.checks)


def test_stage11_readiness_blocks_missing_timestamp_column(tmp_path: Path):
    fixture = generate_stage8_h300_synthetic_demo(tmp_path / "stage8_demo")
    frames_path = fixture.clean_root / "frames.csv"
    rows = list(csv.DictReader(frames_path.open(newline="", encoding="utf-8")))
    fieldnames = [field for field in rows[0] if field != "timestamp_s"]
    with frames_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row.pop("timestamp_s", None)
            writer.writerow(row)

    report = assess_h300_sample_readiness(fixture.clean_root)

    assert report.overall_status == "blocked"
    assert any(check.check_id == "frames:timestamp_s" and check.status == "block" for check in report.checks)
