#!/usr/bin/env bash
set -euo pipefail

for py in /usr/local/python3.12/bin/python3.12 python3.14 python3.13 python3.12 python3; do
  command -v "$py" >/dev/null 2>&1 || continue
  "$py" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1 || continue
  printf '%s\n' "$py"
  exit 0
done

echo "ERROR: last30days requires Python 3.12+." >&2
exit 1
