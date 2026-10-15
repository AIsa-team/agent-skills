#!/usr/bin/env python3
"""AIsa Similarweb client: live contract discovery, quotes, and recorded execution.

  discover [--refresh]               fetch/revalidate the public contract
  describe ROUTE                    parameters, examples, constraints, response schemas
  check ROUTE k=v ...                local supported-schema checks; no paid request
  window                            unverified previous-complete-month candidate; no paid probe
  quote ROUTE k=v ...                authenticated free cost estimate
  call ROUTE k=v ... --max-usd USD   execute with an admission estimate limit (NOT a final-charge cap)
       [--idem KEY] [--out FILE] [--task-ledger FILE --task-budget-usd USD]
  usage [--days 1]                   aggregate API-key usage, not task-specific reconciliation
  reconcile RECORD --charged-usd USD --evidence TEXT
                                    record a charge verified separately in Usage & Logs

ROUTE accepts /website/traffic-engagement, /similarweb/... or /apis/v1/similarweb/....
Set AISA_API_KEY for authenticated requests. Contract and request records live in
AISA_SIMILARWEB_CACHE or ~/.cache/aisa-similarweb. Requests are never retried automatically.
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path
from contextlib import contextmanager
from http.client import HTTPException
import hashlib
from datetime import datetime, timedelta, timezone
import math
import tempfile

CONTRACT_URL = "https://aisa.one/docs/openapi/similarweb.json"
API = "https://api.aisa.one"
CACHE = Path(os.getenv("AISA_SIMILARWEB_CACHE") or Path.home() / ".cache" / "aisa-similarweb")


# ---------------------------------------------------------------- http
def key() -> str:
    k = os.getenv("AISA_API_KEY", "").strip()
    if not k:
        raise SystemExit("AISA_API_KEY is not set.")
    return k


def http(url: str, headers: dict | None = None, auth: bool = True, timeout: int = 90):
    req = urllib.request.Request(url)
    if auth:
        req.add_header("Authorization", "Bearer " + key())
    for h, v in (headers or {}).items():
        req.add_header(h, str(v))
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        status, hdrs, raw = resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        status, hdrs, raw = e.code, dict(e.headers), e.read()
    try:
        body = json.loads(raw)
    except Exception:
        body = raw.decode(errors="replace")
    return status, {k.lower(): v for k, v in hdrs.items()}, body


# ---------------------------------------------------------------- contract
def _read_cache(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise ValueError("expected a JSON object")
        return value
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        print(f"warning: ignoring invalid cache {path.name}: {e}", file=sys.stderr)
        return None


def _write_cache(path: Path, value: dict):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=path.name + ".", delete=False) as f:
            temporary = Path(f.name)
            json.dump(value, f)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load_contract(refresh: bool = False, quiet: bool = True) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    spec_f, meta_f = CACHE / "contract.json", CACHE / "contract.meta.json"
    cached, meta = _read_cache(spec_f), _read_cache(meta_f) or {}
    if cached is not None and not isinstance(cached.get("paths"), dict):
        print("warning: ignoring cached contract without a paths object", file=sys.stderr)
        cached = None
    try:
        age, max_age = time.time() - float(meta.get("fetched_at", 0)), float(meta.get("max_age", 0))
        fresh = math.isfinite(age) and math.isfinite(max_age) and 0 <= age < max_age
    except (TypeError, ValueError):
        fresh = False
    if cached is not None and not refresh and fresh:
        return cached
    headers = {"If-None-Match": meta["etag"]} if cached is not None and meta.get("etag") and not refresh else {}
    try:
        status, hdrs, body = http(CONTRACT_URL, headers, auth=False)
    except Exception as e:
        if cached is not None:
            print(f"warning: contract unreachable ({e}); using cached copy, freshness unverified", file=sys.stderr)
            return cached
        raise SystemExit(f"cannot fetch contract: {e}")
    m = re.search(r"max-age=(\d+)", hdrs.get("cache-control", ""))
    prior = meta if status == 304 else {}
    new_meta = {"etag": hdrs.get("etag", prior.get("etag")),
                "last_modified": hdrs.get("last-modified", prior.get("last_modified")),
                "fetched_at": time.time(), "max_age": int(m.group(1)) if m else 0}
    if status == 304 and cached is not None:
        _write_cache(meta_f, new_meta)
        if not quiet:
            print("contract unchanged (304)", file=sys.stderr)
        return cached
    if status != 200 or not isinstance(body, dict) or not isinstance(body.get("paths"), dict):
        raise SystemExit(f"contract fetch failed: HTTP {status}")
    _write_cache(spec_f, body)
    _write_cache(meta_f, new_meta)
    if not quiet:
        print(f"contract fetched ({len(body['paths'])} routes)", file=sys.stderr)
    return body


def base_url(spec: dict) -> str:
    default = API if any(p.startswith("/apis/v1/") for p in spec["paths"]) else API + "/apis/v1"
    servers = spec.get("servers") or [{"url": default}]
    return servers[0]["url"].rstrip("/")


def norm_route(route: str) -> str:
    route = "/" + route.strip("/")
    return re.sub(r"^/(?:apis/v1/)?similarweb(?=/|$)", "", route) or "/"


def ops(spec: dict) -> dict:
    return {norm_route(path): (path, item["get"]) for path, item in spec["paths"].items() if item.get("get")}


def get_op(spec: dict, route: str):
    table, r = ops(spec), norm_route(route)
    if r not in table:
        close = [k for k in table if r.split("/")[-1][:6] in k]
        raise SystemExit(json.dumps({"error": f"route {r} is not in the contract", "similar_routes": close or sorted(table)}, indent=2))
    return table[r]


def _load_route(route: str):
    spec = load_contract()
    refreshed = norm_route(route) not in ops(spec)
    if refreshed:
        spec = load_contract(refresh=True)
    path, op = get_op(spec, route)
    return spec, path, op, refreshed


def param_line(p: dict) -> str:
    s, bits = p.get("schema", {}), []
    if s.get("enum"):
        bits.append("|".join(map(str, s["enum"])))
    elif s.get("type"):
        bits.append(str(s["type"]))
    for key, label in (("minimum", "min"), ("maximum", "max"), ("minLength", "min length"),
                       ("maxLength", "max length"), ("x-aisa-minItems", "min items"), ("x-aisa-maxItems", "max items")):
        if key in s:
            bits.append(f"{label} {s[key]}")
    if "default" in s:
        bits.append(f"default {s['default']}")
    if "x-aisa-default-policy" in s:
        bits.append(f"default policy {s['x-aisa-default-policy']}")
    return f"{p['name']}[{', '.join(bits)}]" if bits else p["name"]


def date_rule(op: dict) -> str:
    d = op.get("description") or ""
    m = re.search(r"(Date (?:constraint|window)[^:]*:\s*.*?\.)(?:\s|$)", d)
    rules = [m.group(1)] if m else []
    for note in op.get("x-aisa-constraints", {}).get("notes", []):
        if isinstance(note, str) and re.search(r"\b(date|dates|month|months|monthly|granularity|window)\b", note, re.I):
            rules.append(note)
    return " ".join(dict.fromkeys(rules))


def check_request(op: dict, params: dict) -> list[str]:
    """Check supported scalar and AIsa delimited-list rules, not all JSON Schema or provider semantics."""
    declared = {p["name"]: p for p in op.get("parameters", [])}
    problems = []
    for name, p in declared.items():
        if p.get("required") and name not in params:
            description = p.get("description") or p.get("schema", {}).get("description", "")
            problems.append(f"missing required parameter: {param_line(p)} — {description}".strip(" —"))
    for name, value in params.items():
        p = declared.get(name)
        if not p:
            problems.append(f"parameter not in contract: {name}")
            continue
        s, number = p.get("schema", {}), None
        kind = s.get("type")
        if "enum" in s:
            choices = [str(x).lower() if isinstance(x, bool) else str(x) for x in s["enum"]]
            description = str(p.get("description", "")) + " " + str(s.get("description", ""))
            candidate = value
            if "case-insensitive" in description.lower():
                candidate, choices = candidate.casefold(), [x.casefold() for x in choices]
            if candidate not in choices:
                problems.append(f"{name}={value} not allowed; contract allows {s['enum']}")
        if kind == "integer":
            if not re.fullmatch(r"-?[0-9]+", value):
                problems.append(f"{name}={value} must be an integer")
            else:
                number = int(value)
        elif kind == "number":
            try:
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError()
            except ValueError:
                number = None
                problems.append(f"{name}={value} must be a finite number")
        elif kind == "boolean" and value not in ("true", "false"):
            problems.append(f"{name}={value} must be true or false")
        if number is not None:
            if "minimum" in s and number < s["minimum"]:
                problems.append(f"{name}={value} is below contract minimum {s['minimum']}")
            if "maximum" in s and number > s["maximum"]:
                problems.append(f"{name}={value} exceeds contract maximum {s['maximum']}")
        if kind == "string":
            if "minLength" in s and len(value) < s["minLength"]:
                problems.append(f"{name} is shorter than contract minLength {s['minLength']}")
            if "maxLength" in s and len(value) > s["maxLength"]:
                problems.append(f"{name} is longer than contract maxLength {s['maxLength']}")
            if "pattern" in s:
                try:
                    if not re.search(s["pattern"], value):
                        problems.append(f"{name} does not match contract pattern {s['pattern']}")
                except re.error:
                    problems.append(f"{name}: contract pattern is unsupported by the local validator; inspect describe")
        delimiter = s.get("x-aisa-delimiter")
        if isinstance(delimiter, str) and delimiter:
            items = value.split(delimiter) if value else []
            if any(not item.strip() for item in items):
                problems.append(f"{name} contains an empty item; remove empty values or extra delimiters")
            if "x-aisa-minItems" in s and len(items) < s["x-aisa-minItems"]:
                problems.append(f"{name} needs at least {s['x-aisa-minItems']} items")
            if "x-aisa-maxItems" in s and len(items) > s["x-aisa-maxItems"]:
                problems.append(f"{name} exceeds contract maximum of {s['x-aisa-maxItems']} items")
            if "x-aisa-item-enum" in s:
                invalid = [item for item in items if item not in s["x-aisa-item-enum"]]
                if invalid:
                    problems.append(f"{name} has unsupported items {invalid}; contract allows {s['x-aisa-item-enum']}")
    return problems


def _parse_params(kv: list[str]) -> dict:
    params, problems = {}, []
    for token in kv:
        if "=" not in token or not token.split("=", 1)[0]:
            problems.append(f"expected name=value, got {token!r}")
            continue
        name, value = token.split("=", 1)
        if name in params:
            problems.append(f"duplicate parameter: {name}; supply it once")
        params[name] = value
    if problems:
        raise SystemExit(json.dumps({"valid": False, "problems": problems}, indent=2))
    return params


def validated(route: str, kv: list[str]):
    params = _parse_params(kv)
    spec, path, op, refreshed = _load_route(route)
    problems = check_request(op, params)
    if problems and not refreshed:  # A stale contract gets one refresh per invocation.
        spec = load_contract(refresh=True)
        path, op = get_op(spec, route)
        problems = check_request(op, params)
    return spec, path, op, params, problems


def build_url(spec: dict, path: str, params: dict) -> str:
    return base_url(spec) + path + ("?" + urllib.parse.urlencode(params) if params else "")


# ---------------------------------------------------------------- commands
def cmd_discover(a):
    spec = load_contract(refresh=a.refresh, quiet=False)
    print(f"# {spec.get('info', {}).get('title', 'contract')} · base {base_url(spec)} · {len(ops(spec))} routes")
    for route, (path, op) in ops(spec).items():
        ps = op.get("parameters", [])
        req = ", ".join(param_line(p) for p in ps if p.get("required"))
        opt = ", ".join(param_line(p) for p in ps if not p.get("required")) or "—"
        rule = date_rule(op)
        print(f"{route}\n  required: {req}\n  optional: {opt}" + (f"\n  dates: {rule}" if rule else ""))


def _response_definitions(spec: dict, responses: dict) -> dict:
    """Include only local definitions referenced by this operation's responses."""
    definitions = {}
    def visit(value):
        if isinstance(value, dict):
            ref = value.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/") and ref not in definitions:
                target = spec
                try:
                    for part in ref[2:].split("/"):
                        target = target[part.replace("~1", "/").replace("~0", "~")]
                except (KeyError, TypeError):
                    target = {"unresolved": True}
                definitions[ref] = target
                visit(target)
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
    visit(responses)
    return definitions


