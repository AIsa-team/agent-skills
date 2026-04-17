#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$("$ROOT/scripts/dev-python.sh")"

cd "$ROOT"
exec "$PYTHON" -m pytest --capture=no "$@"
