#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1; then
    PYTHON="$py"
    break
  fi
done

if [ -z "${PYTHON:-}" ]; then
  echo "ERROR: last30days requires python3 or python on PATH." >&2
  exit 1
fi

cd "$ROOT"
exec "$PYTHON" "$ROOT/scripts/last30days.py" "$@"
