#!/usr/bin/env python3
"""Version policy, runtime checks, reproducible bundles, and generated catalog."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
IGNORED = {".git", ".venv", "node_modules", "__pycache__"}


def check_publish_repository(repository: str) -> None:
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('invalid destination repository')
    if repository.split('/')[0].lower() != 'aisa-team':
        raise ValueError('CI publishing destinations must belong to AIsa-team')


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def version(text: str) -> str:
    from skills_ref.parser import parse_frontmatter

    metadata, _ = parse_frontmatter(text)
    value = metadata.get("metadata", {}).get("version", "")
    if not isinstance(value, str) or not SEMVER.fullmatch(value):
        raise ValueError("metadata.version must be a quoted MAJOR.MINOR.PATCH version")
    legacy = re.search(r'(?m)^    version: [\"\']?([^\"\'\s]+)', text.split('---', 2)[1])
    if legacy and legacy.group(1) != value:
        raise ValueError("legacy vendor version must match metadata.version; use the bump helper")
    return value


def skill_dirs(root: Path) -> list[Path]:
    config = read_json(root / ".github/skill-catalog.json")
    return sorted(p.parent for category in config["categories"]
                  for p in (root / category).glob("*/SKILL.md"))


def files(directory: Path) -> dict[str, bytes]:
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in sorted(directory.rglob("*")) if p.is_file()
            and not p.is_symlink() and not set(p.relative_to(directory).parts) & IGNORED
            and p.suffix not in {".pyc", ".pyo"}}


def payload(skill: Path) -> dict[str, bytes]:
    result = {f"{skill.name}/{name}": data for name, data in files(skill).items()}
    # Keep category-relative license links valid when unpacking one skill.
    if (skill.parent / "LICENSE").is_file():
        result["LICENSE"] = (skill.parent / "LICENSE").read_bytes()
    return result


def digest(content: dict[str, bytes]) -> str:
    value = hashlib.sha256()
    for name, data in sorted(content.items()):
        value.update(name.encode() + b"\0" + len(data).to_bytes(8, "big") + data)
    return value.hexdigest()


def substantive_content(content: dict[str, bytes]) -> dict[str, bytes]:
    """Version/changelog/maintenance-only changes do not refresh an old skill."""
    result = {}
    for name, data in content.items():
        if name in {"skill.json", "CHANGELOG.md"}:
            continue
        if name == "SKILL.md":
            parts = data.split(b'---', 2)
            if len(parts) == 3:
                front = re.sub(rb'(?m)^(?:  |    )version:.*\n', b'', parts[1])
                # The initial version can introduce an otherwise empty metadata
                # container. Neither it nor vendor version aliases are content.
                front = re.sub(rb'(?m)^metadata:[ \t]*\n(?=\s*\Z)', b'', front)
                data = parts[0] + b'---' + front + b'---' + parts[2]
        result[name] = data
    return result


def historic_files(root: Path, ref: str, relative: str) -> dict[str, bytes]:
    paths = git(root, "ls-tree", "-r", "--name-only", ref, "--", relative).splitlines()
    return {p[len(relative) + 1:]: subprocess.check_output(
        ["git", "show", f"{ref}:{p}"], cwd=root) for p in paths}


def validate(root: Path, reference: str | None = None) -> list[str]:
    issues = []
    config = read_json(root / '.github/skill-catalog.json')
    for category, settings in config['categories'].items():
        if settings.get('repository') is not None:
            try:
                check_publish_repository(settings['repository'])
            except ValueError as error:
                issues.append(f'.github/skill-catalog.json:{category}: {error}')
    upstreams = read_json(root / "maintenance/upstreams.json")
    for source_id, source in upstreams.items():
        if source.get("type") not in {"npm", "docs", "json", "openapi", "mcp"} or not source.get("url", "").startswith("https://"):
            issues.append(f"maintenance/upstreams.json: invalid source {source_id}")
    names: set[str] = set()
    skills = skill_dirs(root)
    known_paths = {s.relative_to(root).as_posix() for s in skills}
    reviews = read_json(root / 'maintenance/reviews.json')
    if not isinstance(reviews, dict):
        issues.append('maintenance/reviews.json: expected a skill-to-review mapping')
        reviews = {}
    for skill_id, review in reviews.items():
        try:
            if skill_id not in known_paths or not isinstance(review, dict):
                raise ValueError('review must refer to a current skill')
            instant = datetime.fromisoformat(review['verified_at'].replace('Z', '+00:00'))
            if instant.tzinfo is None or instant > datetime.now(timezone.utc) + timedelta(minutes=5):
                raise ValueError('verification timestamp must be timezone-aware and not in the future')
            if not review.get('evidence', '').strip() or not re.fullmatch('[a-f0-9]{64}', review.get('payload_sha256', '')):
                raise ValueError('review evidence and a SHA-256 bundle digest are required')
            if not isinstance(review.get('upstreams'), dict) or any(s not in upstreams or not re.fullmatch('[a-f0-9]{64}', h)
                    for s, h in review['upstreams'].items()):
                raise ValueError('review must record known upstream SHA-256 digests')
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            issues.append(f'maintenance/reviews.json:{skill_id}: {error}')
    if reference:
        git(root, "rev-parse", "--verify", f"{reference}^{{commit}}")
    for skill in skills:
        relative = skill.relative_to(root).as_posix()
        try:
            if skill.name in names:
                raise ValueError("skill names must be unique across categories for release tags")
            names.add(skill.name)
            current = version((skill / "SKILL.md").read_text())
            manifest = read_json(skill / "skill.json")
            if manifest.get("schema_version") != 1:
                raise ValueError("unsupported manifest schema_version")
            if not re.fullmatch(r"@[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)?", manifest.get("owner", "")):
                raise ValueError("owner must be a GitHub user or team")
            if not manifest.get("upstreams") or any(s not in upstreams for s in manifest["upstreams"]):
                raise ValueError("declare known upstream dependencies")
            languages = manifest.get("languages")
            if not isinstance(languages, list) or not set(languages) <= {"python", "shell", "javascript", "typescript"}:
                raise ValueError("invalid languages")
            detected = { {".py": "python", ".sh": "shell", ".js": "javascript", ".mjs": "javascript",
                         ".cjs": "javascript", ".ts": "typescript", ".tsx": "typescript"}[Path(p).suffix]
                        for p in files(skill) if Path(p).suffix in {".py", ".sh", ".js", ".mjs", ".cjs", ".ts", ".tsx"} }
            if not detected <= set(languages):
                raise ValueError(f"undeclared languages: {sorted(detected - set(languages))}")
            runtime = manifest.get("runtime")
            if not isinstance(runtime, dict) or any(not isinstance(v, str) or not v for v in runtime.values()):
                raise ValueError("runtime must map runtime names to version strings")
            if "python" in detected and "python" not in runtime or detected & {"typescript", "javascript"} and "node" not in runtime:
                raise ValueError("declare the required Python/Node runtime version")
            for entry in manifest.get("entrypoints", []):
                target = (skill / entry).resolve()
                if not target.is_relative_to(skill.resolve()) or not target.is_file():
                    raise ValueError(f"missing or unsafe entrypoint: {entry}")
            checks = manifest.get("checks")
            if not isinstance(checks, dict) or set(checks) - {"lint", "typecheck", "build", "test"}:
                raise ValueError("checks must declare lint/typecheck/build/test commands")
            for commands in checks.values():
                if not isinstance(commands, list) or any(not isinstance(c, list) or not c or
                        any(not isinstance(a, str) or not a for a in c) for c in commands):
                    raise ValueError("check commands must be arrays of arguments, not shell strings")
            if "typescript" in detected:
                if not (skill / "package.json").is_file() or not (skill / "package-lock.json").is_file():
                    raise ValueError("TypeScript requires a local package.json and package-lock.json")
                if not checks.get("typecheck") or not checks.get("build") or not checks.get("test"):
                    raise ValueError("TypeScript requires typecheck, build, and test commands")
                if not any(Path(p).suffix in {".js", ".mjs", ".cjs"} for p in manifest.get("entrypoints", [])):
                    raise ValueError("TypeScript must ship a built JavaScript entrypoint")
            if (skill / "package.json").is_file():
                package = read_json(skill / "package.json")
                if package.get("version") != current:
                    raise ValueError("package.json version must match metadata.version")
                if not package.get("engines", {}).get("node") or not (skill / "package-lock.json").is_file():
                    raise ValueError("Node packages require engines.node and a package-lock.json")
                lock = read_json(skill / "package-lock.json")
                if lock.get("version") != current or lock.get("packages", {}).get("", {}).get("version") != current:
                    raise ValueError("package-lock.json root version must match metadata.version")
                dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
                if any(str(v).startswith(("workspace:", "file:", "link:")) for v in dependencies.values()):
                    raise ValueError("Node dependencies must not import the source workspace")
            changelog = (skill / "CHANGELOG.md").read_text()
            if f"## {current}\n" not in changelog:
                raise ValueError("CHANGELOG.md must describe the current version")
            if reference:
                old = historic_files(root, reference, relative)
                # Existing unversioned skills are bootstrapped once by this migration.
                if "skill.json" in old:
                    previous = version(old["SKILL.md"].decode())
                    license_path = f"{skill.parent.relative_to(root).as_posix()}/LICENSE"
                    license_result = subprocess.run(["git", "show", f"{reference}:{license_path}"], cwd=root, capture_output=True)
                    license_changed = (skill.parent / "LICENSE").is_file() and license_result.stdout != (skill.parent / "LICENSE").read_bytes()
                    if files(skill) != old or license_changed:
                        if tuple(map(int, current.split('.'))) <= tuple(map(int, previous.split('.'))):
                            raise ValueError("changed bundle requires a strictly higher version")
                        if old.get("CHANGELOG.md") == (skill / "CHANGELOG.md").read_bytes():
                            raise ValueError("changed bundle requires a changelog entry")
            tag = f"skills/{skill.name}/v{current}"
            if git(root, "tag", "--list", tag):
                previous_payload = {f"{skill.name}/{p}": data for p, data in historic_files(root, tag, relative).items()}
                license_path = f"{skill.parent.relative_to(root).as_posix()}/LICENSE"
                license_result = subprocess.run(["git", "show", f"{tag}:{license_path}"], cwd=root, capture_output=True)
                if license_result.returncode == 0:
                    previous_payload["LICENSE"] = license_result.stdout
                if digest(previous_payload) != digest(payload(skill)):
                    raise ValueError(f"immutable version already exists: {tag}")
        except (ValueError, KeyError, TypeError, OSError) as error:
            issues.append(f"{relative}: {error}")
    return issues


def bump(root: Path, skill_id: str, part: str, message: str) -> str:
    skill = next((s for s in skill_dirs(root) if s.relative_to(root).as_posix() == skill_id), None)
    if skill is None or not message.strip():
        raise ValueError("a known skill and changelog message are required")
    path = skill / "SKILL.md"
    text = path.read_text()
    previous = version(text)
    numbers = list(map(int, previous.split('.')))
    index = {"major": 0, "minor": 1, "patch": 2}[part]
    numbers[index] += 1
    numbers[index + 1:] = [0] * (2 - index)
    current = '.'.join(map(str, numbers))
    front, body = text.split('---', 2)[1:]
    front = re.sub(r'(?m)^(  |    )version:.*$', lambda m: f'{m.group(1)}version: "{current}"', front)
    path.write_text('---' + front + '---' + body)
    changelog = skill / "CHANGELOG.md"
    changelog.write_text(changelog.read_text().replace('# Changelog\n', f'# Changelog\n\n## {current}\n\n- {message.strip()}\n', 1))
    if (skill / "package.json").is_file():
        package = read_json(skill / "package.json")
        package["version"] = current
        write_json(skill / "package.json", package)
        lock = read_json(skill / "package-lock.json")
        lock["version"] = current
        lock["packages"][""]["version"] = current
        write_json(skill / "package-lock.json", lock)
    return current


def changed_skills(root: Path, reference: str | None) -> list[Path]:
    if not reference:
        return skill_dirs(root)
    changed = set(git(root, "diff", "--name-only", reference, "HEAD", "--").splitlines())
    # Shared tooling changes require exercising all bundles.
    if any(p.startswith((".github/scripts/", ".github/skill-catalog", "maintenance/")) for p in changed):
        return skill_dirs(root)
    return [s for s in skill_dirs(root) if any(p.startswith(s.relative_to(root).as_posix() + "/")
            or p == s.parent.relative_to(root).as_posix() + "/LICENSE" for p in changed)]


def run_checks(root: Path, reference: str | None = None) -> None:
    """Run checks in isolated exports; no cross-skill imports can accidentally work."""
    for skill in changed_skills(root, reference):
        manifest = read_json(skill / "skill.json")
        if not any(manifest["checks"].values()):
            continue
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            for name, data in payload(skill).items():
                target = stage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                target.chmod(0o755 if data.startswith(b'#!') else 0o644)
            directory = stage / skill.name
            environment = {k: v for k, v in os.environ.items()
                           if k not in {"AISA_API_KEY", "GITHUB_TOKEN", "GH_TOKEN", "SYNC_AISA_SKILLS_TOKEN", "PYTHONPATH", "NODE_PATH"}}
            if (directory / "package.json").is_file():
                subprocess.run(["npm", "ci", "--ignore-scripts", "--engine-strict", "--no-audit", "--no-fund"],
                               cwd=directory, env=environment, check=True, timeout=300)
            before = files(directory)
            for kind in ("lint", "typecheck", "build", "test"):
                for command in manifest["checks"].get(kind, []):
                    argv = [sys.executable if a == "{python}" else a for a in command]
                    print(f"Checking {skill.name}: {kind}", flush=True)
                    subprocess.run(argv, cwd=directory, env=environment, check=True, timeout=300)
                if kind == "build" and manifest["checks"].get(kind) and before != files(directory):
                    raise ValueError(f"{skill.name}: build output differs from the checked-in distribution")


def catalog_text(root: Path) -> str:
    config = read_json(root / ".github/skill-catalog.json")
    text = "<!-- catalog:start -->\n\n| Category | Skills | Description |\n|---|---:|---|\n"
    for category, info in config["categories"].items():
        count = len(list((root / category).glob("*/SKILL.md")))
        text += f"| [{info['name']}](./{category}/) | {count} | {info['description']} |\n"
    text += f"\nThis catalog contains **{len(skill_dirs(root))} skills**.\n\n<!-- catalog:end -->"
    return text


def skill_table(root: Path, category: str, prefix: str) -> str:
    from skills_ref.parser import parse_frontmatter

    text = '| Skill | Version | Description |\n|---|---|---|\n'
    for path in sorted((root / category).glob('*/SKILL.md')):
        properties, _ = parse_frontmatter(path.read_text())
        description = properties['description'].replace('|', '\\|').replace('\n', ' ')
        text += f'| [{path.parent.name}]({prefix}{path.parent.name}/) | {version(path.read_text())} | {description} |\n'
    return text


def generate_catalog(root: Path, check: bool = False) -> None:
    path = root / "README.md"
    text = path.read_text()
    updated = re.sub(r"<!-- catalog:start -->.*?<!-- catalog:end -->", lambda _: catalog_text(root), text, flags=re.S)
    if updated == text and "<!-- catalog:start -->" not in text:
        raise ValueError("README.md is missing generated catalog markers")
    config = read_json(root / '.github/skill-catalog.json')
    tables = '<!-- skills:start -->\n'
    for category, info in config['categories'].items():
        tables += f"\n### [{info['name']}](./{category}/)\n\n" + skill_table(root, category, f'./{category}/')
    tables += '\n<!-- skills:end -->'
    updated = re.sub(r'<!-- skills:start -->.*?<!-- skills:end -->', lambda _: tables, updated, flags=re.S)
    if check and updated != text:
        raise ValueError("catalog counts are stale; run skill_lifecycle.py catalog")
    if not check:
        path.write_text(updated)
    for category in config['categories']:
        category_doc = root / category / 'README.md'
        if not category_doc.exists():
            continue
        before = category_doc.read_text()
        count = len(list((root / category).glob('*/SKILL.md')))
        replacement = f'<!-- category:start -->\n\nThis category contains {count} self-contained Agent Skills.\n\n'
        replacement += skill_table(root, category, './') + '\n<!-- category:end -->'
        after = re.sub(r'<!-- category:start -->.*?<!-- category:end -->', lambda _: replacement, before, flags=re.S)
        if '<!-- category:start -->' not in before:
            raise ValueError(f'{category_doc}: missing generated category markers')
        if check and after != before:
            raise ValueError(f'{category_doc}: stale category catalog')
        if not check:
            category_doc.write_text(after)


def bundle(root: Path, output: Path) -> list[dict[str, Any]]:
    output.mkdir(parents=True, exist_ok=True)
    commit = git(root, "rev-parse", "HEAD")
    releases = []
    for skill in skill_dirs(root):
        current = version((skill / "SKILL.md").read_text())
        name = f"{skill.name}-{current}.tar.gz"
        content = payload(skill)
        with (output / name).open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w") as archive:
                    for path, data in sorted(content.items()):
                        info = tarfile.TarInfo(path)
                        info.size = len(data)
                        info.mode = 0o755 if data.startswith(b"#!") else 0o644
                        archive.addfile(info, io.BytesIO(data))
        release = {"skill": skill.name, "version": current, "source_commit": commit,
                   "tag": f"skills/{skill.name}/v{current}", "archive": name,
                   "payload_sha256": digest(content),
                   "archive_sha256": hashlib.sha256((output / name).read_bytes()).hexdigest()}
        write_json(output / f"{skill.name}-{current}.json", release)
        releases.append(release)
    write_json(output / "catalog.json", releases)
    (output / "SHA256SUMS").write_text("".join(f"{r['archive_sha256']}  {r['archive']}\n" for r in releases))
    return releases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    policy = commands.add_parser("validate")
    policy.add_argument("--changed-from")
    checks = commands.add_parser("checks")
    checks.add_argument("--changed-from")
    catalog = commands.add_parser("catalog")
    catalog.add_argument("--check", action="store_true")
    package = commands.add_parser("bundle")
    package.add_argument("--output", type=Path, required=True)
    update = commands.add_parser("bump")
    update.add_argument("--skill", required=True)
    update.add_argument("--part", choices=("major", "minor", "patch"), required=True)
    update.add_argument("--message", required=True)
    args = parser.parse_args()
    if args.command == "validate":
        issues = validate(args.root, args.changed_from)
        print("\n".join(issues) if issues else "Skill lifecycle checks passed")
        return int(bool(issues))
    if args.command == "checks":
        run_checks(args.root, args.changed_from)
    elif args.command == "catalog":
        generate_catalog(args.root, args.check)
    elif args.command == "bundle":
        bundle(args.root, args.output)
    elif args.command == "bump":
        print(bump(args.root, args.skill, args.part, args.message))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
