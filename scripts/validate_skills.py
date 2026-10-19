#!/usr/bin/env python3
"""Validate every skill against the published AIsa contract and the shared agent rules.

Checks, per skill directory (``<category>/<skill>/``):

* ``unknown-path`` / ``unknown-method``: every AIsa API path a skill mentions
  (``https://api.aisa.one/...``, ``/apis/v1/...``, ``/v1/...``, and path
  literals joined onto a base URL declared in the same file) must exist in
  the published OpenAPI document (https://aisa.one/openapi.json) with the
  method the skill uses. Path templates (``{id}``, ``<id>``, ``$VAR``) match
  any segment; ``...`` or ``*`` at the end matches any operation under the
  prefix.
* ``body-not-accepted``: a request that sends a body (curl ``-d``/``--json``,
  Python ``json=``/``data=``/dict payloads) to an operation whose contract
  declares no ``requestBody``.
* ``literal-key``: an API key literal (``sk-aisa-<alnum>{8,}``, ``sk-<alnum>{20,}``
  or a non-placeholder ``AISA_API_KEY=...`` value) anywhere in the skill.
* ``plugin-root``: ``${CLAUDE_PLUGIN_ROOT}`` references; no documented install
  path sets that variable. Use skill-root-relative paths (``scripts/x.py``).
* ``cost-claim`` (warning): prose that claims responses carry ``usage.cost``
  or ``usage.credits_remaining``. The settled cost is the
  ``X-AISA-Customer-Cost-Micros-USD`` response header.
* ``disabled-operation`` (warning): the operation exists but the contract
  marks it ``x-aisa-status: disabled``.
* ``rules-block-*``: ``SKILL.md`` must carry the shared rules block from
  ``_shared/aisa-rules.md`` between ``<!-- aisa-rules:start -->`` and
  ``<!-- aisa-rules:end -->`` and the text must match the source exactly
  (refresh with ``scripts/sync_shared_rules.py``).

A skill whose ``SKILL.md`` contains ``<!-- aisa-deprecated: ... -->`` is reported
as deprecated: its stale paths are downgraded to ``deprecated-stale-path``
warnings because the skill is documented as targeting removed functionality.

Usage::

    python3 scripts/validate_skills.py                     # downloads the OpenAPI
    python3 scripts/validate_skills.py --openapi spec.json # offline
    python3 scripts/validate_skills.py --changed-from origin/main
    python3 scripts/validate_skills.py --json report.json

Exit status is 1 when any failure remains (or a known-issue entry is stale),
2 on a usage or download error, else 0. The report records the OpenAPI
source and its SHA-256 so a run can be reproduced offline. The download is
capped (``--max-download-mib``, default 64) so a runaway response cannot
exhaust CI memory.

Known limitations (static analysis; a clean run is not proof of correctness):

* Markdown and shell files are scanned for full ``https://api.aisa.one/...``
  URLs, ``/apis/v1/...`` and ``/v1/...`` paths, and bare ``/<family>/...``
  paths or ``$VAR/<family>/...`` references **only when the same file
  declares an ``api.aisa.one`` base URL** (or assigns ``VAR`` to one). A
  README or reference file that lists routes without any base is not
  checked; ``SKILL.md`` is always covered because the shared rules block
  declares the bases.
* Method and body are inferred from curl flags and from Python call sites
  that contain the path literal. A URL built first and used later
  (``url = f"{BASE}/x"; requests.post(url, json=...)``), paths assembled with
  ``"/".join(...)``, ``str.format`` or ``%``, and JavaScript/TypeScript
  ``fetch`` calls are checked for the path only, with method ``ANY`` and no
  body check.
* Request and response **schemas** are not validated, only path, method and
  the presence of a request body. Query parameter names are not checked.
* Files under ``tests/``/``fixtures/`` are scanned for keys and
  ``${CLAUDE_PLUGIN_ROOT}`` but not for paths (they use synthetic URLs).
* Operations are matched on the server declared per operation; other hosts
  (for example ``tools.aisa.one``) are out of scope.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Iterator
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPENAPI_URL = "https://aisa.one/openapi.json"
API_HOST = "api.aisa.one"
SHARED_RULES = Path("_shared/aisa-rules.md")
RULES_START = "<!-- aisa-rules:start -->"
RULES_END = "<!-- aisa-rules:end -->"
DEPRECATED_MARKER = "<!-- aisa-deprecated"
KNOWN_ISSUES = Path("scripts/validate_skills_known_issues.json")

IGNORED_DIRECTORIES = {".git", ".venv", "node_modules", "__pycache__", "build", ".hermes"}
TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".tsx",
    ".json", ".yaml", ".yml", ".toml", ".env", ".example", ".cfg", ".ini", "",
}
HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
FAILURE_CLASSES = (
    "unknown-path",
    "unknown-method",
    "body-not-accepted",
    "literal-key",
    "plugin-root",
    "rules-block-missing",
    "rules-block-stale",
    "rules-block-malformed",
)
WARNING_CLASSES = ("cost-claim", "disabled-operation", "deprecated-stale-path")
ALL_CLASSES = FAILURE_CLASSES + WARNING_CLASSES

# Routes the public docs describe that the OpenAPI document does not list.
# Each entry cites the page that documents it. Keep this list short; a route
# that is not documented anywhere must not be added here.
DOCUMENTED_ROUTES: dict[tuple[str, str], str] = {
    ("GET", "/v1/models"): "https://aisa.one/llms.txt (2. Verify, 4. Spending) and https://aisa.one/docs/guides/models.md",
    ("POST", "/v1/responses"): "https://aisa.one/docs/guides/models.md (Endpoints by model type)",
    ("POST", "/v1/images/edits"): "https://aisa.one/docs/guides/models.md (Endpoints by model type)",
    ("POST", "/v1/video/generations"): "https://aisa.one/docs/guides/models.md (Endpoints by model type)",
    ("GET", "/v1/video/generations/{task_id}"): "https://aisa.one/docs/guides/models.md (Endpoints by model type)",
}

MAX_DOWNLOAD_MIB = 64
PATH_CHARS = r"A-Za-z0-9_\-./{}:<>$*"
# $VAR/path or ${VAR}/path in shell and Markdown; VAR must be assigned an api.aisa.one URL
# in the same file, or the path must start with a known API family.
VAR_PATH_RE = re.compile(r"\$\{?(?P<var>[A-Za-z_][A-Za-z0-9_]*)\}?(?P<path>/[A-Za-z0-9_\-./{}:<>*]+)")
VAR_ASSIGN_RE = re.compile(
    r"(?m)^\s*(?:export\s+)?(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*[\"']?https?://api\.aisa\.one(?P<base>/[A-Za-z0-9_\-./]*)?"
)
FULL_URL_RE = re.compile(r"https?://" + re.escape(API_HOST) + r"(?P<path>/[" + PATH_CHARS + r"]*)?")
BASE_PATH_RE = re.compile(r"(?<![\w./:-])(?P<path>/(?:apis/v1|v1beta|v1)(?:/[" + PATH_CHARS + r"]*)?)")
TRAILING_PUNCTUATION = ".,;:)]}>*'\"`"
FILESYSTEM_ROOTS = {
    "tmp", "usr", "var", "etc", "dev", "proc", "home", "root", "opt", "bin", "sbin",
    "lib", "lib64", "mnt", "srv", "sys", "private", "Users", "Applications", "Library",
    "workspace", "app", "data", "path", "to",
}
METHOD_TOKEN_RE = re.compile(r"(?<![\w/])(GET|POST|PUT|PATCH|DELETE)(?![\w/])")
PLUGIN_ROOT_RE = re.compile(r"\$\{?CLAUDE_PLUGIN_ROOT\}?")
KEY_LITERAL_RE = re.compile(r"(?<![\w-])(sk-aisa-[A-Za-z0-9]{8,}|sk-[A-Za-z0-9]{20,})(?![\w-])")
KEY_ASSIGNMENT_RE = re.compile(
    r"AISA_API_KEY\s*[=:]\s*[\"']?(?P<value>[A-Za-z0-9_\-]{24,})[\"']?"
)
PLACEHOLDER_VALUE_RE = re.compile(r"^(?:[xX]+|\.{3,}|\*+|_+)$")
PLACEHOLDER_PREFIXES = ("your", "YOUR", "sk-...", "sk-aisa-...", "example", "EXAMPLE", "REPLACE", "placeholder")
COST_CLAIM_RE = re.compile(r"usage\.cost\b|usage\.credits_remaining\b|`credits_remaining`")
CURL_BODY_FLAGS = {
    "-d", "--data", "--data-raw", "--data-binary", "--data-ascii", "--data-urlencode",
    "--json", "-F", "--form", "-T", "--upload-file",
}


# --------------------------------------------------------------------------- contract


@dataclass(frozen=True)
class Operation:
    method: str
    path: str
    operation_id: str
    has_body: bool
    status: str | None
    documented_only: str | None = None


class Contract:
    """Operations of the published OpenAPI keyed by their full URL path."""

    def __init__(self, document: dict, source: str, sha256: str) -> None:
        self.source = source
        self.sha256 = sha256
        self.title = f"{document.get('info', {}).get('title', '?')} {document.get('info', {}).get('version', '')}".strip()
        self.operations: dict[str, dict[str, Operation]] = {}
        root_servers = document.get("servers") or []
        for raw_path, item in (document.get("paths") or {}).items():
            if not isinstance(item, dict):
                continue
            for method, op in item.items():
                if method.upper() not in HTTP_METHODS or not isinstance(op, dict):
                    continue
                servers = op.get("servers") or item.get("servers") or root_servers
                base = urlsplit(servers[0]["url"]).path.rstrip("/") if servers else ""
                full = base + raw_path
                self.operations.setdefault(full, {})[method.upper()] = Operation(
                    method=method.upper(),
                    path=full,
                    operation_id=str(op.get("operationId") or ""),
                    has_body=bool(op.get("requestBody")),
                    status=op.get("x-aisa-status"),
                )
        for (method, path), citation in DOCUMENTED_ROUTES.items():
            if method not in self.operations.get(path, {}):
                self.operations.setdefault(path, {})[method] = Operation(
                    method, path, "", True, None, documented_only=citation
                )
        self._templates = [
            (path, [self._segment_regex(s) for s in path.strip("/").split("/")])
            for path in self.operations
            if "{" in path
        ]
        self.families: dict[str, set[str]] = {}
        for path in self.operations:
            for base in ("/apis/v1", "/v1beta", "/v1"):
                if path.startswith(base + "/"):
                    self.families.setdefault(base, set()).add(path[len(base) + 1:].split("/")[0])
                    break

    @staticmethod
    def _segment_regex(segment: str) -> re.Pattern[str]:
        pattern = "".join(
            "[^/]+" if part.startswith("{") else re.escape(part)
            for part in re.split(r"(\{[^}]*\})", segment)
            if part
        )
        return re.compile(pattern)

    @staticmethod
    def is_wildcard(segment: str) -> bool:
        return any(ch in segment for ch in "{<$*") or bool(re.fullmatch(r"(?:YOUR|<)?[A-Z][A-Z0-9_]{2,}>?", segment))

    def resolve(self, path: str) -> list[str]:
        """Return the contract paths that match ``path`` (templates aware)."""
        prefix = path.endswith(("/...", "/*", "...", "/"))
        clean = re.sub(r"/?(?:\.\.\.|\*)$", "", path).rstrip("/")
        if prefix:
            return [known for known in self.operations if known == clean or known.startswith(clean + "/")]
        if clean in self.operations:
            return [clean]
        segments = clean.strip("/").split("/")
        matches = []
        for known, template in self._templates:
            if len(template) != len(segments):
                continue
            if all(self.is_wildcard(s) or t.fullmatch(s) for s, t in zip(segments, template)):
                matches.append(known)
        if matches:
            return matches
        if any(self.is_wildcard(s) for s in segments):
            for known in self.operations:
                parts = known.strip("/").split("/")
                if len(parts) == len(segments) and all(
                    self.is_wildcard(s) or s == p for s, p in zip(segments, parts)
                ):
                    matches.append(known)
        return matches


def load_contract(openapi: Path | None, url: str, timeout: float, cache_dir: Path | None,
                  max_bytes: int = MAX_DOWNLOAD_MIB * 1024 * 1024) -> Contract:
    if openapi is not None:
        data = openapi.read_bytes()
        source = str(openapi)
    else:
        target_dir = cache_dir or Path(tempfile.mkdtemp(prefix="aisa-openapi-"))
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "openapi.json"
        data = _download(url, timeout, max_bytes=max_bytes)
        target.write_bytes(data)
        source = f"{url} (saved to {target})"
    digest = hashlib.sha256(data).hexdigest()
    try:
        document = json.loads(data)
    except json.JSONDecodeError as error:
        raise SystemExit(f"error: OpenAPI document is not valid JSON: {error}")
    if not isinstance(document, dict) or "paths" not in document:
        raise SystemExit("error: OpenAPI document has no 'paths' object")
    return Contract(document, source, digest)


def _download(url: str, timeout: float, attempts: int = 3, max_bytes: int = MAX_DOWNLOAD_MIB * 1024 * 1024) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "aisa-skill-validator/1.0"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                chunks: list[bytes] = []
                received = 0
                while chunk := response.read(1024 * 1024):
                    received += len(chunk)
                    if received > max_bytes:
                        raise SystemExit(f"error: {url} exceeds the {max_bytes // (1024 * 1024)} MiB download cap; "
                                         "download it yourself and pass --openapi, or raise --max-download-mib")
                    chunks.append(chunk)
                return b"".join(chunks)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
            if attempt < attempts:
                time.sleep(2 * attempt)
    raise SystemExit(f"error: could not download {url}: {last_error}")


# --------------------------------------------------------------------------- mentions


@dataclass
class Mention:
    file: str
    line: int
    path: str
    method: str | None = None
    has_body: bool = False
    origin: str = "literal"
    alternatives: tuple[str, ...] = ()  # other base joins; passes when any resolves


@dataclass
class Issue:
    skill: str
    kind: str
    file: str
    line: int
    detail: str

    @property
    def key(self) -> str:
        return f"{self.skill}:{self.kind}:{self.file}:{self.detail}"

    def __str__(self) -> str:
        return f"{self.kind:<22} {self.file}:{self.line}  {self.detail}"


@dataclass
class SkillReport:
    skill: str
    version: str
    deprecated: bool
    issues: list[Issue] = field(default_factory=list)
    mentions: int = 0
    documented_only: set[str] = field(default_factory=set)
    known: list[Issue] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for issue in self.issues:
            counts[issue.kind] = counts.get(issue.kind, 0) + 1
        return counts

    @property
    def failed(self) -> bool:
        return any(issue.kind in FAILURE_CLASSES for issue in self.issues)


def clean_path(raw: str) -> str:
    path = raw.split("?", 1)[0].split("#", 1)[0]
    while path and path[-1] in TRAILING_PUNCTUATION and not path.endswith("..."):
        if path[-1] == "}" and path.count("{") >= path.count("}"):
            break  # closing brace of a path template such as {token_id}
        path = path[:-1]
    return path


PATH_SHAPE_RE = re.compile(r"^/[" + PATH_CHARS + r"]+$")
BASES = ("/apis/v1", "/v1beta", "/v1")


def looks_like_api_path(path: str) -> bool:
    if path == "/" or not PATH_SHAPE_RE.match(path) or "//" in path:
        return False
    first = path.strip("/").split("/")[0]
    if first in FILESYSTEM_ROOTS or first.startswith("."):
        return False
    if re.search(r"\.(?:py|sh|md|json|js|ts|txt|png|jpg|html|yaml|yml|csv)$", path):
        return False
    return True


def is_base_or_family_root(path: str, contract: Contract) -> bool:
    """``/apis/v1``, ``/v1`` or ``/apis/v1/<family>`` name a base URL, not an operation."""
    clean = path.rstrip("/")
    if clean in BASES or clean == "":
        return True
    for base in BASES:
        if clean.startswith(base + "/"):
            rest = clean[len(base) + 1:]
            return "/" not in rest and rest in contract.families.get(base, set()) and not path.endswith("/")
    return False


def base_paths_in(text: str) -> list[str]:
    """Base URLs declared in a file: ``/apis/v1``, ``/v1``, ``/v1beta`` or ``/apis/v1/<family>``."""
    bases: list[str] = []
    for match in FULL_URL_RE.finditer(text):
        base = clean_path(match.group("path") or "").rstrip("/")
        if base in BASES or re.fullmatch(r"/apis/v1/[A-Za-z0-9_-]+", base):
            if base not in bases:
                bases.append(base)
    return bases


def join_base(bases: list[str], relative: str) -> list[str]:
    """Join a relative path literal onto each base; absolute AIsa paths pass through."""
    if relative.startswith(("/apis/", "/v1/", "/v1beta/")):
        return [relative]
    return [base + relative for base in bases]


def mentions_from_text(relative: str, text: str, contract: Contract, relative_paths: bool = True) -> Iterator[Mention]:
    """Full URLs, ``/apis/v1`` and ``/v1`` paths, curl commands and table rows.

    ``relative_paths`` also resolves bare ``/<family>/...`` paths against the
    base URLs the file declares (off for Python, where the AST pass does it).
    """
    seen: set[tuple[int, str, str | None, bool]] = set()
    lines = text.splitlines()
    bases = base_paths_in(text)
    var_bases = variable_bases(text)
    family_pattern = _family_regex(contract, bases) if relative_paths else None

    def emit(mention: Mention) -> Iterator[Mention]:
        key = (mention.line, mention.path, mention.method, mention.has_body)
        if key in seen or not looks_like_api_path(mention.path) or is_base_or_family_root(mention.path, contract):
            return
        seen.add(key)
        yield mention

    def resolve_variable(var: str, path: str) -> list[str]:
        """Join ``$VAR/path`` onto the base VAR is assigned to, else onto bases sharing the family."""
        path = clean_path(path)
        if not looks_like_api_path(path):
            return []
        if var in var_bases:
            return join_base([var_bases[var]], path)
        family = path.strip("/").split("/")[0]
        return [base + path for base in bases if family in contract.families.get(base, set())]

    for command, line_number in curl_commands(lines):
        for mention in curl_mention(command, relative, line_number, resolve_variable):
            yield from emit(mention)

    for index, line in enumerate(lines, 1):
        methods = set(METHOD_TOKEN_RE.findall(line))
        method = methods.pop() if len(methods) == 1 else None
        for match in FULL_URL_RE.finditer(line):
            path = clean_path(match.group("path") or "/")
            if path.startswith("/apis/") or path.startswith("/v1"):
                yield from emit(Mention(relative, index, path, method, False, "url"))
        if not relative_paths:
            continue
        for match in BASE_PATH_RE.finditer(line):
            path = clean_path(match.group("path"))
            if path.startswith("/v1") and not _known_family(contract, path):
                continue
            yield from emit(Mention(relative, index, path, method, False, "path"))
        if family_pattern is not None:
            for match in family_pattern.finditer(line):
                path = clean_path(match.group("path"))
                family = path.strip("/").split("/")[0]
                joins = [base + path for base in bases if family in contract.families.get(base, set())]
                if joins:
                    yield from emit(Mention(relative, index, joins[0], method, False, "relative", tuple(joins[1:])))
        for match in VAR_PATH_RE.finditer(line):
            joins = resolve_variable(match.group("var"), match.group("path"))
            if joins:
                yield from emit(Mention(relative, index, joins[0], method, False, "variable", tuple(joins[1:])))


def variable_bases(text: str) -> dict[str, str]:
    """``VAR=https://api.aisa.one/<base>`` assignments in shell or Markdown."""
    found: dict[str, str] = {}
    for match in VAR_ASSIGN_RE.finditer(text):
        base = clean_path(match.group("base") or "").rstrip("/")
        if base in BASES or re.fullmatch(r"/apis/v1/[A-Za-z0-9_-]+", base) or base == "":
            found.setdefault(match.group("var"), base)
    return found


