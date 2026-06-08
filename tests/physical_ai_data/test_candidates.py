import csv
import json
from pathlib import Path

import pytest

from physical_ai_data.candidates import export_candidates, summarize_package
from physical_ai_data.samples import generate_pick_sort_package, generate_welding_package
from physical_ai_data.schema import CANDIDATE_COLUMNS


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _source_ids(rows: list[dict[str, str]]) -> str:
    return "|".join(row["source_id"] for row in rows)


def _candidate_with_source(rows: list[dict[str, str]], source_id: str) -> dict[str, str]:
    for row in rows:
        if source_id in row["source_id"].split("|"):
            return row
    raise AssertionError(f"Missing candidate for source_id {source_id}")


def test_invalid_package_raises_validation_summary(tmp_path: Path):
    with pytest.raises(ValueError, match="missing_manifest: Missing physical_ai_manifest.json"):
        summarize_package(tmp_path)

    with pytest.raises(ValueError, match="missing_manifest: Missing physical_ai_manifest.json"):
        export_candidates(tmp_path)


def test_export_welding_candidates_creates_stable_csv(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=18, random_seed=5)

    output = export_candidates(package, min_score=0.5)
    rows = _rows(output)

    assert output == package / "derived" / "candidates.csv"
    assert rows
    assert list(rows[0].keys()) == CANDIDATE_COLUMNS
    assert any(row["source_type"] in {"event", "metric", "mixed"} for row in rows)
    assert all(row["frame_id"] for row in rows if row["source_type"] != "label")


def test_export_pick_sort_candidates_includes_label_or_event(tmp_path: Path):
    package = generate_pick_sort_package(tmp_path / "pick", frame_count=12, random_seed=4)

    output = export_candidates(package, min_score=0.5)
    rows = _rows(output)

    assert rows
    assert any(row["source_type"] in {"event", "label", "mixed"} for row in rows)


def test_export_label_candidates_support_object_targets_and_confidence_threshold(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=8, random_seed=2)
    labels = _rows(package / "labels.csv")
    labels.extend(
        [
            {
                "label_id": "label_object_min_score",
                "label_type": "object_quality",
                "target_ref": "object:seam_001",
                "value": "review",
                "confidence": "0.5",
                "source": "test",
            },
            {
                "label_id": "label_low_confidence",
                "label_type": "object_quality",
                "target_ref": "object:seam_001",
                "value": "ignore",
                "confidence": "0.499",
                "source": "test",
            },
        ]
    )
    _write_rows(package / "labels.csv", labels)

    output = export_candidates(package, min_score=0.5)
    rows = _rows(output)
    object_candidate = _candidate_with_source(rows, "label_object_min_score")

    assert object_candidate["source_type"] == "label"
    assert object_candidate["frame_id"] == ""
    assert object_candidate["object_id"] == "seam_001"
    assert object_candidate["score"] == "0.5"
    assert "label_low_confidence" not in _source_ids(rows)


def test_export_metric_candidates_apply_keywords_and_numeric_threshold(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=8, random_seed=2)
    metrics = _rows(package / "metrics.csv")
    metrics.extend(
        [
            {
                "metric_id": "metric_test_probability_min",
                "timestamp_s": "0.0",
                "metric_name": "part_probability",
                "value": "0.5",
                "unit": "ratio",
                "source": "test",
            },
            {
                "metric_id": "metric_test_risk_high",
                "timestamp_s": "1.1429",
                "metric_name": "collision_risk",
                "value": "0.75",
                "unit": "ratio",
                "source": "test",
            },
            {
                "metric_id": "metric_test_success_high",
                "timestamp_s": "2.2857",
                "metric_name": "task_success",
                "value": "0.6",
                "unit": "ratio",
                "source": "test",
            },
            {
                "metric_id": "metric_test_temperature_high",
                "timestamp_s": "3.4286",
                "metric_name": "temperature",
                "value": "9.0",
                "unit": "C",
                "source": "test",
            },
            {
                "metric_id": "metric_test_confidence_low",
                "timestamp_s": "4.5714",
                "metric_name": "object_confidence",
                "value": "0.499",
                "unit": "ratio",
                "source": "test",
            },
        ]
    )
    _write_rows(package / "metrics.csv", metrics)

    output = export_candidates(package, min_score=0.5)
    source_ids = _source_ids(_rows(output))

    assert "metric_test_probability_min" in source_ids
    assert "metric_test_risk_high" in source_ids
    assert "metric_test_success_high" in source_ids
    assert "metric_test_temperature_high" not in source_ids
    assert "metric_test_confidence_low" not in source_ids


