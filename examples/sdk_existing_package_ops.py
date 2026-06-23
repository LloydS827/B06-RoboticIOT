#!/usr/bin/env python3
"""Run top-level SDK operations against an existing sample package."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from physical_ai_data.samples import generate_welding_package
from physical_ai_data.sdk import (
    convert_to_rerun,
    export_candidates_csv,
    export_training_eval_draft,
    summarize,
    validate,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SDK operations on a generated package.")
    parser.add_argument("--output-root", type=Path, default=Path("/tmp/b06_stage10_existing_package_ops"))
    parser.add_argument("--frames", type=int, default=5)
    args = parser.parse_args(argv)

    package_root = generate_welding_package(args.output_root / "package", frame_count=args.frames, random_seed=10)
    validation = validate(package_root)
    summary = summarize(package_root)
    candidates_csv = export_candidates_csv(package_root)
    training_draft_dir = export_training_eval_draft(package_root, split="eval")
    rrd_path = convert_to_rerun(package_root, args.output_root / "package.rrd")

    print(
        json.dumps(
            {
                "package_root": str(package_root),
                "validation_ok": validation.ok,
                "summary": summary,
                "candidates_csv": str(candidates_csv),
                "training_draft_dir": str(training_draft_dir),
                "rrd_path": str(rrd_path),
                "validation": {
                    "ok": validation.ok,
                    "summary": validation.summary,
                    "errors": [asdict(error) for error in validation.errors],
                    "warnings": [asdict(warning) for warning in validation.warnings],
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