def _known_family(contract: Contract, path: str) -> bool:
    for base in ("/apis/v1", "/v1beta", "/v1"):
        if path.startswith(base + "/"):
            return path[len(base) + 1:].split("/")[0] in contract.families.get(base, set())
    return False


def _family_regex(contract: Contract, bases: list[str]) -> re.Pattern[str] | None:
    families: set[str] = set()
    for base in bases:
        families.update(contract.families.get(base, set()))
    if not families:
        return None
    names = "|".join(sorted(map(re.escape, families), key=len, reverse=True))
    return re.compile(r"(?<![\w./:{-])(?P<path>/(?:" + names + r")(?:/[" + PATH_CHARS + r"]*)?)(?![\w-])")


def curl_commands(lines: list[str]) -> Iterator[tuple[str, int]]:
    index = 0
    while index < len(lines):
        line = lines[index]
        if re.search(r"(?:^|[\s$;|(`])curl\s", line + " "):
            start = index
            buffer = [line.rstrip()]
            while buffer[-1].endswith("\\") and index + 1 < len(lines):
                buffer[-1] = buffer[-1][:-1]
                index += 1
                buffer.append(lines[index].rstrip())
            command = " ".join(buffer)
            command = command[command.find("curl"):]
            yield command, start + 1
        index += 1


