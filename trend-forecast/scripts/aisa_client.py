"""
AIsa API Client for Trend Forecaster
Handles all AIsa endpoint calls with error handling and retry logic.
"""

import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
import time

AISA_BASE = "https://api.aisa.one"
AISA_API_BASE = f"{AISA_BASE}/apis/v1"
AISA_LLM_BASE = f"{AISA_BASE}/v1"


def get_api_key():
    """Get AISA_API_KEY from environment."""
    key = os.environ.get("AISA_API_KEY")
    if not key:
        print("ERROR: AISA_API_KEY not set.", file=sys.stderr)
        print("Get your key at https://aisa.one", file=sys.stderr)
        sys.exit(1)
    return key


def _request(url, method="GET", data=None, retries=2):
    """Make an authenticated request to AIsa API."""
    api_key = get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            if e.code == 429 and attempt < retries:
                wait = 2 ** (attempt + 1)
                print(f"  Rate limited, retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  HTTP {e.code}: {error_body[:200]}", file=sys.stderr)
            return {"error": f"HTTP {e.code}", "detail": error_body[:200]}
        except urllib.error.URLError as e:
            print(f"  Network error: {e.reason}", file=sys.stderr)
            return {"error": "network", "detail": str(e.reason)}
        except Exception as e:
            print(f"  Unexpected error: {e}", file=sys.stderr)
            return {"error": "unknown", "detail": str(e)}

    return {"error": "max_retries", "detail": "Exhausted retry attempts"}


# ── LLM Gateway ──────────────────────────────────────────

def llm_chat(messages, model="gpt-4.1-mini", temperature=0.3):
    """Call AIsa's OpenAI-compatible chat completions endpoint."""
    url = f"{AISA_LLM_BASE}/chat/completions"
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2000,
    }
    result = _request(url, method="POST", data=data)

    if "error" in result:
        return result

    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return {"error": "parse", "detail": "Unexpected LLM response format"}


# ── Prediction Markets (Polymarket + Kalshi) ─────────────

def search_prediction_markets(query, limit=5):
    """Search Polymarket markets via fuzzy search.

    GET /polymarket/markets — params: search, status, market_slug, limit.
    Returns markets whose `side_a.id` / `side_b.id` token IDs feed
    get_polymarket_price(). Yes price is a decimal probability (0.65 = 65%).
    """
    params = urllib.parse.urlencode({"search": query, "status": "open", "limit": limit})
    url = f"{AISA_API_BASE}/polymarket/markets?{params}"
    print(f"  📊 Prediction markets (Polymarket): {query}", file=sys.stderr)
    return _request(url)


def get_polymarket_price(token_id, at_time=None):
    """Current (or historical) Polymarket price for a token.

    GET /polymarket/market-price/{token_id} — params: token_id, at_time.
    `token_id` comes from `side_a.id` / `side_b.id` in the markets response.
    Returns a decimal probability (0-1).
    """
    url = f"{AISA_API_BASE}/polymarket/market-price/{urllib.parse.quote(str(token_id))}"
    if at_time:
        url += "?" + urllib.parse.urlencode({"at_time": at_time})
    print(f"  📊 Polymarket price: {token_id}", file=sys.stderr)
    return _request(url)


def search_kalshi_markets(query, limit=5):
    """Search Kalshi markets via fuzzy search.

    GET /kalshi/markets — params: search, status, market_ticker.
    Returns markets whose `market_ticker` feeds get_kalshi_price().
    """
    params = urllib.parse.urlencode({"search": query, "limit": limit})
    url = f"{AISA_API_BASE}/kalshi/markets?{params}"
    print(f"  📊 Prediction markets (Kalshi): {query}", file=sys.stderr)
    return _request(url)


def get_kalshi_price(market_ticker, at_time=None):
    """Current (or historical) Kalshi yes/no price for a market.

    GET /kalshi/market-price/{market_ticker} — params: market_ticker, at_time.
    `market_ticker` comes from the markets response. Returns a decimal
    probability (0-1).
    """
    url = f"{AISA_API_BASE}/kalshi/market-price/{urllib.parse.quote(str(market_ticker))}"
    if at_time:
        url += "?" + urllib.parse.urlencode({"at_time": at_time})
    print(f"  📊 Kalshi price: {market_ticker}", file=sys.stderr)
    return _request(url)


