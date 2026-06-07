"""CSV candidate export before Catalog/DataFrame query workflows are introduced."""

from __future__ import annotations

import csv
from pathlib import Path


CANDIDATE_FIELDNAMES = [
    "sim_time_s",
    "robot_tick",
    "camera_frame",
    "weld_phase",
    "tcp_x",
    "tcp_y",
    "tcp_z",
    "weld_current",
    "weld_voltage",
    "wire_feed_speed",
    "weld_speed",
    "defect_probability",
    "event",
    "quality_label",
    "image_file",
]


def export_candidate_rows(
    package_root: Path,
    output_csv: Path,
    min_defect_probability: float = 0.5,
) -> Path:
    """Export high-risk frame rows as a stable CSV query baseline."""
    frames_csv = package_root / "frames.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    with frames_csv.open(newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        rows = [
            {fieldname: row[fieldname] for fieldname in CANDIDATE_FIELDNAMES}
            for row in reader
            if float(row["defect_probability"]) >= min_defect_probability
        ]

    with output_csv.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=CANDIDATE_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return output_csv
