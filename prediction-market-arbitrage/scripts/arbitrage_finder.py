#!/usr/bin/env python3

"""
OpenClaw Prediction Market Arbitrage Finder
Automated cross-platform arbitrage detection across Polymarket and Kalshi.
Powered by AIsa.

Workflow (mirrors SKILL_ARBITRAGE.md):
  1. Find matching markets across platforms
  2. Compare real-time prices to calculate spreads
  3. Verify orderbook liquidity to confirm actionability

Usage:
  python arbitrage_finder.py scan <sport> --date <YYYY-MM-DD> [--min-spread <pct>] [--min-liquidity <usd>] [--json]
  python arbitrage_finder.py match --polymarket-slug <slug> [--min-spread <pct>] [--min-liquidity <usd>] [--json]
  python arbitrage_finder.py match --kalshi-ticker <ticker> [--min-spread <pct>] [--min-liquidity <usd>] [--json]

Examples:
  python arbitrage_finder.py scan nba --date 2025-03-30
  python arbitrage_finder.py scan nba --date 2025-03-30 --min-spread 3.0 --min-liquidity 500
  python arbitrage_finder.py match --polymarket-slug nba-lakers-vs-celtics
  python arbitrage_finder.py match --kalshi-ticker KXNBA-25-LAL-BOS
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# API Client
# ──────────────────────────────────────────────────────────────────────────────

class AIsaClient:
    """Lightweight client for the AIsa prediction market API."""

    BASE_URL = "https://api.aisa.one/apis/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("AISA_API_KEY")
        if not self.api_key:
            print("Error: AISA_API_KEY is required.")
            print("Set it via:  export AISA_API_KEY=\"your-key\"")
            print("Sign up at:  https://aisa.one")
            sys.exit(1)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        if params:
            qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            if qs:
                url = f"{url}?{qs}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenClaw-ArbitrageFinder/1.0",
        }
        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"error": {"code": str(e.code), "message": body}}
        except urllib.error.URLError as e:
            return {"error": {"code": "NETWORK_ERROR", "message": str(e.reason)}}

    def _get_multi(self, path: str, params_list: List[Tuple[str, str]]) -> Dict[str, Any]:
        """GET with repeated query params (e.g. multiple slugs/tickers)."""
        qs = "&".join(f"{urllib.parse.quote(k)}={urllib.parse.quote(v)}" for k, v in params_list)
        url = f"{self.BASE_URL}{path}?{qs}" if qs else f"{self.BASE_URL}{path}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenClaw-ArbitrageFinder/1.0",
        }
        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"error": {"code": str(e.code), "message": body}}
        except urllib.error.URLError as e:
            return {"error": {"code": "NETWORK_ERROR", "message": str(e.reason)}}

    # ── Step 1: Find matching markets ────────────────────────────────────────

    def matching_sports_by_date(self, sport: str, date: str) -> Dict[str, Any]:
        """Find matching sports markets across platforms for a given date."""
        return self._get(f"/matching-markets/sports/{sport}", {"date": date})

    def matching_sports_by_slug(self, slugs: List[str]) -> Dict[str, Any]:
        """Find matching markets using Polymarket slug(s)."""
        params = [("polymarket_market_slug", s) for s in slugs]
        return self._get_multi("/matching-markets/sports", params)

    def matching_sports_by_ticker(self, tickers: List[str]) -> Dict[str, Any]:
        """Find matching markets using Kalshi event ticker(s)."""
        params = [("kalshi_event_ticker", t) for t in tickers]
        return self._get_multi("/matching-markets/sports", params)

    # ── Step 2: Compare prices ───────────────────────────────────────────────

    def polymarket_price(self, token_id: str) -> Dict[str, Any]:
        """Get current price for a Polymarket token (from side_a.id or side_b.id)."""
        return self._get(f"/polymarket/market-price/{token_id}")

    def kalshi_price(self, market_ticker: str) -> Dict[str, Any]:
        """Get current price for a Kalshi market (from market_ticker)."""
        return self._get(f"/kalshi/market-price/{market_ticker}")

    # ── Step 3: Verify liquidity ─────────────────────────────────────────────

    def polymarket_orderbook(self, token_id: str) -> Dict[str, Any]:
        """Get latest orderbook snapshot for a Polymarket token."""
        return self._get("/polymarket/orderbooks", {"token_id": token_id})

    def kalshi_orderbook(self, ticker: str) -> Dict[str, Any]:
        """Get latest orderbook snapshot for a Kalshi market."""
        return self._get("/kalshi/orderbooks", {"ticker": ticker})


# ──────────────────────────────────────────────────────────────────────────────
# Arbitrage Analysis
# ──────────────────────────────────────────────────────────────────────────────

def extract_polymarket_price(price_resp: Dict[str, Any]) -> Optional[float]:
    """Extract the Yes price from a Polymarket market-price response."""
    if "error" in price_resp:
        return None
    price = price_resp.get("price")
    if price is not None:
        return float(price)
    # Some responses nest under a data key
    data = price_resp.get("data", {})
    if isinstance(data, dict):
        p = data.get("price") or data.get("mid") or data.get("last")
        if p is not None:
            return float(p)
    return None


def extract_kalshi_price(price_resp: Dict[str, Any]) -> Optional[float]:
    """Extract the Yes price from a Kalshi market-price response.
    Kalshi prices are in cents (0-100), so we normalize to 0-1."""
    if "error" in price_resp:
        return None
    # Try direct fields
    for key in ("yes_price", "price", "last_price", "yes_ask"):
        val = price_resp.get(key)
        if val is not None:
            v = float(val)
            return v / 100.0 if v > 1.0 else v
    data = price_resp.get("data", {})
    if isinstance(data, dict):
        for key in ("yes_price", "price", "last_price", "yes_ask"):
            val = data.get(key)
            if val is not None:
                v = float(val)
                return v / 100.0 if v > 1.0 else v
    return None


def compute_orderbook_liquidity(ob_resp: Dict[str, Any]) -> Optional[float]:
    """Estimate total USD liquidity from an orderbook response.
    Sums the top-of-book bid and ask sizes as a rough liquidity measure."""
    if "error" in ob_resp:
        return None

    total = 0.0

    # Handle various response shapes
    orderbook = ob_resp
    if "data" in ob_resp and isinstance(ob_resp["data"], dict):
        orderbook = ob_resp["data"]
    if "orderbook" in orderbook and isinstance(orderbook["orderbook"], dict):
        orderbook = orderbook["orderbook"]

    for side_key in ("bids", "asks"):
        levels = orderbook.get(side_key, [])
        if isinstance(levels, list):
            for level in levels:
                if isinstance(level, dict):
                    size = float(level.get("size", 0) or level.get("quantity", 0) or 0)
                    price = float(level.get("price", 0) or 0)
                    total += size * price if price <= 1.0 else size * (price / 100.0)
                elif isinstance(level, (list, tuple)) and len(level) >= 2:
                    price, size = float(level[0]), float(level[1])
                    total += size * price if price <= 1.0 else size * (price / 100.0)

    return total if total > 0 else None


def calculate_spread(poly_yes: float, kalshi_yes: float) -> Dict[str, Any]:
    """Calculate arbitrage spread between two platforms.

    An arbitrage exists when you can buy 'Yes' on one platform and 'No' on
    the other for a combined cost below 1.0.

    Returns details for the best arbitrage direction."""

    # Direction A: Buy Yes on Polymarket + Buy No on Kalshi
    cost_a = poly_yes + (1.0 - kalshi_yes)
    profit_a = 1.0 - cost_a

    # Direction B: Buy Yes on Kalshi + Buy No on Polymarket
    cost_b = kalshi_yes + (1.0 - poly_yes)
    profit_b = 1.0 - cost_b

    if profit_a >= profit_b:
        return {
            "spread_pct": round(profit_a * 100, 2),
            "profit_per_dollar": round(profit_a, 4),
            "direction": "Buy YES on Polymarket + Buy NO on Kalshi",
            "buy_yes_platform": "Polymarket",
            "buy_yes_price": round(poly_yes, 4),
            "buy_no_platform": "Kalshi",
            "buy_no_price": round(1.0 - kalshi_yes, 4),
            "total_cost": round(cost_a, 4),
        }
    else:
        return {
            "spread_pct": round(profit_b * 100, 2),
            "profit_per_dollar": round(profit_b, 4),
            "direction": "Buy YES on Kalshi + Buy NO on Polymarket",
            "buy_yes_platform": "Kalshi",
            "buy_yes_price": round(kalshi_yes, 4),
            "buy_no_platform": "Polymarket",
            "buy_no_price": round(1.0 - poly_yes, 4),
            "total_cost": round(cost_b, 4),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Matching-Market Parsers
# ──────────────────────────────────────────────────────────────────────────────

def parse_matched_pairs(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract matched market pairs from the /matching-markets response.
    Adapts to multiple possible response shapes."""

    pairs = []

    # Try top-level list
    items = resp if isinstance(resp, list) else resp.get("data", resp.get("matches", resp.get("markets", [])))
    if isinstance(items, dict):
        items = items.get("data", items.get("matches", items.get("markets", [])))
    if not isinstance(items, list):
        items = [items] if isinstance(items, dict) else []

    for item in items:
        if not isinstance(item, dict):
            continue

        pair: Dict[str, Any] = {"title": item.get("title", "Unknown Event")}

        # Polymarket side
        poly = item.get("polymarket", item.get("polymarket_market", {}))
        if isinstance(poly, dict):
            pair["polymarket"] = {
                "market_slug": poly.get("market_slug", ""),
                "token_id_yes": poly.get("side_a", {}).get("id", "") if isinstance(poly.get("side_a"), dict) else "",
                "token_id_no": poly.get("side_b", {}).get("id", "") if isinstance(poly.get("side_b"), dict) else "",
                "condition_id": poly.get("condition_id", ""),
            }
        elif isinstance(poly, list) and poly:
            p = poly[0]
            pair["polymarket"] = {
                "market_slug": p.get("market_slug", ""),
                "token_id_yes": p.get("side_a", {}).get("id", "") if isinstance(p.get("side_a"), dict) else "",
                "token_id_no": p.get("side_b", {}).get("id", "") if isinstance(p.get("side_b"), dict) else "",
                "condition_id": p.get("condition_id", ""),
            }

        # Kalshi side
        kal = item.get("kalshi", item.get("kalshi_market", {}))
        if isinstance(kal, dict):
            pair["kalshi"] = {
                "market_ticker": kal.get("market_ticker", ""),
                "event_ticker": kal.get("event_ticker", ""),
            }
        elif isinstance(kal, list) and kal:
            k = kal[0]
            pair["kalshi"] = {
                "market_ticker": k.get("market_ticker", ""),
                "event_ticker": k.get("event_ticker", ""),
            }

        if "polymarket" in pair and "kalshi" in pair:
            pairs.append(pair)

    return pairs