# ── Twitter / X ──────────────────────────────────────────

def search_twitter(query, query_type="Latest"):
    """Search Twitter/X via AIsa relay.

    GET /twitter/tweet/advanced_search — params: query, queryType
    (Latest|Top), cursor.
    """
    params = urllib.parse.urlencode({"query": query, "queryType": query_type})
    url = f"{AISA_API_BASE}/twitter/tweet/advanced_search?{params}"
    print(f"  🐦 Twitter search: {query}", file=sys.stderr)
    return _request(url)


# ── News (Tavily) ────────────────────────────────────────

def search_news(query, days=7, max_results=10):
    """Search recent news via AIsa's Tavily relay."""
    url = f"{AISA_API_BASE}/tavily/search"
    data = {
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
        "topic": "news",
        "days": days,
    }
    print(f"  📰 News search: {query}", file=sys.stderr)
    return _request(url, method="POST", data=data)


# ── Stock / Market Data (MarketPulse) ────────────────────
# All endpoints live under /financial/. Prices ~$0.001/call,
# financials ~$0.002/call, macro ~$0.0005/call.

def get_stock_prices(ticker, interval="day"):
    """Historical stock prices.

    GET /financial/prices — requires interval params
    (e.g. ?ticker=AAPL&interval=day).
    """
    params = urllib.parse.urlencode({"ticker": ticker, "interval": interval})
    url = f"{AISA_API_BASE}/financial/prices?{params}"
    print(f"  💹 Stock prices: {ticker} ({interval})", file=sys.stderr)
    return _request(url)


def get_stock_news(ticker):
    """Company news by ticker.

    GET /financial/news — ?ticker=AAPL.
    """
    params = urllib.parse.urlencode({"ticker": ticker})
    url = f"{AISA_API_BASE}/financial/news?{params}"
    print(f"  📰 Stock news: {ticker}", file=sys.stderr)
    return _request(url)


def get_financial_metrics(ticker):
    """Real-time financial metrics snapshot.

    GET /financial/financial-metrics/snapshot — ?ticker=AAPL.
    """
    params = urllib.parse.urlencode({"ticker": ticker})
    url = f"{AISA_API_BASE}/financial/financial-metrics/snapshot?{params}"
    print(f"  📈 Financial metrics: {ticker}", file=sys.stderr)
    return _request(url)


def get_analyst_estimates(ticker):
    """Analyst EPS estimates.

    GET /financial/analyst-estimates — ?ticker=AAPL.
    """
    params = urllib.parse.urlencode({"ticker": ticker})
    url = f"{AISA_API_BASE}/financial/analyst-estimates?{params}"
    print(f"  🎯 Analyst estimates: {ticker}", file=sys.stderr)
    return _request(url)


def get_insider_trades(ticker):
    """Insider trades.

    GET /financial/insider-trades — ?ticker=AAPL.
    """
    params = urllib.parse.urlencode({"ticker": ticker})
    url = f"{AISA_API_BASE}/financial/insider-trades?{params}"
    print(f"  🕵️  Insider trades: {ticker}", file=sys.stderr)
    return _request(url)


def get_interest_rates():
    """Current interest rates snapshot.

    GET /financial/macro/interest-rates/snapshot.
    """
    url = f"{AISA_API_BASE}/financial/macro/interest-rates/snapshot"
    print(f"  🏦 Interest rates snapshot", file=sys.stderr)
    return _request(url)


# ── Perplexity (supplemental) ────────────────────────────

def perplexity_search(query):
    """Supplemental deep research via AIsa's Perplexity relay."""
    url = f"{AISA_API_BASE}/perplexity/search"
    data = {"query": query}
    print(f"  🔍 Perplexity: {query}", file=sys.stderr)
    return _request(url, method="POST", data=data)
