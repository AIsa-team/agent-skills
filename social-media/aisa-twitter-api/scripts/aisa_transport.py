"""One-shot AIsa transport with verified quotes and durable request accounting."""

from __future__ import annotations

import argparse
import http.client
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid

import costs


def add_cost_arguments(parser: argparse.ArgumentParser) -> None:
    """Add to each command parser; suppressed defaults also permit parent flags."""
    parser.add_argument("--budget-usd", dest="budget_micros", type=costs.parse_usd,
                        default=argparse.SUPPRESS,
                        help="Approved admission-estimate budget in USD; final charges may exceed estimates")
    parser.add_argument("--cost-ledger", default=argparse.SUPPRESS,
                        help="Durable task ledger; reuse to retain earlier charges")
    parser.add_argument("--allow-variable-cost", action="store_true", default=argparse.SUPPRESS,
                        help="Accept quotes whose final charge may exceed their estimate")
    parser.add_argument("--quote", action="store_true", default=argparse.SUPPRESS,
                        help="Validate a free quote only; do not execute or create a ledger")


def budget_from_args(args: argparse.Namespace) -> costs.RunBudget | None:
    if getattr(args, "quote", False) or getattr(args, "dry_run", False):
        return None
    amount = getattr(args, "budget_micros", None)
    path = getattr(args, "cost_ledger", None)
    if amount is None and not path:
        raise costs.CostControlError("Paid AIsa requests require --budget-usd or an existing --cost-ledger")
    path = path or Path.home() / ".local" / "state" / "aisa-twitter-api" / "costs" / (uuid.uuid4().hex + ".json")
    return costs.RunBudget(path, amount, allow_variable_cost=getattr(args, "allow_variable_cost", False))


_SECRET_FIELDS = frozenset({"aisa_api_key", "api_key", "apikey", "authorization",
                            "access_token", "refresh_token", "client_secret", "password",
                            "accesstoken", "refreshtoken", "clientsecret", "token", "secret", "bearer_token"})


def sanitize(value, api_key: str):
    """Redact nested credential fields and raw/encoded echoes of the API key."""
    if isinstance(value, dict):
        return {
            sanitize(str(key), api_key): (
                "[redacted]" if str(key).lower().replace("-", "_") in _SECRET_FIELDS
                else sanitize(item, api_key)
            ) for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize(item, api_key) for item in value]
    if isinstance(value, str):
        if api_key:
            variants = {api_key, urllib.parse.quote(api_key, safe=""), urllib.parse.quote_plus(api_key),
                        json.dumps(api_key, ensure_ascii=True)[1:-1]}
            for secret in sorted(variants, key=len, reverse=True):
                value = value.replace(secret, "[redacted]")
        return re.sub(r"(?i)\bBearer\s+[^\s\"'<>]+", "Bearer [redacted]", value)
    return value


def is_failure(result) -> bool:
    if not isinstance(result, dict):
        return True
    if result.get("success") is False or result.get("ok") is False:
        return True
    if result.get("error") or result.get("errors"):
        return True
    status = result.get("status")
    if isinstance(status, str) and status.lower() in {"error", "failed", "failure"}:
        return True
    for field in ("status", "status_code", "statusCode", "code"):
        value = result.get(field)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 400:
            return True
    return False


def _invalid_json_constant(value):
    raise ValueError("Non-finite numbers are not valid JSON")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open_request(req, timeout):
    return urllib.request.build_opener(_NoRedirect()).open(req, timeout=timeout)


def _send_once(method, url, headers, data, timeout) -> costs.Response:
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        response = _open_request(req, timeout)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        status = response.status
        response_headers = dict(response.headers.items())
        try:
            return costs.Response(status, response_headers, response.read())
        except (OSError, http.client.HTTPException) as exc:
            partial = getattr(exc, "partial", b"")
            return costs.Response(status, response_headers, partial if isinstance(partial, bytes) else b"",
                                  read_error=type(exc).__name__)


