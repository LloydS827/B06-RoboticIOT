import csv
from pathlib import Path

from physical_ai_data.candidates import export_candidates, summarize_package
from physical_ai_data.samples import generate_pick_sort_package, generate_welding_package
from physical_ai_data.schema import CANDIDATE_COLUMNS


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


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


def test_summarize_package_returns_counts(tmp_path: Path):
    package = generate_welding_package(tmp_path / "weld", frame_count=8, random_seed=2)

    summary = summarize_package(package)

    assert summary["scenario_type"] == "robot_welding_station"
    assert summary["frame_count"] == 8
    assert summary["event_count"] >= 2