def cmd_describe(a):
    spec, path, op, _ = _load_route(a.route)
    def parameter(p):
        result = {"name": p["name"], "schema": p.get("schema", {}),
                  "description": p.get("description") or p.get("schema", {}).get("description"),
                  "examples": p.get("examples", {})}
        if "example" in p:
            result["example"] = p["example"]
        return result
    responses = op.get("responses", {})
    print(json.dumps({"route": norm_route(a.route), "path": path, "url": build_url(spec, path, {}),
                      "summary": op.get("summary"), "description": op.get("description"),
                      "constraints": op.get("x-aisa-constraints", {}),
                      "required": [parameter(p) for p in op.get("parameters", []) if p.get("required")],
                      "optional": [parameter(p) for p in op.get("parameters", []) if not p.get("required")],
                      "responses": responses, "response_definitions": _response_definitions(spec, responses),
                      "response_pending": op.get("x-aisa-response-pending")}, indent=2))


def cmd_check(a):
    spec, path, op, params, problems = validated(a.route, a.kv)
    out = {"valid": not problems, "problems": problems,
           "validation_scope": "Supported local scalar and AIsa delimited-list constraints only; not full JSON Schema or provider/date availability validation.",
           "constraints": op.get("x-aisa-constraints", {})}
    if date_rule(op):
        out["date_rule"] = date_rule(op)
    print(json.dumps(out, indent=2))
    sys.exit(0 if not problems else 1)