def _metadata(budget, status=None, *, quote_only=False):
    result = {"http_status": status, "quote_only": quote_only}
    if budget is not None:
        try:
            result["costs"] = budget.summary()
        except Exception:
            result["costs"] = {"status": "unavailable", "ledger_path": str(budget.path),
                               "warning": "Inspect the durable ledger before further paid requests"}
    else:
        result["costs"] = {"ledger_path": None, "request_count": 0, "known_cost_micros_usd": 0,
                           "unknown_requests": []}
    return result


def request(method: str, url: str, api_key: str, *, json_data=None, data: bytes | None = None,
            headers: dict | None = None, timeout=60, budget: costs.RunBudget | None = None,
            quote_only=False) -> dict:
    """Quote and execute identical bytes once, or only quote, on verified routes.

    Provider objects remain intact on success except the reserved ``_aisa`` key
    and credential redaction. All failures have ``success: false`` and ``ok: false``.
    """
    response = None

    def failure(code, message, provider=None):
        result = {"success": False, "ok": False, "error": {"code": code, "message": message},
                  "_aisa": _metadata(budget, response.status if response else None, quote_only=quote_only)}
        if provider is not None:
            result["provider_response"] = provider
        return sanitize(result, api_key)

    try:
        costs.validate_operation(method, url)
        if not isinstance(api_key, str) or not api_key.strip():
            return failure("AUTH_ERROR", "AISA_API_KEY is required")
        if data is not None and json_data is not None:
            return failure("INPUT_ERROR", "Pass json_data or raw data, not both")
        if data is not None and not isinstance(data, bytes):
            return failure("INPUT_ERROR", "Raw request data must be bytes")
        payload = json.dumps(json_data, allow_nan=False).encode("utf-8") if json_data is not None else data
        request_headers = {key: value for key, value in (headers or {}).items()
                           if key.lower() not in {"authorization", "x-aisa-cost-mode", "x-aisa-max-price-usd"}}
        request_headers["Authorization"] = f"Bearer {api_key}"
        request_headers.setdefault("Accept", "application/json")
        if json_data is not None and not any(key.lower() == "content-type" for key in request_headers):
            request_headers["Content-Type"] = "application/json"
        send = lambda dispatch_headers: _send_once(method.upper(), url, dispatch_headers, payload, timeout)
        if quote_only:
            quote_headers = {key: value for key, value in request_headers.items() if key.lower() != "idempotency-key"}
            response = send({**quote_headers, "X-AISA-Cost-Mode": "quote"})
            quote = costs.validate_quote(response)
            return sanitize({**quote, "_aisa": _metadata(None, response.status, quote_only=True)}, api_key)
        if budget is None:
            return failure("COST_CONTROL", "Paid AIsa requests require an approved budget and durable ledger")
        response = budget.request(method.upper(), url, request_headers, payload, send)
        if response.read_error:
            return failure("RESPONSE_READ_ERROR", "Response could not be fully read; inspect cost accounting before retrying")
        try:
            provider = json.loads(response.body.decode("utf-8"), parse_constant=_invalid_json_constant)
        except (UnicodeError, ValueError):
            return failure("INVALID_RESPONSE", "Provider returned invalid JSON or UTF-8")
        if not isinstance(provider, dict):
            return failure("INVALID_RESPONSE", "Provider response must be a JSON object")
        if not 200 <= response.status < 300:
            return failure("HTTP_ERROR", f"HTTP {response.status}; inspect cost accounting before retrying", provider)
        if is_failure(provider):
            return failure("PROVIDER_ERROR", "Provider reported an error; inspect cost accounting before retrying", provider)
        return sanitize({**provider, "_aisa": _metadata(budget, response.status)}, api_key)
    except costs.CostControlError as exc:
        return failure("COST_CONTROL", str(exc))
    except (TypeError, ValueError) as exc:
        return failure("INPUT_ERROR", f"Invalid request ({type(exc).__name__})")
    except Exception as exc:
        # Provider exception strings may echo credentials or binary upload bodies.
        return failure("NETWORK_ERROR", f"Request failed ({type(exc).__name__}); inspect cost accounting before retrying")