# ──────────────────────────────────────────────────────────────────────────────
# Core Scan Logic
# ──────────────────────────────────────────────────────────────────────────────

def analyze_pair(
    client: AIsaClient,
    pair: Dict[str, Any],
    min_spread: float,
    min_liquidity: float,
) -> Optional[Dict[str, Any]]:
    """Run the full arbitrage workflow on a single matched pair."""

    title = pair.get("title", "Unknown")
    poly = pair.get("polymarket", {})
    kal = pair.get("kalshi", {})

    token_id = poly.get("token_id_yes", "")
    market_ticker = kal.get("market_ticker", "")

    if not token_id or not market_ticker:
        return None

    # Step 2: Compare prices
    poly_resp = client.polymarket_price(token_id)
    kal_resp = client.kalshi_price(market_ticker)

    poly_yes = extract_polymarket_price(poly_resp)
    kal_yes = extract_kalshi_price(kal_resp)

    if poly_yes is None or kal_yes is None:
        return None

    spread = calculate_spread(poly_yes, kal_yes)

    if spread["spread_pct"] < min_spread:
        return None

    # Step 3: Verify liquidity
    poly_ob = client.polymarket_orderbook(token_id)
    kal_ob = client.kalshi_orderbook(market_ticker)

    poly_liq = compute_orderbook_liquidity(poly_ob)
    kal_liq = compute_orderbook_liquidity(kal_ob)

    effective_liq = min(poly_liq or 0, kal_liq or 0)

    result = {
        "title": title,
        "polymarket_slug": poly.get("market_slug", ""),
        "kalshi_ticker": market_ticker,
        "polymarket_yes_price": poly_yes,
        "kalshi_yes_price": kal_yes,
        **spread,
        "polymarket_liquidity_usd": round(poly_liq, 2) if poly_liq else None,
        "kalshi_liquidity_usd": round(kal_liq, 2) if kal_liq else None,
        "effective_liquidity_usd": round(effective_liq, 2),
    }

    if min_liquidity > 0 and effective_liq < min_liquidity:
        result["actionable"] = False
        result["reason"] = f"Insufficient liquidity (${effective_liq:.2f} < ${min_liquidity:.2f})"
    else:
        result["actionable"] = spread["spread_pct"] > 0
        if not result["actionable"]:
            result["reason"] = "No positive spread"

    return result


