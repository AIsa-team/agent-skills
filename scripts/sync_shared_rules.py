#!/usr/bin/env python3
"""Inject or refresh the shared AIsa rules block in every skill's SKILL.md.

The source block lives in ``_shared/aisa-rules.md`` between
``<!-- aisa-rules:start -->`` and ``<!-- aisa-rules:end -->``. Each skill's
``SKILL.md`` carries the same block between the same markers so the rule text
exists exactly once in the repository and once per installed skill bundle.

* A skill that already has the markers gets its block replaced in place.
* A skill without the markers gets the block inserted after its first H1
  heading (or directly after the frontmatter when there is no H1).

Usage::

    python3 scripts/sync_shared_rules.py          # rewrite stale/missing blocks
    python3 scripts/sync_shared_rules.py --check  # exit 1 when any SKILL.md is stale

``scripts/validate_skills.py`` performs the same comparison and fails CI when a
block drifts from the source.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "_shared" / "aisa-rules.md"
START = "<!-- aisa-rules:start -->"
END = "<!-- aisa-rules:end -->"


def source_block(path: Path = SOURCE) -> str:
    text = path.read_text(encoding="utf-8")
    start, end = text.find(START), text.find(END)
    if start < 0 or end < 0 or end < start:
        raise SystemExit(f"error: {path} must contain one {START} ... {END} block")
    return text[start:end + len(END)]


def skill_files(root: Path) -> list[Path]:
    config = json.loads((root / ".github/skill-catalog.json").read_text(encoding="utf-8"))
    return sorted(path for category in config["categories"] for path in (root / category).glob("*/SKILL.md"))


def frontmatter_end(text: str) -> int:
    """Index just past the closing ``---`` line of the YAML frontmatter, else 0."""
    if not text.startswith("---"):
        return 0
    match = re.search(r"(?m)^---[ \t]*$", text[3:])
    return 3 + match.end() + 1 if match else 0


def apply(text: str, block: str) -> str:
    starts = [m.start() for m in re.finditer(re.escape(START), text)]
    ends = [m.end() for m in re.finditer(re.escape(END), text)]
    if starts or ends:
        if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
            raise ValueError("malformed rules markers; expected exactly one start before one end")
        return text[:starts[0]] + block + text[ends[0]:]
    body_start = frontmatter_end(text)
    heading = re.compile(r"(?m)^# .*$").search(text, body_start)
    if heading:
        insert_at = heading.end()
        # Keep the heading's own blank line, then the block, then a blank line.
        return text[:insert_at].rstrip("\n") + "\n\n" + block + "\n\n" + text[insert_at:].lstrip("\n")
    return text[:body_start].rstrip("\n") + "\n\n" + block + "\n\n" + text[body_start:].lstrip("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="report stale skills without writing")
    args = parser.parse_args(argv)

    block = source_block(args.root / "_shared" / "aisa-rules.md")
    stale: list[str] = []
    for path in skill_files(args.root):
        original = path.read_text(encoding="utf-8")
        try:
            updated = apply(original, block)
        except ValueError as error:
            print(f"{path.relative_to(args.root)}: {error}", file=sys.stderr)
            return 2
        if updated == original:
            continue
        stale.append(path.relative_to(args.root).as_posix())
        if not args.check:
            path.write_text(updated, encoding="utf-8")
    if args.check:
        for name in stale:
            print(f"stale: {name}")
        print(f"{len(stale)} SKILL.md file(s) need scripts/sync_shared_rules.py" if stale else "All shared rules blocks are current")
        return 1 if stale else 0
    for name in stale:
        print(f"updated: {name}")
    print(f"{len(stale)} SKILL.md file(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
