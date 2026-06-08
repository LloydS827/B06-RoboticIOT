from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from physical_ai_data.candidates import export_candidates, summarize_package
from physical_ai_data.rerun_adapter import write_rrd
from physical_ai_data.samples import generate_pick_sort_package, generate_welding_package
from physical_ai_data.validation import validate_package


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage CavLAB Physical AI data packages.")
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
    result = validate_package(args.package)
    payload = {
        "ok": result.ok,
        "package": str(args.package),
        "summary": result.summary,
        "errors": [asdict(error) for error in result.errors],
        "warnings": [asdict(warning) for warning in result.warnings],
    }
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
    summary = summarize_package(args.package)
    if args.json:
        _print_json(summary)
    else:
        print(f"Package summary: {args.package}")
        print(_format_summary(summary))
    return 0


def _export_candidates(args: argparse.Namespace) -> int:
    output = export_candidates(args.package, output_csv=args.output_csv, min_score=args.min_score)
    print(f"Wrote candidates: {output}")
    return 0


def _convert_rerun(args: argparse.Namespace) -> int:
    output = write_rrd(args.package, args.output_rrd)
    print(f"Wrote Rerun recording: {output}")
    return 0


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2) + "\n", end="")


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

