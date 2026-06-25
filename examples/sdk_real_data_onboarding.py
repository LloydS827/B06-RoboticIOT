#!/usr/bin/env python3
"""Run candidate real/de-identified H300 Clean Zone onboarding."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from physical_ai_data import assess_h300_sample_readiness
from physical_ai_data.pipelines import run_weld_workcell_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run candidate H300 data onboarding.")
    parser.add_argument("--clean-root", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--training-split", default="eval")
    parser.add_argument("--output-rrd", type=Path)
    parser.add_argument("--no-copy-images", action="store_true")
    args = parser.parse_args(argv)

    report = assess_h300_sample_readiness(args.clean_root, raw_root=args.raw_root)
    if report.overall_status == "blocked":
        _print_payload(report=report.to_dict(), pipeline=None, error=None)
        return 2

    try:
        result = run_weld_workcell_pipeline(
            clean_root=args.clean_root,
            output_dir=args.output_root / "package",
            copy_images=not args.no_copy_images,
            training_split=args.training_split,
            output_rrd=args.output_rrd,
        )
    except Exception as exc:
        _print_payload(report=report.to_dict(), pipeline=None, error=str(exc))
        return 1

    _print_payload(report=report.to_dict(), pipeline=result.to_dict(), error=None)
    return 0


def _print_payload(
    *,
    report: dict[str, object],
    pipeline: dict[str, object] | None,
    error: str | None,
) -> None:
    print(
        json.dumps(
            {
                "readiness": report,
                "pipeline": pipeline,
                "output_index": _output_index(pipeline),
                "next_steps": _next_steps(str(report["overall_status"]), error=error),
                "error": error,
            },
            indent=2,
        )
    )


def _output_index(pipeline: dict[str, object] | None) -> dict[str, object] | None:
    if pipeline is None:
        return None
    return {
        "package_root": pipeline["package_root"],
        "candidates_csv": pipeline["candidates_csv"],
        "training_draft_dir": pipeline["training_draft_dir"],
        "rrd_path": pipeline["rrd_path"],
    }


def _next_steps(overall_status: str, *, error: str | None = None) -> list[str]:
    if error is not None:
        return [
            "Fix the pipeline error, then re-run this onboarding command.",
            "Keep the readiness report with the failure record for review.",
        ]
    if overall_status == "blocked":
        return [
            "Fix blocked Clean Zone checks before running the package pipeline.",
            "Re-run readiness after updating the candidate Clean/Raw roots.",
        ]
    if overall_status == "review_required":
        return [
            "Review readiness gap statuses against the Stage 8 synthetic-to-real gap register.",
            "Inspect generated package artifacts before using the candidate sample downstream.",
        ]
    return [
        "Review the package output index and validation summary.",
        "Keep real/de-identified source data in the approved controlled directory.",
    ]


if __name__ == "__main__":
    raise SystemExit(main())