def curl_mention(command: str, relative: str, line_number: int,
                 resolve_variable: Callable[[str, str], list[str]] | None = None) -> Iterator[Mention]:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    method = None
    has_body = False
    get_flag = False
    url = None
    variable_url: re.Match[str] | None = None
    skip = False
    for position, token in enumerate(tokens):
        if skip:
            skip = False
            continue
        if token in ("-X", "--request") and position + 1 < len(tokens):
            method = tokens[position + 1].upper()
            skip = True
        elif token.startswith("--request="):
            method = token.split("=", 1)[1].upper()
        elif token.startswith("-X") and len(token) > 2:
            method = token[2:].upper()
        elif token in CURL_BODY_FLAGS or any(token.startswith(flag + "=") for flag in CURL_BODY_FLAGS if flag.startswith("--")):
            has_body = True
            if token in CURL_BODY_FLAGS:
                skip = True
        elif token in ("-G", "--get"):
            get_flag = True
        elif url is None and (token.startswith("http://") or token.startswith("https://")):
            url = token
        elif url is None and variable_url is None and token.startswith("$"):
            variable_url = VAR_PATH_RE.match(token)
    if method is None:
        method = "GET" if get_flag or not has_body else "POST"
    if get_flag:
        has_body = False
    if url is None:
        if variable_url is None or resolve_variable is None:
            return
        joins = resolve_variable(variable_url.group("var"), variable_url.group("path"))
        if joins:
            yield Mention(relative, line_number, joins[0], method, has_body, "curl-variable", tuple(joins[1:]))
        return
    match = FULL_URL_RE.search(url)
    if match is None:
        return
    if get_flag:
        has_body = False
    yield Mention(relative, line_number, clean_path(match.group("path") or "/"), method, has_body, "curl")


