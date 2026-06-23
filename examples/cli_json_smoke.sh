#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python}"
OUTPUT_ROOT="${1:-/tmp/b06_stage10_cli_json_smoke}"

"$PYTHON" "$ROOT/scripts/generate_stage8_h300_synthetic_demo.py" --output-root "$OUTPUT_ROOT/fixture" --frames 5 >/dev/null

"$PYTHON" "$ROOT/scripts/physical_ai_package.py" run-weld-workcell \
  --clean-root "$OUTPUT_ROOT/fixture/clean/weld_workcell" \
  --output-dir "$OUTPUT_ROOT/package" \
  --training-split eval \
  --output-rrd "$OUTPUT_ROOT/package.rrd" \
  --json \
  | "$PYTHON" -c 'import json, sys
payload = json.load(sys.stdin)
if payload["validation"]["ok"] is not True:
    raise SystemExit("validation failed")
if payload["summary"]["frame_count"] != 5:
    raise SystemExit("unexpected frame_count")
if not payload["package_root"]:
    raise SystemExit("missing package_root")
print(json.dumps(payload, indent=2))'
