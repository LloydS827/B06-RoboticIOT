#!/usr/bin/env python3
"""Run the Stage 8 weld workcell fixture through the SDK pipeline."""

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

from physical_ai_data.pipelines import PipelineResult, run_weld_workcell_pipeline
from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Stage 8 SDK pipeline example.")
    parser.add_argument("--output-root", type=Path, default=Path("/tmp/b06_stage10_sdk_pipeline"))
    parser.add_argument("--frames", type=int, default=5)
    args = parser.parse_args(argv)

    fixture = generate_stage8_h300_synthetic_demo(args.output_root / "fixture", frame_count=args.frames)
    result = run_weld_workcell_pipeline(
        clean_root=fixture.clean_root,
        output_dir=args.output_root / "package",
        training_split="eval",
        output_rrd=args.output_root / "package.rrd",
    )
    print(json.dumps(_payload(result), indent=2))
    return 0


def _payload(result: PipelineResult) -> dict[str, object]:
    return {
        "package_root": str(result.package_root),
        "validation_ok": result.validation.ok,
        "summary": result.summary,
        "candidates_csv": _optional_path(result.candidates_csv),
        "training_draft_dir": _optional_path(result.training_draft_dir),
        "rrd_path": _optional_path(result.rrd_path),
        "validation": {
            "ok": result.validation.ok,
            "summary": result.validation.summary,
            "errors": [asdict(error) for error in result.validation.errors],
            "warnings": [asdict(warning) for warning in result.validation.warnings],
        },
    }


def _optional_path(path: Path | None) -> str | None:
    return str(path) if path is not None else None


if __name__ == "__main__":
    raise SystemExit(main())
