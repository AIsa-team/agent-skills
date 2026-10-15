#!/usr/bin/env bash
set -euo pipefail

if [ -n "${LAST30DAYS_PYTHON:-}" ]; then
  if ! command -v "$LAST30DAYS_PYTHON" >/dev/null 2>&1 || ! "$LAST30DAYS_PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
    echo "ERROR: LAST30DAYS_PYTHON must name an executable Python 3.11+ interpreter." >&2
    exit 1
  fi
  command -v "$LAST30DAYS_PYTHON"
  exit 0
fi

for py in /usr/local/python3.12/bin/python3.12 python3.14 python3.13 python3.12 python3.11 python3; do
  command -v "$py" >/dev/null 2>&1 || continue
  "$py" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1 || continue
  printf '%s\n' "$py"
  exit 0
done

echo "ERROR: last30days requires Python 3.11+." >&2
exit 1