def mentions_from_python(relative: str, text: str, contract: Contract) -> Iterator[Mention]:
    """Call sites and string literals in Python, resolved against base URLs in the file."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return
    bases = base_paths_in(text)
    handled: set[int] = set()

    def known_family(relative_path: str) -> bool:
        first = relative_path.strip("/").split("/")[0]
        return any(first in contract.families.get(base, set()) for base in bases)

    def literal_paths(node: ast.AST, request_site: bool) -> list[str]:
        """Paths encoded by a string node, resolved against the file's bases.

        Relative literals are joined only when their first segment is a known
        API family, or when they are passed to a request-like call.
        """
        def joined(relative_path: str) -> list[str]:
            relative_path = clean_path(relative_path)
            if not looks_like_api_path(relative_path.replace("{}", "X")):
                return []
            if not bases:
                return []  # no api.aisa.one base in this file: the literal may target another host
            if not relative_path.startswith(("/apis/", "/v1/", "/v1beta/")) and not (request_site or known_family(relative_path)):
                return []
            return join_base(bases, relative_path.replace("{}", "{var}"))

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            match = FULL_URL_RE.search(node.value)
            if match:
                return [clean_path(match.group("path") or "/")]
            return joined(node.value) if node.value.startswith("/") else []
        if isinstance(node, ast.JoinedStr) and node.values:
            first = node.values[0]
            rest = "".join(
                part.value if isinstance(part, ast.Constant) and isinstance(part.value, str) else "{}"
                for part in node.values[1:]
            )
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                match = FULL_URL_RE.search(first.value + rest)
                return [clean_path(match.group("path") or "/").replace("{}", "{var}")] if match else []
            if isinstance(first, ast.FormattedValue) and rest.startswith("/"):
                return joined(rest)
            return []
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            right = node.right
            if isinstance(right, ast.Constant) and isinstance(right.value, str) and right.value.startswith("/"):
                return joined(right.value)
        return []

    def emit(node: ast.AST, paths: list[str], method: str | None, has_body: bool, origin: str, line: int) -> Iterator[Mention]:
        paths = [p for p in paths if looks_like_api_path(p) and not is_base_or_family_root(p, contract)]
        if paths:
            yield Mention(relative, line, paths[0], method, has_body, origin, tuple(paths[1:]))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee = node.func
            name = (callee.attr if isinstance(callee, ast.Attribute) else getattr(callee, "id", "")) or ""
            tokens = {t.lower() for t in re.split(r"[_\W]+", name) if t}
            request_site = bool(tokens & {"request", "post", "get", "put", "delete", "patch", "call", "fetch", "http", "api", "urlopen", "url", "endpoint"})
            method = None
            verbs = tokens & {m.lower() for m in HTTP_METHODS}
            if len(verbs) == 1:
                method = verbs.pop().upper()
            if isinstance(callee, ast.Attribute) and name.lower() in {"get", "post", "put", "delete", "patch"}:
                owner = callee.value
                owner_name = (owner.attr if isinstance(owner, ast.Attribute) else getattr(owner, "id", "")) or ""
                if not re.search(r"request|session|client|http|self|api", owner_name, re.IGNORECASE):
                    method = None  # dict.get / mapping.get, not an HTTP verb
            for keyword in node.keywords:
                if keyword.arg == "method" and isinstance(keyword.value, ast.Constant):
                    method = str(keyword.value.value).upper()
            if node.args and isinstance(node.args[0], ast.Constant) and str(node.args[0].value).upper() in HTTP_METHODS:
                method = str(node.args[0].value).upper()
            has_body = any(
                keyword.arg in {"json", "data", "body", "payload"}
                and not (isinstance(keyword.value, ast.Constant) and keyword.value.value is None)
                for keyword in node.keywords
            ) or any(
                isinstance(arg, ast.Dict)
                or (isinstance(arg, ast.Name) and re.fullmatch(r"(?:json_)?(?:body|payload|data)", arg.id))
                for arg in node.args
            )
            if tokens & {"query", "params"} and not any(k.arg in {"json", "data", "body", "payload"} for k in node.keywords):
                has_body = False  # helpers named *_query/*_params send the mapping as the query string
            for arg in list(node.args) + [keyword.value for keyword in node.keywords]:
                paths = literal_paths(arg, request_site)
                if paths:
                    handled.add(id(arg))
                    yield from emit(arg, paths, method, has_body, "python-call", getattr(arg, "lineno", node.lineno))
    for node in ast.walk(tree):
        if id(node) in handled or not isinstance(node, (ast.Constant, ast.JoinedStr, ast.BinOp)):
            continue
        paths = literal_paths(node, False)
        if paths:
            yield from emit(node, paths, None, False, "python-literal", getattr(node, "lineno", 0))


# --------------------------------------------------------------------------- skills


def skill_directories(root: Path) -> list[Path]:
    config = json.loads((root / ".github/skill-catalog.json").read_text(encoding="utf-8"))
    return sorted(
        path.parent
        for category in config["categories"]
        for path in (root / category).glob("*/SKILL.md")
    )


def skill_files(skill: Path) -> Iterator[Path]:
    for directory, dirnames, filenames in os.walk(skill, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_DIRECTORIES)
        for filename in sorted(filenames):
            path = Path(directory) / filename
            if path.is_symlink() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if path.stat().st_size > 4 * 1024 * 1024:
                continue
            yield path


def is_test_file(relative: str) -> bool:
    parts = relative.split("/")
    return any(p in {"tests", "test", "fixtures", "__tests__"} for p in parts[:-1]) or bool(
        re.match(r"(?:test_.*|.*_test|.*\.test|.*\.spec)\.(?:py|js|mjs|ts)$", parts[-1])
    )


def read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\0" in data[:4096]:
        return None
    return data.decode("utf-8", errors="replace")


def frontmatter_version(text: str) -> str:
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "?"
    match = re.search(r"(?m)^\s+version:\s*[\"']?([0-9]+\.[0-9]+\.[0-9]+)", parts[1])
    return match.group(1) if match else "?"


def rules_block(text: str) -> str | None:
    """Return the text between the rules markers, or None when absent/malformed."""
    starts = [m.start() for m in re.finditer(re.escape(RULES_START), text)]
    ends = [m.start() for m in re.finditer(re.escape(RULES_END), text)]
    if len(starts) != 1 or len(ends) != 1 or starts[0] > ends[0]:
        return None
    return text[starts[0] + len(RULES_START):ends[0]]


def shared_rules_text(root: Path) -> str | None:
    source = root / SHARED_RULES
    if not source.is_file():
        return None
    return rules_block(source.read_text(encoding="utf-8"))


def check_skill(root: Path, skill: Path, contract: Contract, shared_rules: str | None) -> SkillReport:
    name = skill.relative_to(root).as_posix()
    skill_md = (skill / "SKILL.md").read_text(encoding="utf-8")
    report = SkillReport(name, frontmatter_version(skill_md), DEPRECATED_MARKER in skill_md)

    # Shared rules block.
    block = rules_block(skill_md)
    if shared_rules is None:
        report.issues.append(Issue(name, "rules-block-missing", "SKILL.md", 1, f"{SHARED_RULES} has no rules block to compare with"))
    elif RULES_START not in skill_md and RULES_END not in skill_md:
        report.issues.append(Issue(name, "rules-block-missing", "SKILL.md", 1, "run scripts/sync_shared_rules.py"))
    elif block is None:
        report.issues.append(Issue(name, "rules-block-malformed", "SKILL.md", 1, "expected exactly one start marker before one end marker"))
    elif block != shared_rules:
        report.issues.append(Issue(name, "rules-block-stale", "SKILL.md", 1, "block differs from _shared/aisa-rules.md; run scripts/sync_shared_rules.py"))

    for path in skill_files(skill):
        text = read_text(path)
        if text is None:
            continue
        relative = path.relative_to(skill).as_posix()
        in_rules_block = False
        for index, line in enumerate(text.splitlines(), 1):
            if RULES_START in line:
                in_rules_block = True
            if RULES_END in line:
                in_rules_block = False
                continue
            if in_rules_block:
                continue  # the shared block is checked against its source, not scanned
            for match in PLUGIN_ROOT_RE.finditer(line):
                report.issues.append(Issue(name, "plugin-root", relative, index, match.group(0)))
            for match in KEY_LITERAL_RE.finditer(line):
                token = match.group(1)
                rest = token.split("sk-aisa-", 1)[1] if token.startswith("sk-aisa-") else token[3:]
                if not PLACEHOLDER_VALUE_RE.fullmatch(rest):
                    report.issues.append(Issue(name, "literal-key", relative, index, f"{token[:10]}... looks like an API key"))
            for match in KEY_ASSIGNMENT_RE.finditer(line):
                value = match.group("value")
                if not value.startswith(PLACEHOLDER_PREFIXES) and not PLACEHOLDER_VALUE_RE.fullmatch(value.replace("sk-", "")):
                    report.issues.append(Issue(name, "literal-key", relative, index, f"AISA_API_KEY assigned a literal value ({value[:8]}...)"))
            if path.suffix.lower() == ".md" and COST_CLAIM_RE.search(line):
                report.issues.append(Issue(name, "cost-claim", relative, index, "cost is reported in the X-AISA-Customer-Cost-Micros-USD response header, not in usage.cost/credits_remaining"))

        if is_test_file(relative):
            continue  # tests use synthetic URLs by design; key and plugin-root scans above still cover them
        is_python = path.suffix == ".py"
        mentions = list(mentions_from_text(relative, text, contract, relative_paths=not is_python))
        if is_python:
            mentions.extend(mentions_from_python(relative, text, contract))
        for mention in dedupe(mentions):
            report.mentions += 1
            report.issues.extend(check_mention(name, mention, contract, report))
    if report.deprecated:
        for issue in report.issues:
            if issue.kind in ("unknown-path", "unknown-method", "body-not-accepted"):
                issue.kind = "deprecated-stale-path"
    return report


def dedupe(mentions: Iterable[Mention]) -> list[Mention]:
    seen: set[tuple[str, int, str, str | None, bool]] = set()
    result = []
    for mention in mentions:
        key = (mention.file, mention.line, mention.path, mention.method, mention.has_body)
        if key not in seen:
            seen.add(key)
            result.append(mention)
    return result


def check_mention(skill: str, mention: Mention, contract: Contract, report: SkillReport) -> list[Issue]:
    matches: list[str] = []
    for candidate in (mention.path, *mention.alternatives):
        matches = contract.resolve(candidate)
        if matches:
            break
    label = f"{mention.method or 'ANY'} {mention.path}"
    if not matches:
        return [Issue(skill, "unknown-path", mention.file, mention.line, f"{label} is not in the published OpenAPI")]
    issues: list[Issue] = []
    operations = {method: op for known in matches for method, op in contract.operations[known].items()}
    if mention.method is not None and mention.method not in operations:
        return [Issue(skill, "unknown-method", mention.file, mention.line, f"{label}: contract allows {', '.join(sorted(operations))}")]
    candidates = [operations[mention.method]] if mention.method else list(operations.values())
    for op in candidates:
        if op.documented_only:
            report.documented_only.add(f"{op.method} {op.path} ({op.documented_only})")
    if mention.has_body and mention.method and not operations[mention.method].has_body:
        issues.append(Issue(skill, "body-not-accepted", mention.file, mention.line, f"{label} sends a body but the contract declares no requestBody (parameters go in the query string)"))
    if mention.method and operations[mention.method].status == "disabled":
        issues.append(Issue(skill, "disabled-operation", mention.file, mention.line, f"{label} is marked x-aisa-status: disabled"))
    elif mention.method is None and candidates and all(op.status == "disabled" for op in candidates):
        issues.append(Issue(skill, "disabled-operation", mention.file, mention.line, f"{label} is marked x-aisa-status: disabled"))
    return issues


# --------------------------------------------------------------------------- scope & known issues


def changed_skills(root: Path, reference: str, skills: list[Path]) -> list[Path]:
    commands = (
        ["git", "diff", "--name-only", "--diff-filter=ACMRD", f"{reference}...HEAD", "--"],
        ["git", "diff", "--name-only", "--diff-filter=ACMRD", "--"],
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRD", "--"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    changed: set[str] = set()
    for command in commands:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(f"error: {' '.join(command)}: {result.stderr.strip()}")
        changed.update(line for line in result.stdout.splitlines() if line)
    if any(p.startswith(("scripts/", "_shared/", ".github/")) for p in changed):
        return skills
    return [s for s in skills if any(p.startswith(s.relative_to(root).as_posix() + "/") for p in changed)]


def load_known_issues(path: Path) -> dict[str, str]:
    """Tracked issues: ``{"issue": "<skill>:<class>:<file>:<detail>", "reason": "..."}``.

    ``issue`` is matched with ``fnmatch`` so one entry can cover a family of
    paths; an entry that matches nothing is stale and fails the run.
    """
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"error: {path} must be a JSON list of {{\"issue\": ..., \"reason\": ...}}")
    known: dict[str, str] = {}
    for entry in data:
        if not isinstance(entry, dict) or not entry.get("issue") or not entry.get("reason"):
            raise SystemExit(f"error: {path}: each entry needs 'issue' and 'reason'")
        known[str(entry["issue"])] = str(entry["reason"])
    return known


def match_known(key: str, known: dict[str, str]) -> str | None:
    if key in known:
        return key
    for pattern in known:
        if any(ch in pattern for ch in "*?[") and fnmatch.fnmatchcase(key, pattern):
            return pattern
    return None


# --------------------------------------------------------------------------- report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    parser.add_argument("--openapi", type=Path, help="local OpenAPI JSON (offline mode)")
    parser.add_argument("--openapi-url", default=DEFAULT_OPENAPI_URL, help="download URL used when --openapi is absent")
    parser.add_argument("--timeout", type=float, default=120.0, help="download timeout in seconds")
    parser.add_argument("--cache-dir", type=Path, help="where to store the downloaded OpenAPI (default: a temp dir)")
    parser.add_argument("--max-download-mib", type=int, default=MAX_DOWNLOAD_MIB, help="abort when the OpenAPI download exceeds this size")
    parser.add_argument("--changed-from", metavar="REF", help="only check skills changed from this Git ref")
    parser.add_argument("--skill", action="append", help="check only this <category>/<skill> (repeatable)")
    parser.add_argument("--known-issues", type=Path, default=None, help=f"tracked issues file (default: {KNOWN_ISSUES} if present)")
    parser.add_argument("--fail-on-warnings", action="store_true", help="treat warning classes as failures")
    parser.add_argument("--json", type=Path, help="write a machine-readable report here")
    parser.add_argument("--quiet", action="store_true", help="print only skills with findings and the summary")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    contract = load_contract(args.openapi, args.openapi_url, args.timeout, args.cache_dir,
                             max_bytes=args.max_download_mib * 1024 * 1024)
    shared = shared_rules_text(root)
    skills = skill_directories(root)
    if args.changed_from:
        skills = changed_skills(root, args.changed_from, skills)
    if args.skill:
        wanted = set(args.skill)
        skills = [s for s in skills if s.relative_to(root).as_posix() in wanted]
    known_path = args.known_issues or (root / KNOWN_ISSUES)
    known = load_known_issues(known_path)
    used_known: set[str] = set()

    reports = []
    for skill in skills:
        report = check_skill(root, skill, contract, shared)
        remaining = []
        for issue in report.issues:
            pattern = match_known(issue.key, known)
            if pattern is not None:
                used_known.add(pattern)
                report.known.append(issue)
                issue.detail = f"{issue.detail}  [{known[pattern]}]"
            else:
                remaining.append(issue)
        report.issues = remaining
        reports.append(report)

    stale_known = sorted(set(known) - used_known)
    print(f"AIsa skill validator — contract: {contract.title}")
    print(f"openapi: {contract.source}")
    print(f"openapi-sha256: {contract.sha256}")
    print(f"operations: {sum(len(v) for v in contract.operations.values())}  skills: {len(reports)}"
          f"{'  scope: changed from ' + args.changed_from if args.changed_from else ''}")
    print()
    totals = {kind: 0 for kind in ALL_CLASSES}
    failed_skills = 0
    for report in reports:
        counts = report.counts()
        for kind, count in counts.items():
            totals[kind] = totals.get(kind, 0) + count
        failed = report.failed or (args.fail_on_warnings and report.issues)
        failed_skills += bool(failed)
        status = "FAIL" if failed else ("WARN" if report.issues else "OK")
        if args.quiet and not report.issues and not report.known:
            continue
        flags = " deprecated" if report.deprecated else ""
        summary = ", ".join(f"{kind}={count}" for kind, count in sorted(counts.items())) or "no findings"
        print(f"== {report.skill} (v{report.version}){flags}: {status} — {report.mentions} API mentions; {summary}")
        for issue in sorted(report.issues, key=lambda i: (i.kind, i.file, i.line)):
            print(f"   - {issue}")
        for issue in report.known:
            print(f"   ~ KNOWN {issue}")
        for entry in sorted(report.documented_only):
            print(f"   i documented-only route: {entry}")
    print()
    print("summary:")
    for kind in ALL_CLASSES:
        if totals.get(kind):
            severity = "fail" if kind in FAILURE_CLASSES or args.fail_on_warnings else "warn"
            print(f"  {kind:<22} {totals[kind]:>4}  ({severity})")
    if used_known:
        print(f"  known-issues (tracked) {len(used_known):>4}  (listed in {known_path.relative_to(root) if known_path.is_relative_to(root) else known_path})")
    for key in stale_known:
        print(f"  stale known-issue entry: {key}")
    failures = sum(totals[k] for k in FAILURE_CLASSES)
    warnings = sum(totals[k] for k in WARNING_CLASSES)
    print(f"  skills: {len(reports)} checked, {failed_skills} failing; failures={failures} warnings={warnings}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "contract": {"title": contract.title, "source": contract.source, "sha256": contract.sha256},
            "skills": [
                {
                    "skill": r.skill, "version": r.version, "deprecated": r.deprecated,
                    "mentions": r.mentions, "counts": r.counts(),
                    "issues": [i.__dict__ for i in r.issues],
                    "known": [i.__dict__ for i in r.known],
                    "documented_only": sorted(r.documented_only),
                }
                for r in reports
            ],
            "totals": totals, "stale_known_issues": stale_known,
        }, indent=2) + "\n", encoding="utf-8")

    if failures or stale_known or (args.fail_on_warnings and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