def run_scan(
    client: AIsaClient,
    sport: str,
    date: str,
    min_spread: float,
    min_liquidity: float,
) -> List[Dict[str, Any]]:
    """Scan all matching markets for a sport on a given date."""

    print(f"\n{'='*70}")
    print(f"  Arbitrage Scan: {sport.upper()} on {date}")
    print(f"  Filters: min spread >= {min_spread}%  |  min liquidity >= ${min_liquidity:.0f}")
    print(f"{'='*70}\n")

    # Step 1: Find matching markets
    print("[1/3] Finding matching markets across Polymarket and Kalshi...")
    resp = client.matching_sports_by_date(sport, date)

    if "error" in resp:
        print(f"  Error: {resp['error']}")
        return []

    pairs = parse_matched_pairs(resp)
    print(f"  Found {len(pairs)} matched market pair(s).\n")

    if not pairs:
        return []

    # Steps 2 & 3: Compare prices and verify liquidity for each pair
    results = []
    for i, pair in enumerate(pairs, 1):
        title = pair.get("title", "Unknown")
        print(f"[2/3] Analyzing pair {i}/{len(pairs)}: {title}")

        result = analyze_pair(client, pair, min_spread, min_liquidity)
        if result:
            results.append(result)
            _print_opportunity(result)
        else:
            print(f"  -> Skipped (no price data or spread below {min_spread}%)\n")

    return results


