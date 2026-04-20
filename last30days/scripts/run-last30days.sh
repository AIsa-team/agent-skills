#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$("$ROOT/scripts/dev-python.sh")"

cd "$ROOT"
exec "$PYTHON" "$ROOT/scripts/last30days.py" "$@"
