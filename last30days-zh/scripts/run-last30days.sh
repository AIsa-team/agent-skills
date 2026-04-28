#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT"
if command -v python3.12 >/dev/null 2>&1; then
  PYTHON="python3.12"
elif [ -x /usr/local/python3.12/bin/python3.12 ]; then
  PYTHON="/usr/local/python3.12/bin/python3.12"
else
  PYTHON="python3"
fi
exec "$PYTHON" "$ROOT/scripts/last30days.py" "$@"
