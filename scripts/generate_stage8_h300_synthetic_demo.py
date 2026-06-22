#!/usr/bin/env python3
"""Generate a deterministic Stage 8 H300 synthetic demo fixture."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic Stage 8 H300 synthetic demo fixture.")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=5)
    args = parser.parse_args(argv)
    result = generate_stage8_h300_synthetic_demo(args.output_root, frame_count=args.frames)
    print("Generated Stage 8 H300 synthetic demo")
    print(f"Root: {result.root}")
    print(f"Raw: {result.raw_root}")
    print(f"Clean: {result.clean_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
