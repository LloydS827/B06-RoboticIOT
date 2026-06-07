#!/usr/bin/env python3
"""Generate deterministic Stage 2 simulation artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rerun_stage2.sim_data import RecordingConfig, write_simulation_package


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.export_candidates:
        parser.error("--export-candidates is reserved for Task 3 and is not implemented yet.")

    config = RecordingConfig(frame_count=args.frames, random_seed=args.seed)
    package = write_simulation_package(args.output_dir, config)
    print(f"Wrote simulation package: {package.root}")

    if args.write_rrd:
        from rerun_stage2.rerun_writer import write_rrd

        output_rrd = args.output_rrd or (package.root.with_suffix(".rrd"))
        try:
            rrd_path = write_rrd(package.root, output_rrd)
        except Exception as exc:
            print(f"Failed to write Rerun recording: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(f"Wrote Rerun recording: {rrd_path}")

    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate deterministic Stage 2 weld simulation data.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for the generated data package.")
    parser.add_argument("--frames", type=int, default=120, help="Number of simulation frames to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic data generation.")
    parser.add_argument("--write-rrd", action="store_true", help="Also write a Rerun .rrd recording.")
    parser.add_argument("--output-rrd", type=Path, help="Output path for the optional Rerun .rrd recording.")
    parser.add_argument(
        "--export-candidates",
        action="store_true",
        help="Export candidate records. Reserved for Task 3.",
    )
    parser.add_argument("--candidate-csv", type=Path, help="Output CSV for Task 3 candidate export.")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