def cmd_window(a):
    spec = load_contract()
    today = datetime.now(timezone.utc).date()
    candidate = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    policies, constraints = [], []
    for route, (_, op) in ops(spec).items():
        for p in op.get("parameters", []):
            policy = p.get("schema", {}).get("x-aisa-default-policy")
            if policy is not None:
                policies.append({"route": route, "parameter": p["name"], "policy": policy})
        if date_rule(op):
            constraints.append({"route": route, "constraints": op.get("x-aisa-constraints", {}), "date_rule": date_rule(op)})
    print(json.dumps({"latest_month": None, "candidate_month": candidate, "availability": "unverified",
                      "default_policies": policies, "constraints": constraints,
                      "note": "The candidate is the previous complete UTC calendar month, not verified provider availability. Preserve user-requested dates; contract examples are not availability evidence. No authenticated request was made."}, indent=2))


def price_micros(value: str) -> int:
    """Parse USD without floating-point rounding or non-finite budget values."""
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,6})?", str(value)):
        raise argparse.ArgumentTypeError("USD must be a nonnegative decimal with at most six decimal places")
    whole, _, fraction = str(value).partition(".")
    return int(whole) * 1_000_000 + int(fraction.ljust(6, "0"))


def usd_text(micros: int) -> str:
    return f"{micros // 1_000_000}.{micros % 1_000_000:06d}"


