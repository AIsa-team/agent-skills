"""Exact, durable accounting for AIsa requests. No paid request is retried here.

Budgets limit admitted estimates. Provider-reported final charges may exceed an
estimate; those charges are recorded in full. Missing charges remain unknown.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import threading
from typing import Callable
from urllib.parse import quote as quote_url, quote_plus, urlsplit
import uuid


# Verified 2026-10-15 against the shipped Twitter operations in AIsa OpenAPI.
# All allowlisted routes explicitly declare quote, max_price and idempotency.
# spaces/detail and unexposed write operations deliberately remain unsupported.
QUOTABLE_OPERATIONS = frozenset({
    ('GET', '/apis/v1/twitter/article'),
    ('GET', '/apis/v1/twitter/community/get_tweets_from_all_community'),
    ('GET', '/apis/v1/twitter/community/info'),
    ('GET', '/apis/v1/twitter/community/members'),
    ('GET', '/apis/v1/twitter/community/moderators'),
    ('GET', '/apis/v1/twitter/community/tweets'),
    ('GET', '/apis/v1/twitter/list/followers'),
    ('GET', '/apis/v1/twitter/list/members'),
    ('GET', '/apis/v1/twitter/trends'),
    ('GET', '/apis/v1/twitter/tweet/advanced_search'),
    ('GET', '/apis/v1/twitter/tweet/quotes'),
    ('GET', '/apis/v1/twitter/tweet/replies'),
    ('GET', '/apis/v1/twitter/tweet/retweeters'),
    ('GET', '/apis/v1/twitter/tweet/thread_context'),
    ('GET', '/apis/v1/twitter/tweets'),
    ('GET', '/apis/v1/twitter/user/batch_info_by_ids'),
    ('GET', '/apis/v1/twitter/user/check_follow_relationship'),
    ('GET', '/apis/v1/twitter/user/followers'),
    ('GET', '/apis/v1/twitter/user/followings'),
    ('GET', '/apis/v1/twitter/user/info'),
    ('GET', '/apis/v1/twitter/user/last_tweets'),
    ('GET', '/apis/v1/twitter/user/mentions'),
    ('GET', '/apis/v1/twitter/user/search'),
    ('GET', '/apis/v1/twitter/user/verifiedFollowers'),
    ('GET', '/apis/v1/twitter/user_about'),
    ('POST', '/apis/v1/twitter/auth_twitter'),
    ('POST', '/apis/v1/twitter/post_twitter'),
    ('POST', '/apis/v1/twitter/upload_media'),
})


class CostControlError(RuntimeError):
    """A paid request cannot safely proceed; callers must not retry it."""

    retryable = False


def is_micros(value: object) -> bool:
    return type(value) is int and value >= 0


def parse_usd(value: str) -> int:
    """Parse plain nonnegative USD with at most six decimal places, exactly."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,6})?", value):
        raise ValueError("USD must be a nonnegative plain decimal with at most 6 decimal places")
    whole, _, fraction = value.partition(".")
    return int(whole) * 1_000_000 + int(fraction.ljust(6, "0") or "0")


def usd_text(micros: int) -> str:
    if not is_micros(micros):
        raise ValueError("expected nonnegative integer micro-USD")
    return f"{micros // 1_000_000}.{micros % 1_000_000:06d}"


def utc_day() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes
    read_error: str | None = None


def validate_operation(method: str, url: str) -> None:
    """Reject undeclared routes before even a supposedly free quote is sent."""
    target = urlsplit(url)
    if (target.scheme != "https" or target.netloc != "api.aisa.one" or target.fragment
            or (method.upper(), target.path) not in QUOTABLE_OPERATIONS):
        raise CostControlError("This AIsa operation has no verified free-quote capability; no request sent")


