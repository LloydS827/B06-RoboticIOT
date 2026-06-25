from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.lerobot_adapter import LeRobotPackageImporter
from physical_ai_data.pipelines import PipelineResult, run_weld_workcell_pipeline
from physical_ai_data.samples import generate_pick_sort_package, generate_welding_package
from physical_ai_data.schema import ValidationResult
from physical_ai_data.sdk import (
    convert_to_rerun,
    export_candidates_csv,
    export_training_eval_draft,
    summarize,
    validate,
)
from physical_ai_data.stage11_readiness import assess_h300_sample_readiness


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Physical AI Package data packages.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    generate = subcommands.add_parser("generate", help="Generate a deterministic sample package.")
    scenarios = generate.add_subparsers(dest="scenario", required=True)
    _add_generate_parser(scenarios, "welding", _generate_welding)
    _add_generate_parser(scenarios, "pick-sort", _generate_pick_sort)

    validate = subcommands.add_parser("validate", help="Validate a package.")
    validate.add_argument("package", type=Path, help="Package directory to validate.")
    validate.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    validate.set_defaults(func=_validate)

    summarize = subcommands.add_parser("summarize", help="Summarize a package.")
    summarize.add_argument("package", type=Path, help="Package directory to summarize.")
    summarize.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    summarize.set_defaults(func=_summarize)

    export = subcommands.add_parser("export-candidates", help="Export candidate rows from a package.")
    export.add_argument("package", type=Path, help="Package directory to export from.")
    export.add_argument("--output-csv", type=Path, help="Output CSV path. Defaults to PACKAGE/derived/candidates.csv.")
    export.add_argument("--min-score", type=float, default=0.5, help="Minimum candidate score.")
    export.set_defaults(func=_export_candidates)

    convert = subcommands.add_parser("convert-rerun", help="Convert a package to a Rerun .rrd file.")
    convert.add_argument("package", type=Path, help="Package directory to convert.")
    convert.add_argument("--output-rrd", type=Path, required=True, help="Output .rrd path.")
    convert.set_defaults(func=_convert_rerun)

    training = subcommands.add_parser("export-training-draft", help="Export a training/evaluation draft.")
    training.add_argument("package", type=Path, help="Package directory to export from.")
    training.add_argument("--output-dir", type=Path, help="Output directory. Defaults to PACKAGE/derived/training_eval.")
    training.add_argument("--split", default="unspecified", help="Split label to write into the draft.")
    training.set_defaults(func=_export_training_draft)

    run_weld = subcommands.add_parser(
        "run-weld-workcell",
        help="Import a clean weld workcell export and run package derivation steps.",
    )
    run_weld.add_argument("--clean-root", type=Path, required=True, help="Clean weld workcell root directory.")
    run_weld.add_argument("--output-dir", type=Path, required=True, help="Output package directory.")
    run_weld.add_argument(
        "--copy-images",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Copy image assets into the package.",
    )
    run_weld.add_argument("--no-candidates", action="store_true", help="Skip candidates CSV export.")
    run_weld.add_argument("--candidate-min-score", type=float, default=0.5, help="Minimum candidate score.")
    run_weld.add_argument("--training-split", default="unspecified", help="Split label for training draft export.")
    run_weld.add_argument("--output-rrd", type=Path, help="Optional output .rrd path.")
    run_weld.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    run_weld.set_defaults(func=_run_weld_workcell)

    readiness = subcommands.add_parser(
        "assess-h300-readiness",
        help="assess H300 Clean/Raw sample replacement readiness.",
    )
    readiness.add_argument("--clean-root", type=Path, required=True, help="Clean H300 sample root directory.")
    readiness.add_argument("--raw-root", type=Path, help="Optional Raw H300 sample root directory.")
    readiness.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    readiness.set_defaults(func=_assess_h300_readiness)

    import_lerobot = subcommands.add_parser("import-lerobot", help="Import a LeRobot episode into a Physical AI Package.")
    import_lerobot.add_argument("--repo-id", required=True, help="LeRobot repository ID.")
    import_lerobot.add_argument("--episode-index", type=int, required=True, help="Episode index to import.")
    import_lerobot.add_argument("--output-dir", type=Path, required=True, help="Output package directory.")
    import_lerobot.add_argument("--root", type=Path, help="Local LeRobot dataset root.")
    import_lerobot.add_argument(
        "--profile",
        default="auto",
        choices=["auto", "pusht", "aloha", "fallback"],
        help="Dataset mapping profile.",
    )
    import_lerobot.add_argument("--max-frames", type=int, help="Maximum frames to import.")
    import_lerobot.add_argument("--camera", help="Primary camera to import.")
    import_lerobot.set_defaults(func=_import_lerobot)

    return parser


def _add_generate_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    handler: Callable[[argparse.Namespace], int],
) -> None:
    parser = subparsers.add_parser(name, help=f"Generate a {name} sample package.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output package directory.")
    parser.add_argument("--frames", type=int, default=60, help="Number of frames to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation.")
    parser.set_defaults(func=handler)


def _generate_welding(args: argparse.Namespace) -> int:
    package = generate_welding_package(args.output_dir, frame_count=args.frames, random_seed=args.seed)
    print(f"Generated welding package: {package}")
    return 0


def _generate_pick_sort(args: argparse.Namespace) -> int:
    package = generate_pick_sort_package(args.output_dir, frame_count=args.frames, random_seed=args.seed)
    print(f"Generated pick-sort package: {package}")
    return 0