def cost_integer(value) -> bool:
    return type(value) is int and value >= 0


def quote_request(url: str) -> dict:
    status, _, body = http(url, {"X-AISA-Cost-Mode": "quote"})
    micros = body.get("estimated_cost_micros_usd") if isinstance(body, dict) else None
    if (status != 200 or not isinstance(body, dict) or body.get("object") != "cost_estimate"
            or not cost_integer(micros)):
        return {"ok": False, "status": status, "error": body,
                "note": "expected a cost_estimate with nonnegative integer micro-USD; no execution attempted"}
    return {"ok": True, "status": 200, "usd": micros / 1_000_000,
            "estimated_cost_micros_usd": micros, "may_exceed_estimate": body.get("may_exceed_estimate"),
            "limit_semantics": "admission estimate only; the final charge is not capped"}


def quoted(a):
    spec, path, op, params, problems = validated(a.route, a.kv)
    if problems:
        print(json.dumps({"valid": False, "problems": problems, "note": "no execution attempted"}, indent=2))
        sys.exit(1)
    url = build_url(spec, path, params)
    q = quote_request(url)
    if not q["ok"] and q["status"] == 400:
        spec = load_contract(refresh=True)
        path, op = get_op(spec, a.route)
        problems = check_request(op, params)
        q["problems_after_refresh"] = problems
        q["note"] = "quote rejected; inspect constraints and error details; rejection alone does not establish schema drift"
    return spec, path, op, params, url, q


