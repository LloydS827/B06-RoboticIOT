#!/usr/bin/env python3
"""Generate a deterministic Stage 7 simulated weld window fixture."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from physical_ai_data.stage7_sim_window import generate_stage7_sim_weld_window


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    result = generate_stage7_sim_weld_window(args.output_root, frame_count=args.frames)
    print("Generated Stage 7 simulated weld window")
    print(f"Root: {result.root}")
    print(f"Raw: {result.raw_root}")
    print(f"Clean: {result.clean_root}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a deterministic Stage 7 simulated weld window fixture.")
    parser.add_argument("--output-root", type=Path, required=True, help="Directory that will receive stage7_window/.")
    parser.add_argument("--frames", type=int, default=5, help="Number of frames to generate.")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
