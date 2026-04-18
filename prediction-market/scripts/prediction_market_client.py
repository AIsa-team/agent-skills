#!/usr/bin/env python3

"""
OpenClaw Prediction Market - AIsa Dome API Client
Prediction market data from Polymarket and Kalshi for autonomous agents.

Usage:
  # Polymarket
  python prediction_market_client.py polymarket markets [--search <kw>] [--status open|closed] [--min-volume <n>] [--limit <n>]
  python prediction_market_client.py polymarket price <token_id> [--at-time <unix_ts>]
  python prediction_market_client.py polymarket activity --user <wallet> [--market-slug <slug>] [--limit <n>]
  python prediction_market_client.py polymarket orders [--market-slug <slug>] [--token-id <id>] [--user <wallet>] [--limit <n>]
  python prediction_market_client.py polymarket orderbooks --token-id <id> [--start <ms>] [--end <ms>] [--limit <n>]
  python prediction_market_client.py polymarket candlesticks <condition_id> --start <unix_ts> --end <unix_ts> [--interval 1|60|1440]
  python prediction_market_client.py polymarket positions <wallet_address> [--limit <n>]
  python prediction_market_client.py polymarket wallet (--eoa <addr> | --proxy <addr>) [--with-metrics] [--start <unix_ts>] [--end <unix_ts>]
  python prediction_market_client.py polymarket pnl <wallet_address> --granularity <day|week|month> [--start <unix_ts>] [--end <unix_ts>]

  # Kalshi
  python prediction_market_client.py kalshi markets [--search <kw>] [--status open|closed] [--min-volume <n>] [--limit <n>]
  python prediction_market_client.py kalshi price <market_ticker> [--at-time <unix_ts>]
  python prediction_market_client.py kalshi trades [--ticker <ticker>] [--start <unix_ts>] [--end <unix_ts>] [--limit <n>]
  python prediction_market_client.py kalshi orderbooks --ticker <ticker> [--start <ms>] [--end <ms>] [--limit <n>]

  # Cross-platform sports
  python prediction_market_client.py sports matching (--polymarket-slug <slug> | --kalshi-ticker <ticker>)
  python prediction_market_client.py sports by-date <sport> --date <YYYY-MM-DD>
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Dict, List, Optional


class DomeClient:
    """OpenClaw Prediction Market - AIsa Dome API Client."""

    BASE_URL = "https://api.aisa.one/apis/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("AISA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "AISA_API_KEY is required. Set it via environment variable or pass to constructor."
            )

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"

        if params:
            query_string = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None}
            )
            url = f"{url}?{query_string}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenClaw-PredictionMarket/1.0",
        }

        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                parsed = json.loads(error_body)
            except json.JSONDecodeError:
                parsed = {"success": False, "error": {"code": str(e.code), "message": error_body}}
            return self._check_insufficient_quota(e.code, error_body, parsed)
        except urllib.error.URLError as e:
            return {"success": False, "error": {"code": "NETWORK_ERROR", "message": str(e.reason)}}

    @staticmethod
    def _check_insufficient_quota(status_code: int, raw_body: str, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Detect 403 pre-deduction failures and add deposit instructions."""
        if status_code == 403 and "Pre-deduction failed" in raw_body:
            parsed["action_required"] = "DEPOSIT_FUNDS"
            parsed["instructions"] = (
                "Insufficient AIsa API quota. Deposit more USDC into the Circle Gateway contract "
                "to continue making requests.\n\n"
                "Run the following commands:\n"
                "  1. Check current balance:\n"
                "     node x402-payment/scripts/setup.mjs balance\n"
                "  2. If the wallet's USDC balance on Arc testnet is below 5 USDC, claim more from the faucet:\n"
                "     https://faucet.circle.com/\n"
                "  3. Deposit USDC (e.g. 5 USDC):\n"
                "     node x402-payment/scripts/setup.mjs deposit --amount 5\n\n"
                "If the Gateway has not been approved yet, run:\n"
                "     node x402-payment/scripts/setup.mjs approve\n"
                "     node x402-payment/scripts/setup.mjs deposit --amount 5\n\n"
                "After depositing, retry the failed request."
            )
        return parsed

    # ==================== Polymarket ====================

    def polymarket_markets(
        self,
        search: Optional[str] = None,
        market_slug: Optional[List[str]] = None,
        event_slug: Optional[List[str]] = None,
        condition_id: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        min_volume: Optional[float] = None,
        limit: int = 10,
        offset: int = 0,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Search/filter Polymarket markets."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        if min_volume is not None:
            params["min_volume"] = min_volume
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        url = f"{self.BASE_URL}/polymarket/markets"
        parts = []
        for k, v in params.items():
            if v is not None:
                parts.append(f"{urllib.parse.quote(str(k))}={urllib.parse.quote(str(v))}")
        for slug in (market_slug or []):
            parts.append(f"market_slug={urllib.parse.quote(slug)}")
        for slug in (event_slug or []):
            parts.append(f"event_slug={urllib.parse.quote(slug)}")
        for cid in (condition_id or []):
            parts.append(f"condition_id={urllib.parse.quote(cid)}")
        for tag in (tags or []):
            parts.append(f"tags={urllib.parse.quote(tag)}")
        if parts:
            url = f"{url}?{'&'.join(parts)}"
        return self._raw_get(url)

    def polymarket_price(self, token_id: str, at_time: Optional[int] = None) -> Dict[str, Any]:
        """Get current (or historical) price for a Polymarket token."""
        return self._request(f"/polymarket/market-price/{token_id}", params={"at_time": at_time})

    def polymarket_activity(self, user: str, market_slug: Optional[str] = None,
                            condition_id: Optional[str] = None, start_time: Optional[int] = None,
                            end_time: Optional[int] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get activity for a Polymarket wallet address."""
        return self._request("/polymarket/activity", params={
            "user": user, "market_slug": market_slug, "condition_id": condition_id,
            "start_time": start_time, "end_time": end_time, "limit": limit, "offset": offset,
        })

    def polymarket_orders(self, market_slug: Optional[str] = None, condition_id: Optional[str] = None,
                          token_id: Optional[str] = None, user: Optional[str] = None,
                          start_time: Optional[int] = None, end_time: Optional[int] = None,
                          limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get Polymarket trade history."""
        return self._request("/polymarket/orders", params={
            "market_slug": market_slug, "condition_id": condition_id, "token_id": token_id,
            "user": user, "start_time": start_time, "end_time": end_time, "limit": limit, "offset": offset,
        })

    def polymarket_orderbooks(self, token_id: str, start_time: Optional[int] = None,
                              end_time: Optional[int] = None, limit: int = 100,
                              pagination_key: Optional[str] = None) -> Dict[str, Any]:
        """Get Polymarket orderbook snapshots for a token."""
        return self._request("/polymarket/orderbooks", params={
            "token_id": token_id, "start_time": start_time, "end_time": end_time,
            "limit": limit, "pagination_key": pagination_key,
        })

    def polymarket_candlesticks(self, condition_id: str, start_time: int,
                                end_time: int, interval: int = 1) -> Dict[str, Any]:
        """Get Polymarket candlestick data. interval: 1=1m, 60=1h, 1440=1d."""
        return self._request(f"/polymarket/candlesticks/{condition_id}", params={
            "start_time": start_time, "end_time": end_time, "interval": interval,
        })

    def polymarket_positions(self, wallet_address: str, limit: int = 100,
                             pagination_key: Optional[str] = None) -> Dict[str, Any]:
        """Get Polymarket positions for a proxy wallet."""
        return self._request(f"/polymarket/positions/wallet/{wallet_address}", params={
            "limit": limit, "pagination_key": pagination_key,
        })

    def polymarket_wallet(self, eoa: Optional[str] = None, proxy: Optional[str] = None,
                          with_metrics: bool = False, start_time: Optional[int] = None,
                          end_time: Optional[int] = None) -> Dict[str, Any]:
        """Get Polymarket wallet info. Provide either eoa or proxy."""
        return self._request("/polymarket/wallet", params={
            "eoa": eoa, "proxy": proxy,
            "with_metrics": "true" if with_metrics else None,
            "start_time": start_time, "end_time": end_time,
        })

    def polymarket_pnl(self, wallet_address: str, granularity: str,
                       start_time: Optional[int] = None, end_time: Optional[int] = None) -> Dict[str, Any]:
        """Get realized P&L for a Polymarket wallet."""
        return self._request(f"/polymarket/wallet/pnl/{wallet_address}", params={
            "granularity": granularity, "start_time": start_time, "end_time": end_time,
        })

    # ==================== Kalshi ====================

    def kalshi_markets(self, search: Optional[str] = None, market_ticker: Optional[List[str]] = None,
                       event_ticker: Optional[List[str]] = None, status: Optional[str] = None,
                       min_volume: Optional[float] = None, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Search/filter Kalshi markets."""
        url = f"{self.BASE_URL}/kalshi/markets"
        parts = []
        if search:
            parts.append(f"search={urllib.parse.quote(search)}")
        if status:
            parts.append(f"status={urllib.parse.quote(status)}")
        if min_volume is not None:
            parts.append(f"min_volume={min_volume}")
        parts.append(f"limit={limit}")
        parts.append(f"offset={offset}")
        for t in (market_ticker or []):
            parts.append(f"market_ticker={urllib.parse.quote(t)}")
        for t in (event_ticker or []):
            parts.append(f"event_ticker={urllib.parse.quote(t)}")
        if parts:
            url = f"{url}?{'&'.join(parts)}"
        return self._raw_get(url)

    def kalshi_price(self, market_ticker: str, at_time: Optional[int] = None) -> Dict[str, Any]:
        """Get current (or historical) price for a Kalshi market."""
        return self._request(f"/kalshi/market-price/{market_ticker}", params={"at_time": at_time})

    def kalshi_trades(self, ticker: Optional[str] = None, start_time: Optional[int] = None,
                      end_time: Optional[int] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get Kalshi trade history."""
        return self._request("/kalshi/trades", params={
            "ticker": ticker, "start_time": start_time, "end_time": end_time,
            "limit": limit, "offset": offset,
        })

    def kalshi_orderbooks(self, ticker: str, start_time: Optional[int] = None,
                          end_time: Optional[int] = None, limit: int = 100) -> Dict[str, Any]:
        """Get Kalshi orderbook snapshots."""
        return self._request("/kalshi/orderbooks", params={
            "ticker": ticker, "start_time": start_time, "end_time": end_time, "limit": limit,
        })

    # ==================== Cross-Platform ====================

    def sports_matching(self, polymarket_slugs: Optional[List[str]] = None,
                        kalshi_tickers: Optional[List[str]] = None) -> Dict[str, Any]:
        """Find equivalent sports markets across platforms."""
        url = f"{self.BASE_URL}/matching-markets/sports"
        parts = []
        for slug in (polymarket_slugs or []):
            parts.append(f"polymarket_market_slug={urllib.parse.quote(slug)}")
        for ticker in (kalshi_tickers or []):
            parts.append(f"kalshi_event_ticker={urllib.parse.quote(ticker)}")
        if parts:
            url = f"{url}?{'&'.join(parts)}"
        return self._raw_get(url)

    def sports_by_date(self, sport: str, date: str) -> Dict[str, Any]:
        """Find sports markets by sport and date (YYYY-MM-DD)."""
        return self._request(f"/matching-markets/sports/{sport}", params={"date": date})

    def _raw_get(self, url: str) -> Dict[str, Any]:
        """Make a GET request to a fully constructed URL."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenClaw-PredictionMarket/1.0",
        }
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                parsed = json.loads(error_body)
            except json.JSONDecodeError:
                parsed = {"success": False, "error": {"code": str(e.code), "message": error_body}}
            return self._check_insufficient_quota(e.code, error_body, parsed)
        except urllib.error.URLError as e:
            return {"success": False, "error": {"code": "NETWORK_ERROR", "message": str(e.reason)}}


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw Prediction Market - Polymarket & Kalshi data via AIsa Dome API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s polymarket markets --search "election" --status open
  %(prog)s polymarket price <token_id>
  %(prog)s polymarket activity --user <wallet>
  %(prog)s polymarket orders --market-slug <slug> --limit 50
  %(prog)s polymarket orderbooks --token-id <id>
  %(prog)s polymarket candlesticks <condition_id> --start 1700000000 --end 1700086400 --interval 60
  %(prog)s polymarket positions <wallet_address>
  %(prog)s polymarket wallet --eoa <addr> --with-metrics
  %(prog)s polymarket pnl <wallet_address> --granularity day
  %(prog)s kalshi markets --search "fed rate" --status open
  %(prog)s kalshi price <market_ticker>
  %(prog)s kalshi trades --ticker <ticker>
  %(prog)s kalshi orderbooks --ticker <ticker>
  %(prog)s sports matching --polymarket-slug <slug>
  %(prog)s sports by-date nba --date 2025-03-01
"""
    )

    subparsers = parser.add_subparsers(dest="platform", help="Platform")

    # Polymarket
    pm = subparsers.add_parser("polymarket", help="Polymarket commands")
    pm_sub = pm.add_subparsers(dest="command", help="Command")

    pm_markets = pm_sub.add_parser("markets", help="Search/filter Polymarket markets")
    pm_markets.add_argument("--search")
    pm_markets.add_argument("--market-slug", nargs="+")
    pm_markets.add_argument("--event-slug", nargs="+")
    pm_markets.add_argument("--condition-id", nargs="+")
    pm_markets.add_argument("--tags", nargs="+")
    pm_markets.add_argument("--status", choices=["open", "closed"])
    pm_markets.add_argument("--min-volume", type=float)
    pm_markets.add_argument("--limit", type=int, default=10)
    pm_markets.add_argument("--offset", type=int, default=0)
    pm_markets.add_argument("--start-time", type=int)
    pm_markets.add_argument("--end-time", type=int)

    pm_price = pm_sub.add_parser("price")
    pm_price.add_argument("token_id")
    pm_price.add_argument("--at-time", type=int)

    pm_activity = pm_sub.add_parser("activity")
    pm_activity.add_argument("--user", required=True)
    pm_activity.add_argument("--market-slug")
    pm_activity.add_argument("--condition-id")
    pm_activity.add_argument("--start-time", type=int)
    pm_activity.add_argument("--end-time", type=int)
    pm_activity.add_argument("--limit", type=int, default=100)
    pm_activity.add_argument("--offset", type=int, default=0)

    pm_orders = pm_sub.add_parser("orders")
    pm_orders.add_argument("--market-slug")
    pm_orders.add_argument("--condition-id")
    pm_orders.add_argument("--token-id")
    pm_orders.add_argument("--user")
    pm_orders.add_argument("--start-time", type=int)
    pm_orders.add_argument("--end-time", type=int)
    pm_orders.add_argument("--limit", type=int, default=100)
    pm_orders.add_argument("--offset", type=int, default=0)

    pm_ob = pm_sub.add_parser("orderbooks")
    pm_ob.add_argument("--token-id", required=True)
    pm_ob.add_argument("--start", type=int, dest="start_time")
    pm_ob.add_argument("--end", type=int, dest="end_time")
    pm_ob.add_argument("--limit", type=int, default=100)
    pm_ob.add_argument("--pagination-key")

    pm_candles = pm_sub.add_parser("candlesticks")
    pm_candles.add_argument("condition_id")
    pm_candles.add_argument("--start", type=int, required=True, dest="start_time")
    pm_candles.add_argument("--end", type=int, required=True, dest="end_time")
    pm_candles.add_argument("--interval", type=int, default=1, choices=[1, 60, 1440])

    pm_pos = pm_sub.add_parser("positions")
    pm_pos.add_argument("wallet_address")
    pm_pos.add_argument("--limit", type=int, default=100)
    pm_pos.add_argument("--pagination-key")

    pm_wallet = pm_sub.add_parser("wallet")
    pm_wallet_group = pm_wallet.add_mutually_exclusive_group(required=True)
    pm_wallet_group.add_argument("--eoa")
    pm_wallet_group.add_argument("--proxy")
    pm_wallet.add_argument("--with-metrics", action="store_true")
    pm_wallet.add_argument("--start-time", type=int)
    pm_wallet.add_argument("--end-time", type=int)

    pm_pnl = pm_sub.add_parser("pnl")
    pm_pnl.add_argument("wallet_address")
    pm_pnl.add_argument("--granularity", required=True, choices=["day", "week", "month"])
    pm_pnl.add_argument("--start-time", type=int)
    pm_pnl.add_argument("--end-time", type=int)

    # Kalshi
    ks = subparsers.add_parser("kalshi", help="Kalshi commands")
    ks_sub = ks.add_subparsers(dest="command", help="Command")

    ks_markets = ks_sub.add_parser("markets")
    ks_markets.add_argument("--search")
    ks_markets.add_argument("--market-ticker", nargs="+")
    ks_markets.add_argument("--event-ticker", nargs="+")
    ks_markets.add_argument("--status", choices=["open", "closed"])
    ks_markets.add_argument("--min-volume", type=float)
    ks_markets.add_argument("--limit", type=int, default=10)
    ks_markets.add_argument("--offset", type=int, default=0)

    ks_price = ks_sub.add_parser("price")
    ks_price.add_argument("market_ticker")
    ks_price.add_argument("--at-time", type=int)

    ks_trades = ks_sub.add_parser("trades")
    ks_trades.add_argument("--ticker")
    ks_trades.add_argument("--start-time", type=int)
    ks_trades.add_argument("--end-time", type=int)
    ks_trades.add_argument("--limit", type=int, default=100)
    ks_trades.add_argument("--offset", type=int, default=0)

    ks_ob = ks_sub.add_parser("orderbooks")
    ks_ob.add_argument("--ticker", required=True)
    ks_ob.add_argument("--start", type=int, dest="start_time")
    ks_ob.add_argument("--end", type=int, dest="end_time")
    ks_ob.add_argument("--limit", type=int, default=100)

    # Sports
    sp = subparsers.add_parser("sports", help="Cross-platform sports market commands")
    sp_sub = sp.add_subparsers(dest="command", help="Command")

    sp_match = sp_sub.add_parser("matching")
    sp_match_group = sp_match.add_mutually_exclusive_group(required=True)
    sp_match_group.add_argument("--polymarket-slug", nargs="+")
    sp_match_group.add_argument("--kalshi-ticker", nargs="+")

    sp_date = sp_sub.add_parser("by-date")
    sp_date.add_argument("sport", choices=["nba", "nfl", "mlb", "nhl", "soccer", "tennis"])
    sp_date.add_argument("--date", required=True)

    args = parser.parse_args()

    if not args.platform:
        parser.print_help()
        sys.exit(1)

    if not args.command:
        if args.platform == "polymarket":
            pm.print_help()
        elif args.platform == "kalshi":
            ks.print_help()
        elif args.platform == "sports":
            sp.print_help()
        sys.exit(1)

    try:
        client = DomeClient()
    except ValueError as e:
        print(json.dumps({"success": False, "error": {"code": "AUTH_ERROR", "message": str(e)}}))
        sys.exit(1)

    result = None

    if args.platform == "polymarket":
        if args.command == "markets":
            result = client.polymarket_markets(
                search=args.search, market_slug=args.market_slug, event_slug=args.event_slug,
                condition_id=args.condition_id, tags=args.tags, status=args.status,
                min_volume=args.min_volume, limit=args.limit, offset=args.offset,
                start_time=args.start_time, end_time=args.end_time,
            )
        elif args.command == "price":
            result = client.polymarket_price(args.token_id, at_time=args.at_time)
        elif args.command == "activity":
            result = client.polymarket_activity(
                user=args.user, market_slug=args.market_slug, condition_id=args.condition_id,
                start_time=args.start_time, end_time=args.end_time, limit=args.limit, offset=args.offset,
            )
        elif args.command == "orders":
            result = client.polymarket_orders(
                market_slug=args.market_slug, condition_id=args.condition_id, token_id=args.token_id,
                user=args.user, start_time=args.start_time, end_time=args.end_time,
                limit=args.limit, offset=args.offset,
            )
        elif args.command == "orderbooks":
            result = client.polymarket_orderbooks(
                token_id=args.token_id, start_time=args.start_time, end_time=args.end_time,
                limit=args.limit, pagination_key=args.pagination_key,
            )
        elif args.command == "candlesticks":
            result = client.polymarket_candlesticks(
                condition_id=args.condition_id, start_time=args.start_time,
                end_time=args.end_time, interval=args.interval,
            )
        elif args.command == "positions":
            result = client.polymarket_positions(
                wallet_address=args.wallet_address, limit=args.limit,
                pagination_key=args.pagination_key,
            )
        elif args.command == "wallet":
            result = client.polymarket_wallet(
                eoa=args.eoa, proxy=args.proxy, with_metrics=args.with_metrics,
                start_time=args.start_time, end_time=args.end_time,
            )
        elif args.command == "pnl":
            result = client.polymarket_pnl(
                wallet_address=args.wallet_address, granularity=args.granularity,
                start_time=args.start_time, end_time=args.end_time,
            )

    elif args.platform == "kalshi":
        if args.command == "markets":
            result = client.kalshi_markets(
                search=args.search, market_ticker=args.market_ticker, event_ticker=args.event_ticker,
                status=args.status, min_volume=args.min_volume, limit=args.limit, offset=args.offset,
            )
        elif args.command == "price":
            result = client.kalshi_price(args.market_ticker, at_time=args.at_time)
        elif args.command == "trades":
            result = client.kalshi_trades(
                ticker=args.ticker, start_time=args.start_time, end_time=args.end_time,
                limit=args.limit, offset=args.offset,
            )
        elif args.command == "orderbooks":
            result = client.kalshi_orderbooks(
                ticker=args.ticker, start_time=args.start_time,
                end_time=args.end_time, limit=args.limit,
            )

    elif args.platform == "sports":
        if args.command == "matching":
            result = client.sports_matching(
                polymarket_slugs=args.polymarket_slug, kalshi_tickers=args.kalshi_ticker,
            )
        elif args.command == "by-date":
            result = client.sports_by_date(sport=args.sport, date=args.date)

    if result is not None:
        output = json.dumps(result, indent=2, ensure_ascii=False)
        try:
            print(output)
        except UnicodeEncodeError:
            print(json.dumps(result, indent=2, ensure_ascii=True))
        sys.exit(0 if result.get("success", True) else 1)


if __name__ == "__main__":
    main()