def validate_quote(response: Response) -> dict:
    """Accept only the documented, unambiguous quote response contract."""
    try:
        quote = json.loads(response.body.decode("utf-8"), parse_constant=_invalid_json_constant)
    except (ValueError, UnicodeError) as exc:
        raise CostControlError("Invalid cost quote; no paid request sent") from exc
    if (response.status != 200 or response.read_error or not isinstance(quote, dict)
            or quote.get("object") != "cost_estimate"
            or not is_micros(quote.get("estimated_cost_micros_usd"))
            or type(quote.get("may_exceed_estimate")) is not bool
            or quote.get("success") is False or quote.get("ok") is False
            or quote.get("error") or quote.get("errors")):
        raise CostControlError("Invalid cost quote; expected integer micro-USD and a boolean may_exceed_estimate; no paid request sent")
    return quote


def _invalid_json_constant(value):
    raise ValueError("Non-finite numbers are not valid JSON")


@contextmanager
def _locked(path: Path):
    """OS lock releases on process death; a persisted pending request does not."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(path) + ".lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _save(path: Path, ledger: dict) -> None:
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            os.chmod(temporary, 0o600)
            json.dump(ledger, handle, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def _load(path: Path) -> dict:
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CostControlError(f"Cannot read cost ledger {path}: {exc}") from exc
    if (not isinstance(ledger, dict) or ledger.get("schema_version") != 1
            or not is_micros(ledger.get("budget_micros_usd"))
            or not isinstance(ledger.get("requests"), list)):
        raise CostControlError(f"Invalid cost ledger: {path}")
    ids = set()
    for record in ledger["requests"]:
        if (not isinstance(record, dict) or not isinstance(record.get("request_id"), str)
                or record["request_id"] in ids
                or (record.get("cost_micros_usd") is not None
                    and not is_micros(record["cost_micros_usd"]))):
            raise CostControlError(f"Invalid request record in cost ledger: {path}")
        ids.add(record["request_id"])
    return ledger


def _summary(ledger: dict, path: Path) -> dict:
    records = ledger["requests"]
    unknown = [r["request_id"] for r in records if r.get("cost_micros_usd") is None]
    known = sum(r["cost_micros_usd"] for r in records if r.get("cost_micros_usd") is not None)
    budget = ledger["budget_micros_usd"]
    return {
        "ledger_path": str(path), "period": ledger.get("period"),
        "budget_micros_usd": budget, "known_cost_micros_usd": known,
        "spent_micros_usd": None if unknown else known,
        "remaining_micros_usd": None if unknown else max(0, budget - known),
        "unknown_requests": unknown, "request_count": len(records),
        "budget_exceeded": known > budget,
        "limit_semantics": "admission estimate limit; final charges may exceed estimates",
    }


def ledger_summary(path: str | Path) -> dict:
    path = Path(path).expanduser().resolve()
    with _locked(path):
        return _summary(_load(path), path)


def _run_summary(ledger: dict, path: Path, run_id: str) -> dict:
    result = _summary(ledger, path)
    records = [r for r in ledger["requests"] if r.get("run_id") == run_id]
    unknown = [r["request_id"] for r in records if r.get("cost_micros_usd") is None]
    known = sum(r["cost_micros_usd"] for r in records if r.get("cost_micros_usd") is not None)
    result.update(run_id=run_id, run_request_count=len(records),
                  run_known_cost_micros_usd=known, run_unknown_requests=unknown,
                  run_cost_micros_usd=None if unknown else known)
    return result


def run_summary(path: str | Path, run_id: str) -> dict:
    path = Path(path).expanduser().resolve()
    with _locked(path):
        return _run_summary(_load(path), path, run_id)


def _redact_auth_echo(value: str | None, headers: dict[str, str]) -> str | None:
    """Provider correlation headers are untrusted and may echo credentials."""
    if not isinstance(value, str):
        return None
    for name, header in headers.items():
        if name.lower() != "authorization" or not isinstance(header, str):
            continue
        secret = header.split(" ", 1)[-1]
        for variant in sorted({header, secret, quote_url(secret, safe=""), quote_plus(secret)}, key=len, reverse=True):
            if variant:
                value = value.replace(variant, "[redacted]")
    return value


class RunBudget:
    """Thread/process-safe budget backed by one durable ledger.

    A ledger's budget is immutable. Reusing it requires the same authorization
    or omitting budget_micros. Every quote and dispatch shares its file lock.
    """

    def __init__(self, ledger_path: str | Path, budget_micros: int | None = None,
                 *, allow_variable_cost: bool = False, period: str | None = None,
                 run_id: str | None = None):
        if budget_micros is not None and not is_micros(budget_micros):
            raise CostControlError("Budget must be nonnegative integer micro-USD")
        self.path = Path(ledger_path).expanduser().resolve()
        self.run_id = run_id or uuid.uuid4().hex
        if not isinstance(self.run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", self.run_id):
            raise CostControlError("Invalid cost run ID")
        self.allow_variable_cost = allow_variable_cost
        self._thread_lock = threading.RLock()
        self.last_refusal: str | None = None
        with self._thread_lock, _locked(self.path):
            if self.path.exists():
                ledger = _load(self.path)
                if budget_micros is not None and ledger["budget_micros_usd"] != budget_micros:
                    raise CostControlError("Budget differs from the existing ledger; its approved budget cannot be silently changed")
                if period is not None and ledger.get("period") != period:
                    raise CostControlError("Ledger period does not match the requested UTC day")
            else:
                if budget_micros is None:
                    raise CostControlError("A new cost ledger requires an explicit --budget-usd")
                ledger = {"schema_version": 1, "budget_micros_usd": budget_micros,
                          "period": period, "created_at": _now(), "requests": []}
                _save(self.path, ledger)

    def summary(self) -> dict:
        with self._thread_lock, _locked(self.path):
            ledger = _load(self.path)
            result = _run_summary(ledger, self.path, self.run_id)
        if self.last_refusal:
            result["last_refusal"] = self.last_refusal
        return result

    def _refuse(self, message: str):
        self.last_refusal = message
        raise CostControlError(message)

    def request(self, method: str, url: str, headers: dict[str, str], data: bytes | None,
                send: Callable[[dict[str, str]], Response]) -> Response:
        target = urlsplit(url)
        try:
            validate_operation(method, url)
        except CostControlError as exc:
            self._refuse(str(exc))
        with self._thread_lock, _locked(self.path):
            ledger = _load(self.path)
            state = _summary(ledger, self.path)
            if state["unknown_requests"]:
                self._refuse(f"Unresolved charge in {self.path}; reconcile before further paid requests")
            if state["budget_exceeded"]:
                self._refuse("Actual charges already exceeded the approved estimate budget")
            remaining = state["remaining_micros_usd"]
            clean_headers = {k: v for k, v in headers.items()
                             if k.lower() not in {"x-aisa-cost-mode", "x-aisa-max-price-usd", "idempotency-key"}}
            try:
                quote_response = send({**clean_headers, "X-AISA-Cost-Mode": "quote"})
                quote = validate_quote(quote_response)
            except Exception as exc:
                self._refuse(f"Cost quote failed; no paid request sent ({type(exc).__name__})")
            estimate = quote["estimated_cost_micros_usd"]
            variable = quote["may_exceed_estimate"]
            if variable and not self.allow_variable_cost:
                self._refuse("This quote may exceed its estimate; explicit --allow-variable-cost is required")
            if estimate > remaining:
                self._refuse(f"Quote {estimate} micro-USD exceeds remaining approved budget {remaining} micro-USD")

            # Caller-supplied idempotency keys are retained and never redispatched.
            request_id = next((v for k, v in headers.items() if k.lower() == "idempotency-key"), None)
            request_id = request_id or "tw-" + uuid.uuid4().hex
            if not re.fullmatch(r"[\x21-\x7e]{1,200}", request_id):
                self._refuse("Invalid idempotency key")
            if any(r["request_id"] == request_id for r in ledger["requests"]):
                self._refuse("Request already recorded; inspect its result rather than redispatching")
            record = {
                "request_id": request_id, "run_id": self.run_id, "started_at": _now(), "method": method,
                "url": target.scheme + "://" + target.netloc + target.path,
                "query_sha256": hashlib.sha256(target.query.encode()).hexdigest(),
                "body_sha256": hashlib.sha256(data or b"").hexdigest(),
                "quoted_micros_usd": estimate, "max_estimate_micros_usd": remaining,
                "may_exceed_estimate": variable, "outcome": "pending",
                "cost_micros_usd": None, "cost_status": "unknown",
            }
            ledger["requests"].append(record)
            _save(self.path, ledger)  # Must succeed before any paid dispatch.
            try:
                response = send({**clean_headers, "Idempotency-Key": request_id,
                                 "X-AISA-Max-Price-USD": usd_text(remaining)})
            except Exception as exc:
                record.update(outcome="transport_error", finished_at=_now(), error_type=type(exc).__name__)
                _save(self.path, ledger)
                raise CostControlError(f"Paid request outcome is unknown ({request_id}); reconcile {self.path} before retrying") from exc
            response.headers = {k.lower(): v for k, v in response.headers.items()}
            raw_cost = response.headers.get("x-aisa-customer-cost-micros-usd")
            charge = int(raw_cost) if isinstance(raw_cost, str) and re.fullmatch(r"[0-9]+", raw_cost) else None
            record.update(
                outcome="response_read_error" if response.read_error else "response_received",
                finished_at=_now(), http_status=response.status, cost_micros_usd=charge,
                cost_status="reported" if charge is not None else "unknown",
                estimate_exceeded=(charge > estimate) if charge is not None else None,
                budget_exceeded=(charge > remaining) if charge is not None else None,
                provider_request_id=_redact_auth_echo(response.headers.get("x-request-id"), headers),
            )
            _save(self.path, ledger)
            return response


_active_budget: RunBudget | None = None
_active_lock = threading.Lock()


@contextmanager
def activate(budget: RunBudget):
    """Activate one process-wide budget, including ThreadPoolExecutor workers."""
    global _active_budget
    with _active_lock:
        if _active_budget is not None:
            raise CostControlError("An AIsa cost context is already active in this process")
        _active_budget = budget
    try:
        yield budget
    finally:
        with _active_lock:
            _active_budget = None


def current_budget() -> RunBudget:
    if _active_budget is None:
        raise CostControlError("Paid AIsa requests require an explicit --budget-usd and --cost-ledger")
    return _active_budget


def reconcile(ledger_path: str | Path, request_id: str, charged_micros: int, evidence: str) -> dict:
    """Record externally verified, request-specific billing evidence; no network."""
    if not is_micros(charged_micros) or not evidence.strip():
        raise CostControlError("Reconciliation requires an exact nonnegative charge and request-specific evidence")
    path = Path(ledger_path).expanduser().resolve()
    with _locked(path):
        ledger = _load(path)
        record = next((r for r in ledger["requests"] if r["request_id"] == request_id), None)
        if record is None:
            raise CostControlError("Request ID does not exist in this ledger")
        record.setdefault("reconciliations", []).append({
            "at": _now(), "evidence": evidence.strip(),
            "previous_cost_micros_usd": record.get("cost_micros_usd"),
            "charged_micros_usd": charged_micros,
        })
        record.update(cost_micros_usd=charged_micros, cost_status="reconciled")
        _save(path, ledger)
        return _summary(ledger, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    show = sub.add_parser("show")
    show.add_argument("ledger")
    fix = sub.add_parser("reconcile")
    fix.add_argument("ledger")
    fix.add_argument("request_id")
    fix.add_argument("--charged-usd", type=parse_usd, required=True)
    fix.add_argument("--evidence", required=True, help="Externally verified request-specific Usage & Logs evidence")
    args = parser.parse_args()
    try:
        result = (reconcile(args.ledger, args.request_id, args.charged_usd, args.evidence)
                  if args.command == "reconcile" else ledger_summary(args.ledger))
    except CostControlError as exc:
        parser.exit(2, f"{exc}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
