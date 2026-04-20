#!/usr/bin/env bash
# sync.sh - Safe local file sync helper
# Usage: bash scripts/sync.sh /absolute/or/relative/target-dir
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: bash scripts/sync.sh <target-dir>"
  exit 1
fi

SRC="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$1"
PYTHON="$("$SRC/scripts/dev-python.sh")"

mkdir -p "$TARGET/scripts/lib"
cp "$SRC/SKILL.md" "$TARGET/SKILL.md"
cp "$SRC/scripts/last30days.py" "$TARGET/scripts/"
cp "$SRC/scripts/watchlist.py" "$TARGET/scripts/"
cp "$SRC/scripts/briefing.py" "$TARGET/scripts/"
cp "$SRC/scripts/store.py" "$TARGET/scripts/"
cp "$SRC/scripts/lib/"*.py "$TARGET/scripts/lib/"

echo "Synced skill files to $TARGET"
(
  cd "$TARGET/scripts" &&
  "$PYTHON" -c "import briefing, store, watchlist; from lib import youtube_yt, render, ui; print('Import check: OK')"
)