def cmd_quote(a):
    _, _, op, _, _, q = quoted(a)
    if q["ok"]:
        q["constraints"] = op.get("x-aisa-constraints", {})
        if date_rule(op):
            q["date_rule"] = date_rule(op)
    print(json.dumps(q, indent=2))
    sys.exit(0 if q["ok"] else 1)


def save_execution(path: Path, data: dict, *, exclusive: bool = False):
    """Durably save the request before dispatch, and atomically replace after it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive:
        with path.open("x", encoding="utf-8") as handle:
            os.chmod(path, 0o600)
            json.dump(data, handle, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        return
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            os.chmod(temporary, 0o600)
            json.dump(data, handle, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def execution_lock(path: Path):
    """Serialize ledger use; never steal an existing lock after an interruption."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError(f"execution lock exists: {lock}; check for an active process or reconcile interrupted work before removing it")
    try:
        os.write(descriptor, str(os.getpid()).encode())
        yield
    finally:
        os.close(descriptor)
        lock.unlink()


def read_ledger(path: Path, budget: int | None) -> dict:
    if path.exists():
        ledger = json.loads(path.read_text())
        if (not isinstance(ledger, dict) or ledger.get("schema_version") != 1
                or not cost_integer(ledger.get("budget_micros_usd")) or not isinstance(ledger.get("requests"), list)
                or any(not isinstance(entry, dict) or not isinstance(entry.get("request_record"), str)
                       or not Path(entry["request_record"]).is_absolute() for entry in ledger["requests"])):
            raise ValueError("invalid task ledger")
        if budget is not None and budget != ledger["budget_micros_usd"]:
            raise ValueError("task budget differs from the existing ledger; review its recorded budget before changing it")
        return ledger
    if budget is None:
        raise ValueError("a new --task-ledger requires --task-budget-usd")
    return {"schema_version": 1, "budget_micros_usd": budget, "requests": []}


def ledger_remaining(ledger: dict) -> int:
    charged = 0
    for entry in ledger["requests"]:
        record = json.loads(Path(entry["request_record"]).read_text())
        cost = record.get("cost_micros_usd")
        if not cost_integer(cost):
            raise ValueError(f"unresolved charge in {entry['request_record']}; reconcile before further task spending")
        charged += cost
    return ledger["budget_micros_usd"] - charged


