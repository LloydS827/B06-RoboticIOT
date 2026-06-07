"""Local Rerun Catalog and DataFrame/Chunk smoke probes."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from rerun_stage2.query_export import export_candidate_rows
from rerun_stage2.rerun_writer import write_rrd
from rerun_stage2.sim_data import RecordingConfig, SimulationPackage, write_simulation_package


def run_catalog_smoke(root: Path) -> dict[str, Any]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    packages = _write_packages(root)

    catalog_attempt = _try_catalog(root, packages)
    dataframe_attempt = _try_dataframe_chunks(root, packages)
    queried_rows = catalog_attempt.get("queried_rows", 0) + dataframe_attempt.get("queried_rows", 0)

    if catalog_attempt["status"] == "ok" or dataframe_attempt["status"] == "ok":
        return {
            "status": "ok",
            "catalog_attempt": catalog_attempt,
            "dataframe_attempt": dataframe_attempt,
            "segments": len(packages),
            "queried_rows": queried_rows,
        }

    return {
        "status": "not_available",
        "catalog_attempt": catalog_attempt,
        "dataframe_attempt": dataframe_attempt,
        "segments": len(packages),
        "queried_rows": queried_rows,
        "fallback": "csv_candidate_export_verified",
    }


def _write_packages(root: Path) -> list[SimulationPackage]:
    packages = []
    for index in range(2):
        config = RecordingConfig(frame_count=24, random_seed=42 + index, batch_id=f"batch_stage2_catalog_{index}")
        packages.append(write_simulation_package(root / f"segment_{index}", config))
    return packages


def _try_catalog(root: Path, packages: list[SimulationPackage]) -> dict[str, Any]:
    try:
        import pyarrow as pa
        import rerun as rr

        rows = _candidate_rows(root, packages)
        schema = pa.schema(
            [
                ("segment", pa.string()),
                ("sim_time_s", pa.float64()),
                ("camera_frame", pa.int64()),
                ("defect_probability", pa.float64()),
                ("quality_label", pa.string()),
            ]
        )

        server = rr.server.Server()
        try:
            client = server.client()
            table = client.create_table("stage2_catalog_candidates", schema, url=None)
            if rows:
                table.append([_rows_to_batch(pa, rows)])
            queried_rows = sum(batch.num_rows for batch in table.to_arrow_reader())
            return {
                "status": "ok",
                "reason": f"created local Catalog table via {server.url()}",
                "table_names": client.table_names(),
                "queried_rows": queried_rows,
            }
        finally:
            server.shutdown()
    except Exception as exc:
        return {
            "status": "not_available",
            "reason": f"{type(exc).__name__}: {exc}",
            "queried_rows": 0,
        }


def _candidate_rows(root: Path, packages: list[SimulationPackage]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidates_dir = root / "candidates"
    candidates_dir.mkdir(exist_ok=True)
    for index, package in enumerate(packages):
        candidate_csv = export_candidate_rows(package.root, candidates_dir / f"segment_{index}_candidates.csv")
        with candidate_csv.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                rows.append(
                    {
                        "segment": f"segment_{index}",
                        "sim_time_s": float(row["sim_time_s"]),
                        "camera_frame": int(row["camera_frame"]),
                        "defect_probability": float(row["defect_probability"]),
                        "quality_label": row["quality_label"],
                    }
                )
    return rows


def _rows_to_batch(pa: Any, rows: list[dict[str, Any]]) -> Any:
    return pa.record_batch(
        [
            pa.array([row["segment"] for row in rows], type=pa.string()),
            pa.array([row["sim_time_s"] for row in rows], type=pa.float64()),
            pa.array([row["camera_frame"] for row in rows], type=pa.int64()),
            pa.array([row["defect_probability"] for row in rows], type=pa.float64()),
            pa.array([row["quality_label"] for row in rows], type=pa.string()),
        ],
        names=["segment", "sim_time_s", "camera_frame", "defect_probability", "quality_label"],
    )


def _try_dataframe_chunks(root: Path, packages: list[SimulationPackage]) -> dict[str, Any]:
    try:
        import rerun as rr

        rrd_paths = []
        for index, package in enumerate(packages):
            rrd_paths.append(write_rrd(package.root, root / f"segment_{index}.rrd"))

        if hasattr(rr, "experimental") and hasattr(rr.experimental, "RrdReader"):
            queried_rows = 0
            chunk_count = 0
            for rrd_path in rrd_paths:
                chunks = rr.experimental.RrdReader(rrd_path).stream().to_chunks()
                queried_rows += sum(chunk.num_rows for chunk in chunks)
                chunk_count += len(chunks)
            return {
                "status": "ok",
                "reason": "queried .rrd chunks via rerun.experimental.RrdReader.stream",
                "rrd_files": [str(path) for path in rrd_paths],
                "chunks": chunk_count,
                "queried_rows": queried_rows,
            }

        if hasattr(rr, "recording") and hasattr(rr.recording, "load_recording"):
            queried_rows = 0
            chunk_count = 0
            for rrd_path in rrd_paths:
                recording = rr.recording.load_recording(rrd_path)
                chunks = list(recording.chunks())
                queried_rows += sum(chunk.num_rows for chunk in chunks)
                chunk_count += len(chunks)
            return {
                "status": "ok",
                "reason": "queried .rrd chunks via rerun.recording.load_recording",
                "rrd_files": [str(path) for path in rrd_paths],
                "chunks": chunk_count,
                "queried_rows": queried_rows,
            }

        return {
            "status": "not_available",
            "reason": "Rerun SDK has no experimental.RrdReader or recording.load_recording API",
            "queried_rows": 0,
        }
    except Exception as exc:
        return {
            "status": "not_available",
            "reason": f"{type(exc).__name__}: {exc}",
            "queried_rows": 0,
        }