def run_match(
    client: AIsaClient,
    polymarket_slug: Optional[str],
    kalshi_ticker: Optional[str],
    min_spread: float,
    min_liquidity: float,
) -> List[Dict[str, Any]]:
    """Analyze a specific matched market by slug or ticker."""

    print(f"\n{'='*70}")
    print(f"  Arbitrage Match Analysis")
    if polymarket_slug:
        print(f"  Polymarket slug: {polymarket_slug}")
    if kalshi_ticker:
        print(f"  Kalshi ticker:   {kalshi_ticker}")
    print(f"  Filters: min spread >= {min_spread}%  |  min liquidity >= ${min_liquidity:.0f}")
    print(f"{'='*70}\n")

    # Step 1: Find matching markets
    print("[1/3] Finding matching markets...")
    if polymarket_slug:
        resp = client.matching_sports_by_slug([polymarket_slug])
    else:
        resp = client.matching_sports_by_ticker([kalshi_ticker])

    if "error" in resp:
        print(f"  Error: {resp['error']}")
        return []

    pairs = parse_matched_pairs(resp)
    print(f"  Found {len(pairs)} matched market pair(s).\n")

    if not pairs:
        return []

    results = []
    for i, pair in enumerate(pairs, 1):
        title = pair.get("title", "Unknown")
        print(f"[2/3] Analyzing pair {i}/{len(pairs)}: {title}")

        result = analyze_pair(client, pair, min_spread, min_liquidity)
        if result:
            results.append(result)
            _print_opportunity(result)
        else:
            print(f"  -> Skipped (no price data or spread below {min_spread}%)\n")

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Display
# ──────────────────────────────────────────────────────────────────────────────

