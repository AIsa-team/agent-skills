#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$(bash "$ROOT/scripts/dev-python.sh")"

exec "$PYTHON" "$ROOT/scripts/briefing.py" "$@"
