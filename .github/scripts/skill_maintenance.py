#!/usr/bin/env python3
"""Read-only upstream monitoring and evidence-based fourteen-day warnings."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from skill_lifecycle import ROOT, check_publish_repository, digest, files, git, historic_files, payload, read_json, skill_dirs, substantive_content, version, write_json

MAX_RESPONSE = 16 * 1024 * 1024


def utc(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return result.astimezone(timezone.utc)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def request(url: str, body: dict[str, Any] | None = None,
            headers: dict[str, str] | None = None) -> tuple[str, dict[str, str]]:
    if not url.startswith("https://"):
        raise ValueError("upstream URLs must use HTTPS")
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"User-Agent": "aisa-skill-maintenance/1", **(headers or {})})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = response.read(MAX_RESPONSE + 1)
        if len(data) > MAX_RESPONSE:
            raise ValueError("upstream response is too large")
        return data.decode("utf-8"), dict(response.headers.items())


def rpc_result(text: str, expected_id: int) -> dict[str, Any]:
    messages = [json.loads(line[5:].strip()) for line in text.splitlines() if line.startswith("data:")] if text.lstrip().startswith("event:") or text.lstrip().startswith("data:") else [json.loads(text)]
    for message in messages:
        if message.get("id") == expected_id:
            if "error" in message:
                raise ValueError("MCP returned a JSON-RPC error")
            return message["result"]
    raise ValueError("MCP response did not include the requested result")


def observe(source: dict[str, Any]) -> Any:
    kind = source["type"]
    url = source["url"]
    if kind == "mcp":
        # Only initialize and tools/list. Never tools/call, quotes, or paid probes.
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        token = os.environ.get(source.get("token_env", "AISA_MONITOR_MCP_TOKEN"), "")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        text, response_headers = request(url, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "skill-maintenance", "version": "1.0.0"}}}, headers)
        initialized = rpc_result(text, 1)
        headers["MCP-Protocol-Version"] = initialized["protocolVersion"]
        session = next((v for k, v in response_headers.items() if k.lower() == "mcp-session-id"), None)
        if session:
            headers["Mcp-Session-Id"] = session
        request(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, headers)
        tools, cursor, seen = [], None, set()
        for page in range(100):
            text, _ = request(url, {"jsonrpc": "2.0", "id": page + 2, "method": "tools/list",
                                   "params": {"cursor": cursor} if cursor else {}}, headers)
            result = rpc_result(text, page + 2)
            tools.extend(result["tools"])
            cursor = result.get("nextCursor")
            if not cursor:
                return {"protocol": initialized["protocolVersion"], "tools": sorted(tools, key=lambda t: t["name"])}
            if cursor in seen:
                raise ValueError("MCP pagination repeated a cursor")
            seen.add(cursor)
        raise ValueError("MCP pagination exceeded the limit")
    text, _ = request(url, headers={"Accept": "application/json" if kind in {"npm", "json"} else "text/markdown, text/plain"})
    if kind == "npm":
        package = json.loads(text)
        return {k: package.get(k) for k in ("version", "engines", "bin", "dist", "repository")}
    if kind == "json":
        return json.loads(text)
    if kind == "openapi":
        try:
            specification = json.loads(text)
        except json.JSONDecodeError:
            specification = yaml.load(text, Loader=yaml.CSafeLoader)
        patterns = source.get("paths", [])
        selected = {p: v for p, v in specification["paths"].items() if not patterns or any(re.search(pattern, p) for pattern in patterns)}
        if not selected:
            raise ValueError("no tracked OpenAPI paths found")
        # Follow component references, so unrelated endpoint changes stay scoped.
        references: dict[str, Any] = {}
        queue = [selected, specification.get("security", [])]
        while queue:
            item = queue.pop()
            if isinstance(item, dict):
                ref = item.get("$ref")
                if isinstance(ref, str) and ref.startswith("#/") and ref not in references:
                    target = specification
                    for part in ref[2:].split("/"):
                        target = target[part.replace("~1", "/").replace("~0", "~")]
                    references[ref] = target
                    queue.append(target)
                queue.extend(item.values())
            elif isinstance(item, list):
                queue.extend(item)
        return {"paths": selected, "references": references, "security": specification.get("security", []),
                "securitySchemes": specification.get("components", {}).get("securitySchemes", {}),
                "servers": specification.get("servers", [])}
    # Markdown endpoints avoid navigation HTML and deployment timestamps.
    if text.lstrip().lower().startswith(("<!doctype html", "<html")):
        raise ValueError("expected documentation text, received HTML")
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").splitlines()).strip()


class SourceUnavailable(ValueError):
    """A sanitized child-worker failure; never includes fetched bodies/tokens."""


def bounded_observe(source: dict[str, Any]) -> Any:
    # A socket timeout does not bound DNS, a slow streaming body, or parsing.
    # A disposable process bounds the entire operation and is killed on timeout.
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '_observe'],
        input=json.dumps(source), capture_output=True, text=True, timeout=90, check=True)
    value = json.loads(result.stdout)
    if not value['ok']:
        raise SourceUnavailable(value['error'])
    return value['value']


def monitor(sources: dict[str, Any], previous: dict[str, Any], now: str) -> dict[str, Any]:
    def poll(item: tuple[str, Any]) -> tuple[str, Any]:
        source_id, source = item
        old = previous.get("sources", {}).get(source_id, {})
        try:
            value = bounded_observe(source)
            current = fingerprint(value)
            snapshot = {"digest": current, "baseline_digest": old.get("baseline_digest", current),
                "observed_at": now, "value": value, "status": "ok"}
            if old.get('digest') and old['digest'] != current:
                snapshot.update(previous_digest=old['digest'], previous_value=old.get('value'))
            elif old.get('previous_digest'):
                snapshot.update(previous_digest=old['previous_digest'], previous_value=old.get('previous_value'))
        except (ValueError, KeyError, OSError, yaml.YAMLError, subprocess.SubprocessError) as error:
            # Do not leak URL/query credentials, headers, response bodies, or tokens.
            code = str(error) if isinstance(error, SourceUnavailable) else f"HTTP {error.code}" if isinstance(error, urllib.error.HTTPError) else type(error).__name__
            snapshot = {**old, "status": "unavailable", "error": code, "attempted_at": now}
        return source_id, snapshot
    with ThreadPoolExecutor(max_workers=4) as executor:
        snapshots = dict(executor.map(poll, sources.items()))
    return {"schema_version": 1, "sources": snapshots}


def last_update(root: Path, skill: Path) -> str:
    relative = skill.relative_to(root).as_posix()
    history = git(root, "log", "--format=%H %cI", "--", relative).splitlines()
    for line in history:
        commit, timestamp = line.split(" ", 1)
        current = substantive_content(historic_files(root, commit, relative))
        parent = git(root, "rev-list", "--parents", "-n", "1", commit).split()
        previous = substantive_content(historic_files(root, parent[1], relative)) if len(parent) > 1 else {}
        if current != previous:
            return timestamp
    raise ValueError(f"no committed content history for {relative}")


def report(root: Path, state: dict[str, Any], now: str, days: int = 14) -> list[dict[str, Any]]:
    instant = utc(now)
    reviews = read_json(root / "maintenance/reviews.json")
    sources = read_json(root / 'maintenance/upstreams.json')
    rows = []
    for skill in skill_dirs(root):
        relative = skill.relative_to(root).as_posix()
        manifest = read_json(skill / "skill.json")
        reviewed = reviews.get(relative, {})
        updated = last_update(root, skill)
        age = max(0, int((instant - utc(updated)).total_seconds() // 86400))
        review_age = max(0, int((instant - utc(reviewed["verified_at"])).total_seconds() // 86400)) if reviewed else None
        changed, unavailable, unreviewed = [], [], []
        for source_id in manifest["upstreams"]:
            snapshot = state.get("sources", {}).get(source_id, {})
            if snapshot.get("status") != "ok":
                unavailable.append(source_id)
            known = reviewed.get("upstreams", {}).get(source_id, snapshot.get("baseline_digest"))
            if snapshot.get("digest") and known and snapshot["digest"] != known:
                changed.append(source_id)
            if source_id not in reviewed.get("upstreams", {}):
                unreviewed.append(source_id)
        review_matches = reviewed.get("payload_sha256") == digest(payload(skill))
        warnings = []
        if age >= days:
            warnings.append("no update in 14 days")
        if review_age is None or review_age >= days or not review_matches or unreviewed:
            warnings.append("review overdue")
        if changed:
            warnings.append("upstream change pending")
        if unavailable:
            warnings.append("monitoring unavailable")
        status = "; ".join(warnings) or "current"
        if age >= days and review_age is not None and review_age < days and review_matches and not changed and not unavailable and not unreviewed:
            status += "; unchanged, verified current"
        row = {"skill": relative, "owner": manifest["owner"], "version": version((skill / "SKILL.md").read_text()),
               "updated_at": updated, "update_age_days": age, "verified_at": reviewed.get("verified_at"),
               "review_age_days": review_age, "status": status, "warnings": warnings,
               "changed_upstreams": changed, "unavailable_upstreams": unavailable, "unreviewed_upstreams": unreviewed}
        row['upstream_links'] = {s: sources[s]['url'] for s in manifest['upstreams']}
        # Ages change daily; notify only on a meaningful state/evidence transition.
        row["notification_digest"] = fingerprint({"status": status, "version": row["version"],
            "payload": digest(payload(skill)), "verified_at": row["verified_at"],
            "sources": {s: state.get("sources", {}).get(s, {}).get("digest") for s in manifest["upstreams"]}})
        rows.append(row)
    return rows


def markdown(rows: list[dict[str, Any]], now: str) -> str:
    text = f"# Skill maintenance report\n\nGenerated {now}. Warnings are advisory.\n\n"
    text += "| Skill | Owner | Version | Update age | Review age | Status |\n|---|---|---|---|---|---|\n"
    for row in rows:
        review_age = "never verified" if row["review_age_days"] is None else f"{row['review_age_days']}d"
        text += f"| {row['skill']} | {row['owner']} | {row['version']} | {row['update_age_days']}d | {review_age} | {row['status']} |\n"
    text += "\n## Pending evidence\n\n"
    for row in rows:
        for key in ("changed_upstreams", "unavailable_upstreams", "unreviewed_upstreams"):
            if row[key]:
                links = [f"[{s}]({row.get('upstream_links', {}).get(s, '#')})" for s in row[key]]
                text += f"- {row['skill']} — {key.replace('_', ' ')}: {', '.join(links)}\n"
    return text


def record_review(root: Path, skill_id: str, state: dict[str, Any], evidence: str, now: str) -> None:
    skill = next((s for s in skill_dirs(root) if s.relative_to(root).as_posix() == skill_id), None)
    if skill is None:
        raise ValueError("unknown skill")
    if not evidence.strip():
        raise ValueError("review evidence is required")
    manifest = read_json(skill / "skill.json")
    snapshots = {}
    for source_id in manifest["upstreams"]:
        snapshot = state["sources"][source_id]
        age = (utc(now) - utc(snapshot.get("observed_at", "1970-01-01T00:00:00+00:00"))).total_seconds()
        if snapshot.get("status") != "ok" or not 0 <= age <= 86400:
            raise ValueError(f"review requires a successful snapshot from the last 24 hours: {source_id}")
        snapshots[source_id] = snapshot["digest"]
    path = root / "maintenance/reviews.json"
    reviews = read_json(path)
    reviews[skill_id] = {"verified_at": now, "payload_sha256": digest(payload(skill)),
                         "upstreams": snapshots, "evidence": evidence}
    write_json(path, reviews)


def notify(rows: list[dict[str, Any]], repo: str) -> None:
    check_publish_repository(repo)
    issues = json.loads(subprocess.check_output(["gh", "issue", "list", "--repo", repo, "--state", "all",
        "--limit", "1000", "--json", "number,title,body,state"], text=True))
    for row in rows:
        title = f"Skill maintenance: {row['skill']}"
        issue = next((i for i in issues if i["title"] == title and "<!-- skill-maintenance:" in i["body"]), None)
        if not row["warnings"]:
            if issue and issue["state"] == "OPEN":
                subprocess.run(["gh", "issue", "close", str(issue["number"]), "--repo", repo], check=True)
            continue
        marker = f"<!-- skill-maintenance:{row['notification_digest']} -->"
        if issue and issue["state"] == "OPEN" and marker in issue["body"]:
            continue
        with tempfile.TemporaryDirectory() as directory:
            body = Path(directory) / "body.md"
            body.write_text(marker + "\n\n" + markdown([row], datetime.now(timezone.utc).isoformat()) +
                            "\nReview the tracked upstream evidence and commit the review record. No automatic skill rewrites are performed.\n")
            if issue:
                if issue["state"] == "CLOSED":
                    subprocess.run(["gh", "issue", "reopen", str(issue["number"]), "--repo", repo], check=True)
                command = ["gh", "issue", "edit", str(issue["number"]), "--repo", repo, "--body-file", str(body)]
            else:
                command = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body-file", str(body)]
            subprocess.run(command, check=True)


def main() -> int:
    if sys.argv[1:] == ['_observe']:
        try:
            value = observe(json.load(sys.stdin))
            print(json.dumps({'ok': True, 'value': value}))
        except Exception as error:
            code = f'HTTP {error.code}' if isinstance(error, urllib.error.HTTPError) else type(error).__name__
            print(json.dumps({'ok': False, 'error': code}))
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--now", default=datetime.now(timezone.utc).isoformat())
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan")
    scan.add_argument("--previous", type=Path)
    scan.add_argument("--output", type=Path, required=True)
    scan.add_argument("--offline", action="store_true", help="Render a report from saved snapshots without fetching")
    scan.add_argument("--notify", metavar="OWNER/REPO")
    review = commands.add_parser("review")
    review.add_argument("--skill", required=True)
    review.add_argument("--state", type=Path, required=True)
    review.add_argument("--evidence", required=True)
    notifications = commands.add_parser("notify")
    notifications.add_argument("--report", type=Path, required=True)
    notifications.add_argument("--repo", required=True)
    args = parser.parse_args()
    utc(args.now)
    if args.command == "notify":
        notify(read_json(args.report), args.repo)
        return 0
    if args.command == "review":
        record_review(args.root, args.skill, read_json(args.state), args.evidence, args.now)
        return 0
    previous = read_json(args.previous) if args.previous and args.previous.exists() else {}
    state = previous if args.offline else monitor(read_json(args.root / "maintenance/upstreams.json"), previous, args.now)
    rows = report(args.root, state, args.now)
    write_json(args.output / "state.json", state)
    write_json(args.output / "report.json", rows)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.md").write_text(markdown(rows, args.now))
    if args.notify:
        if args.offline:
            raise ValueError("offline snapshots cannot send notifications")
        notify(rows, args.notify)
    print(f"skills={len(rows)} warnings={sum(bool(r['warnings']) for r in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
