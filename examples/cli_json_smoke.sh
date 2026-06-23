#!/usr/bin/env bash
set -euo pipefail

OUTPUT_ROOT="${1:-/tmp/b06_stage10_cli_json_smoke}"

python scripts/generate_stage8_h300_synthetic_demo.py --output-root "$OUTPUT_ROOT/fixture" --frames 5 >/dev/null

python scripts/physical_ai_package.py run-weld-workcell \
  --clean-root "$OUTPUT_ROOT/fixture/clean/weld_workcell" \
  --output-dir "$OUTPUT_ROOT/package" \
  --training-split eval \
  --output-rrd "$OUTPUT_ROOT/package.rrd" \
  --json \
  | python -c 'import json, sys
payload = json.load(sys.stdin)
assert payload["validation"]["ok"] is True
assert payload["summary"]["frame_count"] == 5
assert payload["package_root"]
print(json.dumps(payload, indent=2))'
