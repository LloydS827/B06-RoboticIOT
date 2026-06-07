#!/usr/bin/env python3
"""External-importer-style CLI for Stage 2 weld simulation packages."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rerun_stage2.rerun_writer import write_rrd


REQUIRED_INPUT_FILES = ("manifest.json", "frames.csv", "point_cloud.csv")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    missing_files = [name for name in REQUIRED_INPUT_FILES if not (args.input_dir / name).is_file()]
    if missing_files:
        missing = ", ".join(missing_files)
        print(f"Missing required input file(s) in {args.input_dir}: {missing}", file=sys.stderr)
        return 1

    try:
        output_rrd = write_rrd(args.input_dir, args.output_rrd)
    except Exception as exc:
        print(f"Failed to import simulation package: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote Rerun recording: {output_rrd}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a Stage 2 weld simulation package to a Rerun .rrd recording. "
            "This is an external-importer-style prototype, not the full Rerun external importer protocol."
        )
    )
    parser.add_argument("--input-dir", type=Path, required=True, help="Simulation package directory to import.")
    parser.add_argument("--output-rrd", type=Path, required=True, help="Output path for the Rerun .rrd recording.")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
