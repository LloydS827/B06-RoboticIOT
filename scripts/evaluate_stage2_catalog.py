#!/usr/bin/env python3
"""Run the Stage 2 local Catalog/DataFrame smoke probe."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rerun_stage2.catalog_eval import run_catalog_smoke


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    result = run_catalog_smoke(args.output_dir)
    output_path = args.output_dir / "catalog_eval_result.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote catalog evaluation result: {output_path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate local Rerun Catalog/DataFrame availability.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for generated smoke artifacts.")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
