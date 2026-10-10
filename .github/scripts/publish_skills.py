#!/usr/bin/env python3
"""Publish validated artifacts and normal commits from an exact source revision."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from skill_lifecycle import ROOT, files, git, read_json, write_json


def publish_releases(artifacts: Path, repo: str, expected_commit: str | None = None) -> None:
    for release in read_json(artifacts / "catalog.json"):
        archive = artifacts / release['archive']
        if hashlib.sha256(archive.read_bytes()).hexdigest() != release['archive_sha256']:
            raise ValueError("validated archive checksum does not match")
        if expected_commit and release['source_commit'] != expected_commit:
            raise ValueError("artifact source revision does not match this workflow")
        tag = release["tag"]
        filename = f"{release['skill']}-{release['version']}.json"
        exists = subprocess.run(["gh", "api", f"repos/{repo}/git/ref/tags/{tag}"], capture_output=True, text=True)
        if exists.returncode:
            # A network/auth failure must never be interpreted as an absent release.
            if "HTTP 404" not in exists.stderr:
                raise RuntimeError("unable to inspect release tag")
            # Create the immutable tag before a draft release. GitHub may defer
            # creating a draft's tag until publication, making retries ambiguous.
            with tempfile.TemporaryDirectory() as temporary:
                tag_body = Path(temporary) / 'tag.json'
                write_json(tag_body, {'ref': f'refs/tags/{tag}', 'sha': release['source_commit']})
                subprocess.run(['gh', 'api', f'repos/{repo}/git/refs', '--method', 'POST',
                                '--input', str(tag_body)], check=True, capture_output=True)
        else:
            target = json.loads(exists.stdout)["object"]
            if target["type"] != "commit":
                raise ValueError(f"unexpected annotated release tag: {tag}")
            view = subprocess.run(["gh", "release", "view", tag, "--repo", repo, "--json", "isDraft"], capture_output=True, text=True)
            if view.returncode == 0:
                is_draft = json.loads(view.stdout)["isDraft"]
                if is_draft and target["sha"] == release["source_commit"]:
                    # Resume an interrupted asset upload while the release is private.
                    subprocess.run(["gh", "release", "upload", tag, "--repo", repo, "--clobber",
                                    str(artifacts / release["archive"]), str(artifacts / filename)], check=True)
                with tempfile.TemporaryDirectory() as temporary:
                    subprocess.run(["gh", "release", "download", tag, "--repo", repo, "--pattern", filename,
                                    "--dir", temporary], check=True)
                    old = read_json(Path(temporary) / filename)
                    if old["payload_sha256"] != release["payload_sha256"] or old["archive_sha256"] != release["archive_sha256"]:
                        raise ValueError(f"immutable release content differs: {tag}")
                if is_draft:
                    subprocess.run(["gh", "release", "edit", tag, "--repo", repo, "--draft=false"], check=True)
                continue
            if 'release not found' not in view.stderr.lower() and 'HTTP 404' not in view.stderr:
                raise RuntimeError('unable to inspect existing release')
            # A prior interrupted run may have created only the tag. Resume only
            # for the same source commit; do not silently reuse an unrelated tag.
            if target["sha"] != release["source_commit"]:
                raise ValueError(f"tag exists without matching release: {tag}")
        with tempfile.TemporaryDirectory() as temporary:
            notes = Path(temporary) / "notes.md"
            notes.write_text(f"Skill version {release['version']} from `{release['source_commit']}`.\n\n"
                             f"Payload SHA-256: `{release['payload_sha256']}`\n\n"
                             f"Archive SHA-256: `{release['archive_sha256']}`\n")
            # Create a draft with assets in one operation, then expose it. A
            # failed upload leaves a recoverable draft, not a partial release.
            subprocess.run(["gh", "release", "create", tag, "--repo", repo, "--verify-tag",
                            "--title", f"{release['skill']} {release['version']}", "--notes-file", str(notes), "--draft",
                            str(artifacts / release["archive"]), str(artifacts / filename)], check=True)
            subprocess.run(["gh", "release", "edit", tag, "--repo", repo, "--draft=false"], check=True)


def publish_directory(source: Path, repository: str, branch: str, token: str, message: str,
                      provenance: dict[str, str] | None = None) -> bool:
    if not source.is_dir() or not files(source):
        raise ValueError('refusing to publish an absent or empty export')
    if not token:
        raise ValueError("publishing token is required")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid destination repository")
    authorization = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    environment = {**os.environ, "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
                   "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {authorization}", "GIT_TERMINAL_PROMPT": "0"}
    with tempfile.TemporaryDirectory() as temporary:
        destination = Path(temporary)
        def run(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(["git", *args], cwd=destination, env=environment,
                                  check=True, capture_output=True, text=True)
        run("init", "-b", branch)
        run("remote", "add", "origin", f"https://github.com/{repository}.git")
        heads = run("ls-remote", "--heads", "origin", branch).stdout
        if heads.strip():
            run("fetch", "--depth=1", "origin", branch)
            run("checkout", "-B", branch, "FETCH_HEAD")
        existing = files(destination)
        existing.pop("SOURCE.json", None)
        content = files(source)
        if existing == content:
            return False
        for path in destination.iterdir():
            if path.name != ".git":
                shutil.rmtree(path) if path.is_dir() else path.unlink()
        for name, data in content.items():
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o755 if data.startswith(b"#!") else 0o644)
        if provenance:
            write_json(destination / "SOURCE.json", provenance)
        run("config", "user.name", "github-actions")
        run("config", "user.email", "github-actions@aisa.one")
        run("add", ".")
        run("commit", "-m", message)
        # Normal push preserves destination history and rejects races.
        run("push", "origin", f"HEAD:refs/heads/{branch}")
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    release = commands.add_parser("releases")
    release.add_argument("--artifacts", type=Path, required=True)
    release.add_argument("--repo", required=True)
    category = commands.add_parser("category")
    category.add_argument("--category", required=True)
    state = commands.add_parser("state")
    state.add_argument("--directory", type=Path, required=True)
    state.add_argument("--repo", required=True)
    args = parser.parse_args()
    if args.command == "releases":
        publish_releases(args.artifacts, args.repo, os.environ.get('GITHUB_SHA'))
    elif args.command == "category":
        config = read_json(args.root / ".github/skill-catalog.json")
        repository = config["categories"][args.category]["repository"]
        if not repository:
            raise ValueError("category has no distribution repository")
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary) / "export"
            subprocess.run(["bash", ".github/scripts/prepare-category-repo.sh", args.category, "--output", str(stage)],
                           cwd=args.root, check=True)
            publish_directory(stage, repository, "main", os.environ.get("SYNC_AISAS_KILLS_TOKEN", ""),
                              f"Sync {args.category} from {git(args.root, 'rev-parse', 'HEAD')}",
                              {"source_commit": git(args.root, "rev-parse", "HEAD"), "category": args.category})
    else:
        publish_directory(args.directory, args.repo, "skill-maintenance-state", os.environ.get("GH_TOKEN", ""),
                          "Update skill maintenance observations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
