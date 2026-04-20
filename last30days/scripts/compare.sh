#!/bin/bash
# Safe local comparison helper for last30days.
# Usage: bash scripts/compare.sh "Kanye West"

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Usage: bash scripts/compare.sh <topic>"
  echo "  Example: bash scripts/compare.sh Kevin Rose"
  exit 1
fi

TOPIC="$*"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${LAST30DAYS_COMPARE_DIR:-$ROOT/.last30days-compare}"

mkdir -p "$OUT_DIR"

echo "=============================================="
echo " Local compare: $TOPIC"
echo " Output dir: $OUT_DIR"
echo "=============================================="
echo ""

echo "[1/2] Running quick profile..."
bash "$ROOT/scripts/run-last30days.sh" "$TOPIC" --emit=json --quick > "$OUT_DIR/quick.json"
echo "  ✓ Wrote $OUT_DIR/quick.json"
echo ""

echo "[2/2] Running deep profile..."
bash "$ROOT/scripts/run-last30days.sh" "$TOPIC" --emit=json --deep > "$OUT_DIR/deep.json"
echo "  ✓ Wrote $OUT_DIR/deep.json"
echo ""

echo "Compare these files:"
echo "  $OUT_DIR/quick.json"
echo "  $OUT_DIR/deep.json"
