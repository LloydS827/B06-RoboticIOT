#!/usr/bin/env python3
"""Import the Stage 8 weld workcell fixture with low-level importer APIs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from physical_ai_data.importers import ImportRequest, run_import
from physical_ai_data.stage8_h300_demo import generate_stage8_h300_synthetic_demo
from physical_ai_data.weld_workcell_importer import WeldWorkcellPackageImporter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the low-level weld workcell importer example.")
    parser.add_argument("--output-root", type=Path, default=Path("/tmp/b06_stage10_low_level_importer"))
    parser.add_argument("--frames", type=int, default=5)
    args = parser.parse_args(argv)

    fixture = generate_stage8_h300_synthetic_demo(args.output_root / "fixture", frame_count=args.frames)
    result = run_import(
        WeldWorkcellPackageImporter(),
        ImportRequest(
            source_format="weld_workcell",
            source={"root": fixture.clean_root},
            output_dir=args.output_root / "package",
            options={"copy_images": True},
        ),
    )

    print(
        json.dumps(
            {
                "package_root": str(result.package_root),
                "source_format": result.source_format,
                "source_id": result.source_id,
                "frame_count": result.frame_count,
                "warnings": result.warnings,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
