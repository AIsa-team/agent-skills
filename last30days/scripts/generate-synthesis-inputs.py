#!/usr/bin/env python3
"""Legacy compatibility wrapper that renders compact markdown from saved reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from lib import render, schema

JSON_DIR = SCRIPT_DIR.parent / "outputs" / "json"
COMPACT_DIR = SCRIPT_DIR.parent / "outputs" / "compact"


def main() -> int:
    COMPACT_DIR.mkdir(parents=True, exist_ok=True)
    for json_path in sorted(JSON_DIR.glob("*.json")):
        report = schema.report_from_dict(json.loads(json_path.read_text()))
        output = f"# last30days v3.0.0: {report.topic}\n\n" + render.render_compact(report)
        out_path = COMPACT_DIR / f"{json_path.stem}.md"
        out_path.write_text(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