def _validate(args: argparse.Namespace) -> int:
    result = validate(args.package)
    payload = _validation_payload(args.package, result)
    if args.json:
        _print_json(payload)
    elif result.ok:
        print(f"Valid package: {args.package}")
        print(_format_summary(result.summary))
    else:
        print(f"Invalid package: {args.package}", file=sys.stderr)
        _print_messages(result.errors, file=sys.stderr)
    return 0 if result.ok else 1


def _summarize(args: argparse.Namespace) -> int:
    if args.json:
        validation = validate(args.package)
        if not validation.ok:
            _print_json(_validation_payload(args.package, validation))
            return 1

        _print_json(summarize(args.package))
        return 0

    summary = summarize(args.package)
    print(f"Package summary: {args.package}")
    print(_format_summary(summary))
    return 0


def _export_candidates(args: argparse.Namespace) -> int:
    output = export_candidates_csv(args.package, output_csv=args.output_csv, min_score=args.min_score)
    print(f"Wrote candidates: {output}")
    return 0


def _convert_rerun(args: argparse.Namespace) -> int:
    output = convert_to_rerun(args.package, args.output_rrd)
    print(f"Wrote Rerun recording: {output}")
    return 0


def _export_training_draft(args: argparse.Namespace) -> int:
    output = export_training_eval_draft(args.package, output_dir=args.output_dir, split=args.split)
    print(f"Wrote training/evaluation draft: {output}")
    return 0


def _run_weld_workcell(args: argparse.Namespace) -> int:
    result = run_weld_workcell_pipeline(
        clean_root=args.clean_root,
        output_dir=args.output_dir,
        copy_images=args.copy_images,
        export_candidates=not args.no_candidates,
        candidate_min_score=args.candidate_min_score,
        training_split=_normalize_training_split(args.training_split),
        output_rrd=args.output_rrd,
    )

    if args.json:
        _print_json(_pipeline_payload(result))
        return 0

    print(f"Wrote Physical AI Package: {result.package_root}")
    if result.candidates_csv is not None:
        print(f"Wrote candidates: {result.candidates_csv}")
    if result.training_draft_dir is not None:
        print(f"Wrote training/evaluation draft: {result.training_draft_dir}")
    if result.rrd_path is not None:
        print(f"Wrote Rerun recording: {result.rrd_path}")
    return 0


def _assess_h300_readiness(args: argparse.Namespace) -> int:
    report = assess_h300_sample_readiness(args.clean_root, raw_root=args.raw_root)
    if args.json:
        _print_json(report.to_dict())
        return 0

    _print_h300_readiness_text(report)
    return 0


def _print_h300_readiness_text(report) -> None:
    print(f"H300 readiness: {report.overall_status}")
    print(f"clean_root: {report.clean_root}")
    if report.raw_root is not None:
        print(f"raw_root: {report.raw_root}")

    non_pass_checks = [check for check in report.checks if check.status != "pass"]
    if non_pass_checks:
        print("Non-pass checks:")
        for check in non_pass_checks:
            detail = f"- {check.check_id}: {check.status} - {check.message}"
            if check.path is not None:
                detail = f"{detail} ({check.path})"
            print(detail)
    else:
        print("Non-pass checks: none")

    non_ready_gaps = [gap for gap in report.gap_statuses if gap.status != "ready_to_review"]
    if non_ready_gaps:
        print("Non-ready gaps:")
        for gap in non_ready_gaps:
            print(f"- gap {gap.gap_id}: {gap.status}")
            if gap.evidence:
                print(f"  evidence: {', '.join(gap.evidence)}")
            print(f"  next step: {gap.next_step}")
    else:
        print("Non-ready gaps: none")


def _import_lerobot(args: argparse.Namespace) -> int:
    if args.max_frames is not None and args.max_frames <= 0:
        raise ValueError("max_frames must be positive")

    request = ImportRequest(
        source_format="lerobot",
        source={
            "repo_id": args.repo_id,
            "episode_index": args.episode_index,
            "root": args.root,
        },
        output_dir=args.output_dir,
        options={
            "profile": args.profile,
            "max_frames": args.max_frames,
            "camera": args.camera,
        },
    )
    result = run_import(LeRobotPackageImporter(), request)
    print(f"Imported LeRobot episode to Physical AI Package: {result.package_root}")
    return 0


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2) + "\n", end="")


def _validation_payload(package: Path, result: ValidationResult) -> dict[str, object]:
    return {
        "ok": result.ok,
        "package": str(package),
        "summary": result.summary,
        "errors": [asdict(error) for error in result.errors],
        "warnings": [asdict(warning) for warning in result.warnings],
    }


def _pipeline_payload(result: PipelineResult) -> dict[str, object]:
    return result.to_dict()


def _normalize_training_split(split: str | None) -> str | None:
    if split is None:
        return "unspecified"
    value = split.strip()
    if value.lower() in {"", "none", "null"}:
        return None
    return value


def _format_summary(summary: dict[str, object]) -> str:
    fields = [
        "package_id",
        "scenario_type",
        "frame_count",
        "event_count",
        "label_count",
        "metric_count",
    ]
    return "\n".join(f"{field}: {summary.get(field, '')}" for field in fields)


def _print_messages(messages: list[object], file: object) -> None:
    for message in messages:
        code = getattr(message, "code", "")
        text = getattr(message, "message", "")
        path = getattr(message, "path", "")
        suffix = f" ({path})" if path else ""
        print(f"- {code}: {text}{suffix}", file=file)


if __name__ == "__main__":
    raise SystemExit(main())
