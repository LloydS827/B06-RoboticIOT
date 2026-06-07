import csv
from pathlib import Path

from rerun_stage2.query_export import export_candidate_rows
from rerun_stage2.sim_data import RecordingConfig, write_simulation_package


def test_export_candidate_rows_selects_high_risk_window(tmp_path: Path):
    package = write_simulation_package(
        tmp_path / "sim_weld_001",
        RecordingConfig(frame_count=20, random_seed=4),
    )
    output_csv = tmp_path / "candidate_rows.csv"

    written = export_candidate_rows(package.root, output_csv, min_defect_probability=0.55)

    rows = list(csv.DictReader(written.open(newline="", encoding="utf-8")))
    assert written == output_csv
    assert rows
    assert all(float(row["defect_probability"]) >= 0.55 for row in rows)
    assert {"sim_time_s", "tcp_x", "weld_current", "defect_probability", "event"}.issubset(rows[0])