def execute_call(a, params: dict, url: str, q: dict):
    idem = a.idem or ("sw-" + uuid.uuid4().hex)
    if not re.fullmatch(r"[\x21-\x7e]{1,200}", idem):
        raise ValueError("Idempotency-Key must contain 1–200 printable ASCII characters without spaces")
    record_path = (CACHE / "requests" / (hashlib.sha256(idem.encode()).hexdigest() + ".json")).resolve()
    ledger_path = Path(a.task_ledger).resolve() if a.task_ledger else None
    with execution_lock(ledger_path or record_path):
        if record_path.exists():
            raise ValueError(f"logical request already recorded at {record_path}; inspect/reconcile it instead of redispatching")
        ledger = read_ledger(ledger_path, a.task_budget_usd) if ledger_path else None
        limit = a.max_usd
        if ledger is not None:
            remaining = ledger_remaining(ledger)
            if remaining < q["estimated_cost_micros_usd"]:
                print(json.dumps({"refused": True, "reason": "quote exceeds remaining task budget",
                                  "remaining_micros_usd": remaining, "quoted_usd": q["usd"]}, indent=2))
                sys.exit(2)
            limit = min(limit, remaining)
        if a.out and Path(a.out).resolve() in {record_path, ledger_path}:
            raise ValueError("--out must not overwrite the request record or task ledger")
        record = {"schema_version": 1, "created_at": time.time(), "url": url,
                  "idempotency_key": idem, "request_record": str(record_path),
                  "task_ledger": str(ledger_path) if ledger_path else None,
                  "requested_period": {k: params[k] for k in ("month", "start_date", "end_date") if k in params},
                  "outcome": "pending", "quoted_usd": q["usd"],
                  "quoted_cost_micros_usd": q["estimated_cost_micros_usd"],
                  "max_estimate_micros_usd": limit, "may_exceed_estimate": q["may_exceed_estimate"],
                  "limit_semantics": q["limit_semantics"], "cost_micros_usd": None,
                  "cost_usd": None, "cost_status": "unknown"}
        save_execution(record_path, record, exclusive=True)
        if ledger is not None:
            ledger["requests"].append({"request_record": str(record_path)})
            save_execution(ledger_path, ledger)
        headers = {"X-AISA-Max-Price-USD": usd_text(limit), "Idempotency-Key": idem}
        t0 = time.time()
        try:
            status, hdrs, body = http(url, headers)
        except (OSError, ValueError, HTTPException) as error:
            record.update(outcome="unknown", error=str(error), status=None,
                          note="execution may have been admitted; inspect Usage & Logs before retrying or changing the key")
        else:
            raw_cost = hdrs.get("x-aisa-customer-cost-micros-usd")
            cost = int(raw_cost) if isinstance(raw_cost, str) and re.fullmatch(r"[0-9]+", raw_cost) else None
            record.update(status=status, outcome="succeeded" if status == 200 else "http_error",
                          cost_micros_usd=cost, cost_usd=cost / 1_000_000 if cost is not None else None,
                          cost_status="reported" if cost is not None else "unknown",
                          estimate_limit_exceeded=cost > limit if cost is not None else None,
                          request_id=hdrs.get("x-request-id"), data=body)
            if isinstance(body, dict):
                meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
                record["data_period"] = {"start_date": meta.get("start_date"), "end_date": meta.get("end_date")}
                data = body.get("data")
                record["data_month"] = data.get("month") if isinstance(data, dict) else None
                record["last_updated"] = meta.get("last_updated")
                if meta.get("error_message"):
                    record["note"] = meta["error_message"]
            if status == 409:
                record["note"] = "key already admitted; this is not a replay. Reconcile the original request before any new execution"
            if cost is None:
                record["cost_note"] = "missing or invalid cost metadata means unknown, not zero; reconcile using Usage & Logs"
        record["latency_s"] = round(time.time() - t0, 2)
        try:
            save_execution(record_path, record)
        except OSError as error:
            record["record_write_error"] = str(error)
            record["note"] = "response is shown here, but the durable record remains unresolved; reconcile before retrying"
        if ledger is not None:
            try:
                remaining = ledger_remaining(ledger)
                record["task_remaining_micros_usd"] = remaining
                record["task_budget_exceeded"] = remaining < 0
            except ValueError:
                record["task_remaining_micros_usd"] = None
        output_error = False
        if a.out:
            try:
                save_execution(Path(a.out), record)
            except OSError as error:
                output_error = True
                record["output_error"] = str(error)
                print(json.dumps(record, indent=2))
            else:
                print(json.dumps({**{k: v for k, v in record.items() if k != "data"}, "output_file": a.out}, indent=2))
        else:
            print(json.dumps(record, indent=2))
        sys.exit(0 if record.get("status") == 200 and not output_error and "record_write_error" not in record else 1)


def cmd_call(a):
    if a.task_budget_usd is not None and not a.task_ledger:
        raise ValueError("--task-budget-usd requires --task-ledger")
    _, _, _, params, url, q = quoted(a)
    if not q["ok"]:
        print(json.dumps(q, indent=2))
        sys.exit(1)
    if a.max_usd is None:
        print(json.dumps({"needs_budget": True, "quoted_usd": q["usd"],
                          "may_exceed_estimate": q["may_exceed_estimate"], "limit_semantics": q["limit_semantics"],
                          "note": "no execution attempted; use --max-usd for the authorized per-call estimate limit"}, indent=2))
        sys.exit(3)
    if q["estimated_cost_micros_usd"] > a.max_usd:
        print(json.dumps({"refused": True, "quoted_usd": q["usd"], "max_usd": a.max_usd / 1_000_000,
                          "note": "quote exceeds the authorized estimate limit; no execution attempted"}, indent=2))
        sys.exit(2)
    execute_call(a, params, url, q)


