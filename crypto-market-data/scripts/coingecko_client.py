#!/usr/bin/env python3
"""
AIsa CoinGecko - AIsa API Client
Complete cryptocurrency market data for autonomous agents.

Usage:
    # Simple
    python coingecko_client.py simple price --ids <ids> --vs <currencies> [flags]
    python coingecko_client.py simple supported-currencies
    python coingecko_client.py simple token-price --platform <id> --addresses <csv> --vs <currencies> [flags]

    # Coins
    python coingecko_client.py coins list [--include-platform]
    python coingecko_client.py coins markets --vs <currency> [--ids <csv>] [--category <id>] [--order <order>] [--per-page <n>] [--page <n>] [--sparkline] [--price-change <csv>]
    python coingecko_client.py coins data --id <coin-id> [--no-localization] [--no-tickers] [--no-market-data] [--no-community-data] [--no-developer-data] [--sparkline]
    python coingecko_client.py coins tickers --id <coin-id> [--exchange-ids <csv>] [--page <n>] [--order <order>] [--depth]
    python coingecko_client.py coins history --id <coin-id> --date <dd-mm-yyyy> [--no-localization]
    python coingecko_client.py coins chart --id <coin-id> --vs <currency> --days <n|max> [--interval <daily>]
    python coingecko_client.py coins chart-range --id <coin-id> --vs <currency> --from <unix> --to <unix>
    python coingecko_client.py coins ohlc --id <coin-id> --vs <currency> --days <1|7|14|30|90|180|365>
    python coingecko_client.py coins contract --platform <id> --address <0x...> [--no-localization] [--no-tickers] [--no-market-data] [--no-community-data] [--no-developer-data] [--sparkline]
    python coingecko_client.py coins contract-chart --platform <id> --address <0x...> --vs <currency> --days <n|max>

    # Categories
    python coingecko_client.py categories list
    python coingecko_client.py categories markets [--order <order>]

    # Exchanges
    python coingecko_client.py exchanges list [--per-page <n>] [--page <n>]
    python coingecko_client.py exchanges id-map
    python coingecko_client.py exchanges data --id <exchange-id>
    python coingecko_client.py exchanges tickers --id <exchange-id> [--coin-ids <csv>] [--page <n>] [--order <order>] [--depth]

    # Other
    python coingecko_client.py news
    python coingecko_client.py trending

Environment:
    AISA_API_KEY    Required. Get one at https://aisa.one
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


class CoinGeckoClient:
    """AIsa CoinGecko - Unified Cryptocurrency Data API Client."""

    BASE_URL = "https://api.aisa.one/apis/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("AISA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "AISA_API_KEY is required. Set it via environment variable or pass to constructor."
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        if params:
            cleaned = {k: _fmt(v) for k, v in params.items() if v is not None}
            if cleaned:
                url = f"{url}?{urllib.parse.urlencode(cleaned)}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "AIsa-CoinGecko/1.0",
        }

        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"success": False, "error": {"code": str(e.code), "message": body}}
        except urllib.error.URLError as e:
            return {"success": False, "error": {"code": "NETWORK_ERROR", "message": str(e.reason)}}

    # ==================== Simple ====================

    def simple_price(
        self,
        ids: str,
        vs_currencies: str,
        include_market_cap: Optional[bool] = None,
        include_24hr_vol: Optional[bool] = None,
        include_24hr_change: Optional[bool] = None,
        include_last_updated_at: Optional[bool] = None,
        precision: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._request("GET", "/coingecko/simple/price", params={
            "ids": ids,
            "vs_currencies": vs_currencies,
            "include_market_cap": include_market_cap,
            "include_24hr_vol": include_24hr_vol,
            "include_24hr_change": include_24hr_change,
            "include_last_updated_at": include_last_updated_at,
            "precision": precision,
        })

    def simple_supported_currencies(self) -> Dict[str, Any]:
        return self._request("GET", "/coingecko/simple/supported_vs_currencies")

    def simple_token_price(
        self,
        platform_id: str,
        contract_addresses: str,
        vs_currencies: str,
        include_market_cap: Optional[bool] = None,
        include_24hr_vol: Optional[bool] = None,
        include_24hr_change: Optional[bool] = None,
        include_last_updated_at: Optional[bool] = None,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/coingecko/simple/token_price/{urllib.parse.quote(platform_id, safe='')}",
            params={
                "contract_addresses": contract_addresses,
                "vs_currencies": vs_currencies,
                "include_market_cap": include_market_cap,
                "include_24hr_vol": include_24hr_vol,
                "include_24hr_change": include_24hr_change,
                "include_last_updated_at": include_last_updated_at,
            },
        )

    # ==================== Coins ====================

    def coins_list(self, include_platform: Optional[bool] = None) -> Dict[str, Any]:
        return self._request("GET", "/coingecko/coins/list", params={
            "include_platform": include_platform,
        })

    def coins_markets(
        self,
        vs_currency: str,
        ids: Optional[str] = None,
        category: Optional[str] = None,
        order: Optional[str] = None,
        per_page: Optional[int] = None,
        page: Optional[int] = None,
        sparkline: Optional[bool] = None,
        price_change_percentage: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._request("GET", "/coingecko/coins/markets", params={
            "vs_currency": vs_currency,
            "ids": ids,
            "category": category,
            "order": order,
            "per_page": per_page,
            "page": page,
            "sparkline": sparkline,
            "price_change_percentage": price_change_percentage,
        })

    def coin_data(
        self,
        coin_id: str,
        localization: Optional[bool] = None,
        tickers: Optional[bool] = None,
        market_data: Optional[bool] = None,
        community_data: Optional[bool] = None,
        developer_data: Optional[bool] = None,
        sparkline: Optional[bool] = None,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/coingecko/coins/{urllib.parse.quote(coin_id, safe='')}",
            params={
                "localization": localization,
                "tickers": tickers,
                "market_data": market_data,
                "community_data": community_data,
                "developer_data": developer_data,
                "sparkline": sparkline,
            },
        )

    def coin_tickers(
        self,
        coin_id: str,
        exchange_ids: Optional[str] = None,
        page: Optional[int] = None,
        order: Optional[str] = None,
        depth: Optional[bool] = None,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/coingecko/coins/{urllib.parse.quote(coin_id, safe='')}/tickers",
            params={
                "exchange_ids": exchange_ids,
                "page": page,
                "order": order,
                "depth": depth,
            },
        )

    def coin_history(
        self,
        coin_id: str,
        date: str,
        localization: Optional[bool] = None,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/coingecko/coins/{urllib.parse.quote(coin_id, safe='')}/history",
            params={"date": date, "localization": localization},
        )

    def coin_market_chart(
        self,
        coin_id: str,
        vs_currency: str,
        days: str,
        interval: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/coingecko/coins/{urllib.parse.quote(coin_id, safe='')}/market_chart",
            params={"vs_currency": vs_currency, "days": days, "interval": interval},
        )

    def coin_market_chart_range(
        self,
        coin_id: str,
        vs_currency: str,
        from_ts: int,
        to_ts: int,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/coingecko/coins/{urllib.parse.quote(coin_id, safe='')}/market_chart/range",
            params={"vs_currency": vs_currency, "from": from_ts, "to": to_ts},
        )

    def coin_ohlc(
        self,
        coin_id: str,
        vs_currency: str,
        days: str,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/coingecko/coins/{urllib.parse.quote(coin_id, safe='')}/ohlc",
            params={"vs_currency": vs_currency, "days": days},
        )

    def coin_by_contract(
        self,
        platform_id: str,
        address: str,
        localization: Optional[bool] = None,
        tickers: Optional[bool] = None,
        market_data: Optional[bool] = None,
        community_data: Optional[bool] = None,
        developer_data: Optional[bool] = None,
        sparkline: Optional[bool] = None,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/coingecko/coins/{urllib.parse.quote(platform_id, safe='')}/contract/{urllib.parse.quote(address, safe='')}",
            params={
                "localization": localization,
                "tickers": tickers,
                "market_data": market_data,
                "community_data": community_data,
                "developer_data": developer_data,
                "sparkline": sparkline,
            },
        )

    def coin_contract_market_chart(
        self,
        platform_id: str,
        address: str,
        vs_currency: str,
        days: str,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/coingecko/coins/{urllib.parse.quote(platform_id, safe='')}/contract/{urllib.parse.quote(address, safe='')}/market_chart",
            params={"vs_currency": vs_currency, "days": days},
        )

    # ==================== Categories ====================

    def categories_list(self) -> Dict[str, Any]:
        return self._request("GET", "/coingecko/coins/categories/list")

    def categories_markets(self, order: Optional[str] = None) -> Dict[str, Any]:
        return self._request("GET", "/coingecko/coins/categories", params={"order": order})

    # ==================== Exchanges ====================

    def exchanges_list(
        self,
        per_page: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Dict[str, Any]:
        return self._request("GET", "/coingecko/exchanges", params={
            "per_page": per_page,
            "page": page,
        })

    def exchanges_id_map(self) -> Dict[str, Any]:
        return self._request("GET", "/coingecko/exchanges/list")

    def exchange_data(self, exchange_id: str) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/coingecko/exchanges/{urllib.parse.quote(exchange_id, safe='')}",
        )

    def exchange_tickers(
        self,
        exchange_id: str,
        coin_ids: Optional[str] = None,
        page: Optional[int] = None,
        depth: Optional[bool] = None,
        order: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/coingecko/exchanges/{urllib.parse.quote(exchange_id, safe='')}/tickers",
            params={
                "coin_ids": coin_ids,
                "page": page,
                "depth": depth,
                "order": order,
            },
        )

    # ==================== Other ====================

    def news(self) -> Dict[str, Any]:
        return self._request("GET", "/coingecko/news")

    def trending(self) -> Dict[str, Any]:
        return self._request("GET", "/coingecko/search/trending")


def _fmt(v: Any) -> Any:
    if isinstance(v, bool):
        return "true" if v else "false"
    return v


def _print(result: Dict[str, Any]) -> None:
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="coingecko_client.py",
        description="AIsa CoinGecko - Complete cryptocurrency market data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s simple price --ids bitcoin,ethereum --vs usd,eur --include-24hr-change
    %(prog)s coins markets --vs usd --per-page 25 --order market_cap_desc
    %(prog)s coins data --id bitcoin --no-tickers
    %(prog)s coins chart --id bitcoin --vs usd --days 30
    %(prog)s coins ohlc --id bitcoin --vs usd --days 7
    %(prog)s simple token-price --platform ethereum --addresses 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 --vs usd
    %(prog)s exchanges data --id binance
    %(prog)s trending
        """,
    )
    sub = parser.add_subparsers(dest="group", required=True)

    # simple
    g_simple = sub.add_parser("simple", help="Simple price endpoints").add_subparsers(dest="action", required=True)

    p = g_simple.add_parser("price", help="Current price for coins")
    p.add_argument("--ids", required=True, help="Comma-separated CoinGecko IDs (e.g. bitcoin,ethereum)")
    p.add_argument("--vs", dest="vs_currencies", required=True, help="Comma-separated target currencies (e.g. usd,eur)")
    p.add_argument("--include-market-cap", action="store_true")
    p.add_argument("--include-24hr-vol", action="store_true")
    p.add_argument("--include-24hr-change", action="store_true")
    p.add_argument("--include-last-updated-at", action="store_true")
    p.add_argument("--precision", help="Decimal precision, e.g. '2' or 'full'")

    g_simple.add_parser("supported-currencies", help="List supported fiat/crypto currencies")

    p = g_simple.add_parser("token-price", help="Current price by contract address")
    p.add_argument("--platform", dest="platform_id", required=True, help="Asset platform (e.g. ethereum, binance-smart-chain, polygon-pos)")
    p.add_argument("--addresses", dest="contract_addresses", required=True, help="Comma-separated contract addresses")
    p.add_argument("--vs", dest="vs_currencies", required=True, help="Comma-separated target currencies")
    p.add_argument("--include-market-cap", action="store_true")
    p.add_argument("--include-24hr-vol", action="store_true")
    p.add_argument("--include-24hr-change", action="store_true")
    p.add_argument("--include-last-updated-at", action="store_true")

    # coins
    g_coins = sub.add_parser("coins", help="Coin data, markets, and history").add_subparsers(dest="action", required=True)

    p = g_coins.add_parser("list", help="All coins with id/symbol/name")
    p.add_argument("--include-platform", action="store_true")

    p = g_coins.add_parser("markets", help="All coins with full market data")
    p.add_argument("--vs", dest="vs_currency", required=True)
    p.add_argument("--ids", help="Comma-separated coin IDs to filter")
    p.add_argument("--category", help="Filter by category id")
    p.add_argument("--order", help="e.g. market_cap_desc, volume_desc")
    p.add_argument("--per-page", type=int)
    p.add_argument("--page", type=int)
    p.add_argument("--sparkline", action="store_true")
    p.add_argument("--price-change", dest="price_change_percentage", help="Comma-separated windows, e.g. 1h,24h,7d")

    p = g_coins.add_parser("data", help="Full coin data by ID")
    p.add_argument("--id", dest="coin_id", required=True)
    p.add_argument("--no-localization", dest="localization", action="store_false", default=None)
    p.add_argument("--no-tickers", dest="tickers", action="store_false", default=None)
    p.add_argument("--no-market-data", dest="market_data", action="store_false", default=None)
    p.add_argument("--no-community-data", dest="community_data", action="store_false", default=None)
    p.add_argument("--no-developer-data", dest="developer_data", action="store_false", default=None)
    p.add_argument("--sparkline", action="store_true", default=None)

    p = g_coins.add_parser("tickers", help="Exchange-listed trading pairs for a coin")
    p.add_argument("--id", dest="coin_id", required=True)
    p.add_argument("--exchange-ids", help="Comma-separated exchange IDs")
    p.add_argument("--page", type=int)
    p.add_argument("--order", help="e.g. trust_score_desc, volume_desc")
    p.add_argument("--depth", action="store_true", default=None)

    p = g_coins.add_parser("history", help="Historical snapshot on a given date")
    p.add_argument("--id", dest="coin_id", required=True)
    p.add_argument("--date", required=True, help="Date in dd-mm-yyyy format")
    p.add_argument("--no-localization", dest="localization", action="store_false", default=None)

    p = g_coins.add_parser("chart", help="Historical market data over the last N days")
    p.add_argument("--id", dest="coin_id", required=True)
    p.add_argument("--vs", dest="vs_currency", required=True)
    p.add_argument("--days", required=True, help="Number of days, or 'max'")
    p.add_argument("--interval", help="e.g. daily")

    p = g_coins.add_parser("chart-range", help="Historical market data within a UNIX timestamp range")
    p.add_argument("--id", dest="coin_id", required=True)
    p.add_argument("--vs", dest="vs_currency", required=True)
    p.add_argument("--from", dest="from_ts", type=int, required=True, help="UNIX timestamp (seconds)")
    p.add_argument("--to", dest="to_ts", type=int, required=True, help="UNIX timestamp (seconds)")

    p = g_coins.add_parser("ohlc", help="OHLC candles for a coin")
    p.add_argument("--id", dest="coin_id", required=True)
    p.add_argument("--vs", dest="vs_currency", required=True)
    p.add_argument("--days", required=True, help="1, 7, 14, 30, 90, 180, 365")

    p = g_coins.add_parser("contract", help="Full coin data by contract address")
    p.add_argument("--platform", dest="platform_id", required=True)
    p.add_argument("--address", required=True)
    p.add_argument("--no-localization", dest="localization", action="store_false", default=None)
    p.add_argument("--no-tickers", dest="tickers", action="store_false", default=None)
    p.add_argument("--no-market-data", dest="market_data", action="store_false", default=None)
    p.add_argument("--no-community-data", dest="community_data", action="store_false", default=None)
    p.add_argument("--no-developer-data", dest="developer_data", action="store_false", default=None)
    p.add_argument("--sparkline", action="store_true", default=None)

    p = g_coins.add_parser("contract-chart", help="Historical chart by contract address")
    p.add_argument("--platform", dest="platform_id", required=True)
    p.add_argument("--address", required=True)
    p.add_argument("--vs", dest="vs_currency", required=True)
    p.add_argument("--days", required=True)

    # categories
    g_cat = sub.add_parser("categories", help="Coin categories").add_subparsers(dest="action", required=True)
    g_cat.add_parser("list", help="All category IDs and names")
    p = g_cat.add_parser("markets", help="All categories with market cap, volume, and top-3 coins")
    p.add_argument("--order", help="e.g. market_cap_desc, volume_desc")

    # exchanges
    g_ex = sub.add_parser("exchanges", help="Exchanges and tickers").add_subparsers(dest="action", required=True)

    p = g_ex.add_parser("list", help="Exchanges with current volume and metadata")
    p.add_argument("--per-page", type=int)
    p.add_argument("--page", type=int)

    g_ex.add_parser("id-map", help="All exchange IDs and names (map names -> IDs)")

    p = g_ex.add_parser("data", help="Detailed data for one exchange")
    p.add_argument("--id", dest="exchange_id", required=True)

    p = g_ex.add_parser("tickers", help="Trading pairs on an exchange")
    p.add_argument("--id", dest="exchange_id", required=True)
    p.add_argument("--coin-ids", help="Comma-separated coin IDs")
    p.add_argument("--page", type=int)
    p.add_argument("--order", help="e.g. trust_score_desc, volume_desc")
    p.add_argument("--depth", action="store_true", default=None)

    # standalone
    sub.add_parser("news", help="Latest crypto news from CoinGecko")
    sub.add_parser("trending", help="Top-7 trending coin searches in last 24h")

    args = parser.parse_args()

    try:
        client = CoinGeckoClient()
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    # dispatch
    group = args.group
    action = getattr(args, "action", None)

    if group == "simple":
        if action == "price":
            _print(client.simple_price(
                ids=args.ids,
                vs_currencies=args.vs_currencies,
                include_market_cap=args.include_market_cap or None,
                include_24hr_vol=args.include_24hr_vol or None,
                include_24hr_change=args.include_24hr_change or None,
                include_last_updated_at=args.include_last_updated_at or None,
                precision=args.precision,
            ))
        elif action == "supported-currencies":
            _print(client.simple_supported_currencies())
        elif action == "token-price":
            _print(client.simple_token_price(
                platform_id=args.platform_id,
                contract_addresses=args.contract_addresses,
                vs_currencies=args.vs_currencies,
                include_market_cap=args.include_market_cap or None,
                include_24hr_vol=args.include_24hr_vol or None,
                include_24hr_change=args.include_24hr_change or None,
                include_last_updated_at=args.include_last_updated_at or None,
            ))

    elif group == "coins":
        if action == "list":
            _print(client.coins_list(include_platform=args.include_platform or None))
        elif action == "markets":
            _print(client.coins_markets(
                vs_currency=args.vs_currency,
                ids=args.ids,
                category=args.category,
                order=args.order,
                per_page=args.per_page,
                page=args.page,
                sparkline=args.sparkline or None,
                price_change_percentage=args.price_change_percentage,
            ))
        elif action == "data":
            _print(client.coin_data(
                coin_id=args.coin_id,
                localization=args.localization,
                tickers=args.tickers,
                market_data=args.market_data,
                community_data=args.community_data,
                developer_data=args.developer_data,
                sparkline=args.sparkline,
            ))
        elif action == "tickers":
            _print(client.coin_tickers(
                coin_id=args.coin_id,
                exchange_ids=args.exchange_ids,
                page=args.page,
                order=args.order,
                depth=args.depth,
            ))
        elif action == "history":
            _print(client.coin_history(
                coin_id=args.coin_id,
                date=args.date,
                localization=args.localization,
            ))
        elif action == "chart":
            _print(client.coin_market_chart(
                coin_id=args.coin_id,
                vs_currency=args.vs_currency,
                days=args.days,
                interval=args.interval,
            ))
        elif action == "chart-range":
            _print(client.coin_market_chart_range(
                coin_id=args.coin_id,
                vs_currency=args.vs_currency,
                from_ts=args.from_ts,
                to_ts=args.to_ts,
            ))
        elif action == "ohlc":
            _print(client.coin_ohlc(
                coin_id=args.coin_id,
                vs_currency=args.vs_currency,
                days=args.days,
            ))
        elif action == "contract":
            _print(client.coin_by_contract(
                platform_id=args.platform_id,
                address=args.address,
                localization=args.localization,
                tickers=args.tickers,
                market_data=args.market_data,
                community_data=args.community_data,
                developer_data=args.developer_data,
                sparkline=args.sparkline,
            ))
        elif action == "contract-chart":
            _print(client.coin_contract_market_chart(
                platform_id=args.platform_id,
                address=args.address,
                vs_currency=args.vs_currency,
                days=args.days,
            ))

    elif group == "categories":
        if action == "list":
            _print(client.categories_list())
        elif action == "markets":
            _print(client.categories_markets(order=args.order))

    elif group == "exchanges":
        if action == "list":
            _print(client.exchanges_list(per_page=args.per_page, page=args.page))
        elif action == "id-map":
            _print(client.exchanges_id_map())
        elif action == "data":
            _print(client.exchange_data(exchange_id=args.exchange_id))
        elif action == "tickers":
            _print(client.exchange_tickers(
                exchange_id=args.exchange_id,
                coin_ids=args.coin_ids,
                page=args.page,
                depth=args.depth,
                order=args.order,
            ))

    elif group == "news":
        _print(client.news())
    elif group == "trending":
        _print(client.trending())


if __name__ == "__main__":
    main()
