#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from physical_ai_data import inspect_h300_static_project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect an H300 static engineering project with the B06 SDK.")
    parser.add_argument("project_root", help="Local H300 static project directory to inspect.")
    args = parser.parse_args(argv)

    report = inspect_h300_static_project(args.project_root)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