def cmd_reconcile(a):
    path = Path(a.record).resolve()
    record = json.loads(path.read_text())
    lock_path = Path(record["task_ledger"]) if record.get("task_ledger") else path
    with execution_lock(lock_path):
        record = json.loads(path.read_text())
        if record.get("schema_version") != 1 or not record.get("idempotency_key"):
            raise ValueError("not a Similarweb execution record")
        if not a.evidence.strip():
            raise ValueError("provide Usage & Logs evidence for the reconciled charge")
        record.setdefault("reconciliations", []).append({"at": time.time(), "evidence": a.evidence,
                                                         "previous_cost_micros_usd": record.get("cost_micros_usd"),
                                                         "charged_micros_usd": a.charged_usd})
        record.update(cost_micros_usd=a.charged_usd, cost_usd=a.charged_usd / 1_000_000, cost_status="reconciled")
        save_execution(path, record)
    print(json.dumps({"request_record": str(path), "cost_micros_usd": a.charged_usd,
                      "note": "recorded supplied reconciliation evidence; no API call made"}, indent=2))


def cmd_usage(a):
    end = int(time.time())
    start = end - 86400 * a.days
    status, _, body = http(f"{API}/v1/usage?start_time={start}&end_time={end}")
    if status == 200 and isinstance(body, dict) and isinstance(body.get("totals"), dict):
        t = body["totals"]
        charged = t.get("charged_micros_usd")
        print(json.dumps({"days": a.days, "requests": t.get("requests"), "failed": t.get("failed_requests"),
                          "charged_micros_usd": charged if cost_integer(charged) else None,
                          "charged_usd": charged / 1_000_000 if cost_integer(charged) else None,
                          "scope": "aggregate usage for the API key and time window; not a task ledger"}, indent=2))
        sys.exit(0 if cost_integer(charged) else 1)
    print(json.dumps({"status": status, "body": body}, indent=2))
    sys.exit(1)


def positive_days(value):
    if not re.fullmatch(r"[0-9]+", value) or int(value) < 1:
        raise argparse.ArgumentTypeError("days must be a positive integer")
    return int(value)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("discover"); s.add_argument("--refresh", action="store_true"); s.set_defaults(fn=cmd_discover)
    s = sub.add_parser("describe"); s.add_argument("route"); s.set_defaults(fn=cmd_describe)
    for name, fn in (("check", cmd_check), ("quote", cmd_quote)):
        s = sub.add_parser(name); s.add_argument("route"); s.add_argument("kv", nargs="*"); s.set_defaults(fn=fn)
    s = sub.add_parser("call"); s.add_argument("route"); s.add_argument("kv", nargs="*")
    s.add_argument("--max-usd", type=price_micros, default=None, help="authorized per-call estimate limit, not a final-charge ceiling")
    s.add_argument("--idem", default=None); s.add_argument("--out", default=None)
    s.add_argument("--task-ledger", default=None, help="file tracking this task's actual charges and unresolved requests")
    s.add_argument("--task-budget-usd", type=price_micros, default=None, help="approved total for a new task ledger")
    s.set_defaults(fn=cmd_call)
    s = sub.add_parser("window"); s.set_defaults(fn=cmd_window)
    s = sub.add_parser("usage"); s.add_argument("--days", type=positive_days, default=1); s.set_defaults(fn=cmd_usage)
    s = sub.add_parser("reconcile"); s.add_argument("record")
    s.add_argument("--charged-usd", type=price_micros, required=True)
    s.add_argument("--evidence", required=True); s.set_defaults(fn=cmd_reconcile)
    a = p.parse_args()
    try:
        a.fn(a)
    except (OSError, ValueError, KeyError, HTTPException) as error:
        print(json.dumps({"error": str(error)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
