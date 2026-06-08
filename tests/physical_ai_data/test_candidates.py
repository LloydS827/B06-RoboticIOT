import csv
import json
from pathlib import Path

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

    assert summary["scenario_type"] == "robot_welding_station"
    assert summary["frame_count"] == 8
    assert summary["event_count"] >= 2
