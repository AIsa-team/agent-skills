#!/usr/bin/env python3
"""Check the case-sensitive Connect URLs promised by landing-page prompts.

Run locally with optional website workflow JSON files:
  python3 scripts/validate_connect_paths.py --website-content /path/to/en.json /path/to/zh.json
The default offline check protects the same file paths in this repository's CI.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
URL_PREFIX = "https://github.com/AIsa-team/agent-skills/blob/main/"
TREE_PREFIX = "https://github.com/AIsa-team/agent-skills/tree/main/"


def validate(root: Path, website_files: list[Path] | None = None) -> list[str]:
    issues: list[str] = []
    manifest = json.loads((root / "AIsa-connect/paths.json").read_text())
    if manifest.get("schema_version") != 1:
        return ["Unsupported Connect path manifest version"]
    entries = manifest.get("skills", [])
    by_slug = {e["slug"]: e for e in entries}
    if not entries or len(by_slug) != len(entries):
        issues.append("Connect paths must contain nonempty, unique slugs")
    folders = {p.parent.name for p in (root / "AIsa-connect").glob("*/SKILL.md")}
    if folders != set(by_slug):
        issues.append("Connect path manifest and Skill folders differ")
    for slug, entry in by_slug.items():
        expected = f"AIsa-connect/{slug}/SKILL.md"
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            issues.append(f"{slug}: invalid Skill slug")
        if entry["path"] != expected or entry["url"] != URL_PREFIX + expected:
            issues.append(f"{slug}: URL/path must match {URL_PREFIX + expected} exactly")
        parts = urlsplit(entry["url"])
        if parts.query or parts.fragment:
            issues.append(f"{slug}: Skill URL must not contain a query or fragment")
        target = root
        for part in Path(expected).parts:
            # macOS can resolve wrong-case paths that fail on GitHub/Linux.
            if not target.is_dir() or part not in {p.name for p in target.iterdir()}:
                issues.append(f"{slug}: missing exact-case path {expected}")
                break
            target /= part
        else:
            if not target.is_file():
                issues.append(f"{slug}: SKILL.md is not a regular file")
            elif re.search(r"(?m)^name: " + re.escape(slug) + r"\s*$", target.read_text()) is None:
                issues.append(f"{slug}: Skill name does not match its URL folder")
    for filename in website_files or []:
        data = json.loads(filename.read_text())
        workflows = data["workflows"]
        if set(workflows) != set(by_slug):
            issues.append(f"{filename.name}: workflow/Skill slugs differ")
        for slug, workflow in workflows.items():
            if slug not in by_slug:
                continue
            url = by_slug[slug]["url"]
            skill = workflow.get("skill", {})
            if skill.get("markdownUrl") != url:
                issues.append(f"{filename.name}/{slug}: markdownUrl differs from the repository path")
            if skill.get("githubUrl") != TREE_PREFIX + f"AIsa-connect/{slug}":
                issues.append(f"{filename.name}/{slug}: GitHub folder URL differs")
            prompts = [workflow.get("prompt", "")] + [p.get("text", "") for p in workflow.get("prompts", [])]
            for index, prompt in enumerate(prompts):
                rendered = prompt.replace("[SKILL.md URL]", str(skill.get("markdownUrl", "")))
                if url not in rendered:
                    issues.append(f"{filename.name}/{slug}: copied prompt {index} omits its Skill URL")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--website-content", type=Path, nargs="*", default=[])
    args = parser.parse_args()
    issues = validate(args.root, args.website_content)
    if issues:
        print("\n".join(issues))
        return 1
    print("Connect Skill URL paths passed" + (f"; matched {len(args.website_content)} website content files" if args.website_content else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