def test_export_merges_duplicate_frame_candidates_with_reasons(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=18, random_seed=5)

    output = export_candidates(package, min_score=0.5)
    rows = _rows(output)
    merged = _candidate_with_source(rows, "event_0001")

    assert merged["source_type"] == "mixed"
    assert "label_0000" in merged["source_id"]
    assert "metric_" in merged["source_id"]
    assert "event:porosity_risk" in merged["reasons"]
    assert "label:quality" in merged["reasons"]
    assert "metric:defect_probability" in merged["reasons"]


def test_export_ignores_non_finite_label_confidence_metric_value_and_timestamp(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=8, random_seed=2)
    labels = _rows(package / "labels.csv")
    labels.extend(
        [
            {
                "label_id": "label_nan_confidence",
                "label_type": "quality",
                "target_ref": "object:seam_001",
                "value": "review",
                "confidence": "nan",
                "source": "test",
            },
            {
                "label_id": "label_inf_confidence",
                "label_type": "quality",
                "target_ref": "object:seam_001",
                "value": "review",
                "confidence": "inf",
                "source": "test",
            },
        ]
    )
    _write_rows(package / "labels.csv", labels)

    metrics = _rows(package / "metrics.csv")
    metrics.extend(
        [
            {
                "metric_id": "metric_nan_value",
                "timestamp_s": "0.0",
                "metric_name": "quality_score",
                "value": "nan",
                "unit": "ratio",
                "source": "test",
            },
            {
                "metric_id": "metric_inf_value",
                "timestamp_s": "0.0",
                "metric_name": "quality_score",
                "value": "inf",
                "unit": "ratio",
                "source": "test",
            },
            {
                "metric_id": "metric_nan_timestamp",
                "timestamp_s": "nan",
                "metric_name": "quality_score",
                "value": "0.8",
                "unit": "ratio",
                "source": "test",
            },
            {
                "metric_id": "metric_inf_timestamp",
                "timestamp_s": "inf",
                "metric_name": "quality_score",
                "value": "0.9",
                "unit": "ratio",
                "source": "test",
            },
        ]
    )
    _write_rows(package / "metrics.csv", metrics)

    output = export_candidates(package, min_score=0.5)
    rows = _rows(output)
    source_ids = _source_ids(rows)

    assert "label_nan_confidence" not in source_ids
    assert "label_inf_confidence" not in source_ids
    assert "metric_nan_value" not in source_ids
    assert "metric_inf_value" not in source_ids
    assert _candidate_with_source(rows, "metric_nan_timestamp")["frame_id"] == ""
    assert _candidate_with_source(rows, "metric_inf_timestamp")["frame_id"] == ""


def test_export_candidates_does_not_match_nearest_frames_outside_sim_time(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=8, random_seed=2)
    manifest_path = package / "physical_ai_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["timelines"].append({"timeline_id": "controller_time", "unit": "s"})
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    frames = _rows(package / "frames.csv")
    for frame in frames:
        frame["timeline"] = "controller_time"
    _write_rows(package / "frames.csv", frames)

    events = _rows(package / "events.csv")
    for event in events:
        if event["event_id"] == "event_0001":
            event["related_frame_id"] = ""
    _write_rows(package / "events.csv", events)

    output = export_candidates(package, min_score=0.5)
    rows = _rows(output)

    nearest_candidates = [
        row
        for row in rows
        if "event_0001" in row["source_id"] or "defect_probability" in row["source_id"]
    ]
    assert nearest_candidates
    assert all(row["frame_id"] == "" for row in nearest_candidates)


def test_summarize_package_returns_counts(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=8, random_seed=2)

    summary = summarize_package(package)

    assert summary["package_id"] == "sample_robot_welding_station_seed_2_frames_8"
    assert summary["scenario_type"] == "robot_welding_station"
    assert summary["frame_count"] == 8
    assert summary["event_count"] == 3
    assert summary["label_count"] == 2
    assert summary["metric_count"] == 24
    assert summary["phases"] == ["approach", "finish", "welding"]
    assert summary["event_types"] == ["end", "porosity_risk", "start"]
    assert summary["label_types"] == ["quality"]
    assert summary["metric_names"] == ["defect_probability", "weld_current", "weld_voltage"]