def _print_opportunity(r: Dict[str, Any]) -> None:
    """Pretty-print a single arbitrage opportunity."""
    actionable = r.get("actionable", False)
    tag = "ACTIONABLE" if actionable else "NOT ACTIONABLE"
    marker = ">>>" if actionable else "   "

    print(f"\n  {marker} [{tag}] {r['title']}")
    print(f"      Polymarket YES: {r['polymarket_yes_price']:.4f}  |  Kalshi YES: {r['kalshi_yes_price']:.4f}")
    print(f"      Spread:         {r['spread_pct']:+.2f}%  ({r['direction']})")
    print(f"      Total cost:     {r['total_cost']:.4f}  |  Profit/dollar: {r['profit_per_dollar']:.4f}")

    poly_liq = r.get("polymarket_liquidity_usd")
    kal_liq = r.get("kalshi_liquidity_usd")
    eff_liq = r.get("effective_liquidity_usd", 0)
    print(f"      Liquidity:      Polymarket ${poly_liq or 'N/A'}  |  Kalshi ${kal_liq or 'N/A'}  |  Effective ${eff_liq}")

    if not actionable and "reason" in r:
        print(f"      Reason:         {r['reason']}")
    print()


def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print a summary table of all results."""
    if not results:
        print("\nNo arbitrage opportunities found matching your criteria.\n")
        return

    actionable = [r for r in results if r.get("actionable")]
    print(f"\n{'='*70}")
    print(f"  SUMMARY: {len(results)} opportunity(ies) analyzed, {len(actionable)} actionable")
    print(f"{'='*70}")

    if actionable:
        print(f"\n  {'Event':<35} {'Spread':>8} {'Liquidity':>12} {'Direction'}")
        print(f"  {'-'*35} {'-'*8} {'-'*12} {'-'*40}")
        for r in sorted(actionable, key=lambda x: x["spread_pct"], reverse=True):
            title = r["title"][:33] + ".." if len(r["title"]) > 35 else r["title"]
            spread = f"{r['spread_pct']:+.2f}%"
            liq = f"${r.get('effective_liquidity_usd', 0):,.0f}"
            direction = r["direction"]
            print(f"  {title:<35} {spread:>8} {liq:>12} {direction}")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw Prediction Market Arbitrage Finder - Detect cross-platform price discrepancies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scan nba --date 2025-03-30
  %(prog)s scan nba --date 2025-03-30 --min-spread 3.0 --min-liquidity 500
  %(prog)s match --polymarket-slug nba-lakers-vs-celtics
  %(prog)s match --kalshi-ticker KXNBA-25-LAL-BOS
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # scan
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan all matching markets for a sport on a given date",
    )
    scan_parser.add_argument(
        "sport",
        choices=["nba", "nfl", "mlb", "nhl", "soccer", "tennis"],
        help="Sport to scan",
    )
    scan_parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    scan_parser.add_argument("--min-spread", type=float, default=0.0, help="Minimum spread %% to report (default: 0)")
    scan_parser.add_argument("--min-liquidity", type=float, default=0.0, help="Minimum effective liquidity in USD (default: 0)")
    scan_parser.add_argument("--json", action="store_true", help="Output results as JSON")

    # match
    match_parser = subparsers.add_parser(
        "match",
        help="Analyze a specific market by Polymarket slug or Kalshi ticker",
    )
    match_group = match_parser.add_mutually_exclusive_group(required=True)
    match_group.add_argument("--polymarket-slug", help="Polymarket market slug")
    match_group.add_argument("--kalshi-ticker", help="Kalshi event ticker")
    match_parser.add_argument("--min-spread", type=float, default=0.0, help="Minimum spread %% to report (default: 0)")
    match_parser.add_argument("--min-liquidity", type=float, default=0.0, help="Minimum effective liquidity in USD (default: 0)")
    match_parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = AIsaClient()

    if args.command == "scan":
        results = run_scan(client, args.sport, args.date, args.min_spread, args.min_liquidity)
    elif args.command == "match":
        results = run_match(client, args.polymarket_slug, args.kalshi_ticker, args.min_spread, args.min_liquidity)
    else:
        parser.print_help()
        sys.exit(1)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print_summary(results)

    sys.exit(0 if results else 1)


if __name__ == "__main__":
    main()
