#!/usr/bin/env python3
"""
FinReport — MarketPulse API wrapper.

Fetches all financial data needed for an investment report:
prices, news, financial statements, SEC filings, insider trades,
and analyst estimates. All via the AIsa MarketPulse API.
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from typing import Any, Dict, Optional


BASE_URL = "https://api.aisa.one/apis/v1"


def _get_api_key() -> str:
    key = os.environ.get("AISA_API_KEY")
    if not key:
        raise ValueError(
            "AISA_API_KEY environment variable is not set. "
            "Add it to your shell profile or .env file."
        )
    return key


def _request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make a GET request to the MarketPulse API with 1 retry on 429/503."""
    api_key = _get_api_key()
    url = f"{BASE_URL}{endpoint}"

    if params:
        query_string = urllib.parse.urlencode(
            {k: v for k, v in params.items() if v is not None}
        )
        url = f"{url}?{query_string}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "FinReport/1.0",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            if exc.code in {429, 503} and attempt == 0:
                time.sleep(2)
                continue
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                raise RuntimeError(
                    f"MarketPulse API error {exc.code}: {error_body[:200]}"
                ) from exc
        except urllib.error.URLError as exc:
            if attempt == 0:
                time.sleep(2)
                continue
            raise RuntimeError(f"Network error: {exc.reason}") from exc

    raise RuntimeError("Request failed after retry.")


def is_crypto(ticker: str) -> bool:
    """Return True if ticker is a cryptocurrency (ends with -USD)."""
    return ticker.upper().endswith("-USD")


def get_stock_price(ticker: str) -> Dict[str, Any]:
    """Fetch 30-day daily OHLCV history for an equity ticker."""
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    return _request("/financial/prices", params={
        "ticker": ticker,
        "interval": "day",
        "interval_multiplier": 1,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
    })


def get_crypto_snapshot(ticker: str) -> Dict[str, Any]:
    """Fetch real-time price snapshot for a crypto ticker (e.g. BTC-USD)."""
    return _request("/financial/crypto/prices/snapshot", params={"ticker": ticker})


def get_news(ticker: str, limit: int = 5) -> Dict[str, Any]:
    """Fetch the latest news articles for a ticker."""
    return _request("/financial/news", params={"ticker": ticker, "limit": limit})


def get_financials(ticker: str) -> Dict[str, Any]:
    """Fetch financial metrics snapshot (P/E, revenue, margins)."""
    return _request("/financial/financial-metrics/snapshot", params={"ticker": ticker})


def get_sec_filings(ticker: str) -> Dict[str, Any]:
    """Fetch the most recent SEC filings."""
    return _request("/financial/filings", params={"ticker": ticker})


def get_insider_trades(ticker: str) -> Dict[str, Any]:
    """Fetch recent insider buy/sell activity by company executives."""
    return _request("/financial/insider-trades", params={"ticker": ticker})


def get_analyst_estimates(ticker: str) -> Dict[str, Any]:
    """Fetch analyst EPS and revenue estimates by fiscal period."""
    return _request("/financial/analyst-estimates", params={
        "ticker": ticker,
        "period": "annual",
    })
