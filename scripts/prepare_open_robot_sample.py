#!/usr/bin/env python3
"""Prepare a small open robot comparison sample."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rerun_stage2.open_dataset import write_open_robot_sample


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    sample = write_open_robot_sample(args.output_dir)
    print(f"Wrote open robot sample: {sample}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare a Stage 2 open robot comparison sample.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for the generated sample.")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
