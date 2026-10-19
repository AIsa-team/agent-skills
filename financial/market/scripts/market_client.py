#!/usr/bin/env python3
"""
AIsa Market - AIsa API Client
Complete market data for autonomous agents: Stocks + Crypto.

Usage:
    # Stock commands
    python market_client.py stock prices --ticker <ticker> --start <date> --end <date> [--interval day|week|month] [--multiplier 1]
    python market_client.py stock news --ticker <ticker> [--count <n>]
    python market_client.py stock statements --ticker <ticker> --type <all|income|balance|cash> [--period annual|quarterly|ttm]
    python market_client.py stock metrics --ticker <ticker> [--historical] [--period annual|quarterly|ttm]
    python market_client.py stock analyst --ticker <ticker>
    python market_client.py stock insider --ticker <ticker>
    python market_client.py stock ownership --ticker <ticker>
    python market_client.py stock filings --ticker <ticker>
    python market_client.py stock facts --ticker <ticker>
    python market_client.py stock rates [--bank <bank>] [--historical]
    python market_client.py stock screen --filter <field>:<gt|lt|gte|lte|eq>:<value> [--filter ...] [--limit <n>]
    
    # Crypto commands
    python market_client.py crypto snapshot --ticker <BTC-USD>
    python market_client.py crypto historical --ticker <BTC-USD> --start <date> --end <date> [--interval day]
    python market_client.py crypto portfolio --tickers <BTC-USD,ETH-USD,SOL-USD>
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class MarketClient:
    """AIsa Market - Unified Market Data API Client."""
    
    BASE_URL = "https://api.aisa.one/apis/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with an API key."""
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
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the AIsa API."""
        url = f"{self.BASE_URL}{endpoint}"
        
        if params:
            query_string = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None}
            )
            url = f"{url}?{query_string}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AIsa-Market/1.0"
        }
        
        request_data = None
        if data:
            request_data = json.dumps(data).encode("utf-8")
        
        if method == "POST" and request_data is None:
            request_data = b"{}"
        
        req = urllib.request.Request(url, data=request_data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                return {"success": False, "error": {"code": str(e.code), "message": error_body}}
        except urllib.error.URLError as e:
            return {"success": False, "error": {"code": "NETWORK_ERROR", "message": str(e.reason)}}
    
    # ==================== Stock APIs ====================
    
    def stock_prices(
        self, 
        ticker: str, 
        start_date: str, 
        end_date: str,
        interval: str = "day",
        interval_multiplier: int = 1
    ) -> Dict[str, Any]:
        """
        Get historical stock prices.
        
        Args:
            ticker: Stock symbol (e.g., AAPL)
            start_date: Start date (YYYY-MM-DD) - required
            end_date: End date (YYYY-MM-DD) - required
            interval: second, minute, day, week, month, year (default: day)
            interval_multiplier: Multiplier for interval (default: 1)
        """
        return self._request("GET", "/financial/prices", params={
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
            "interval_multiplier": interval_multiplier
        })
    
    def company_news(self, ticker: str, limit: int = 10) -> Dict[str, Any]:
        """Get company news by ticker."""
        return self._request("GET", "/financial/news", params={
            "ticker": ticker,
            "limit": limit
        })
    
    def statements_all(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get all financial statements (period is required by the contract)."""
        return self._request("GET", "/financial/financials", params={"ticker": ticker, "period": period})

    def statements_income(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get income statements."""
        return self._request("GET", "/financial/financials/income-statements", params={"ticker": ticker, "period": period})

    def statements_balance(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get balance sheets."""
        return self._request("GET", "/financial/financials/balance-sheets", params={"ticker": ticker, "period": period})

    def statements_cash(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get cash flow statements."""
        return self._request("GET", "/financial/financials/cash-flow-statements", params={"ticker": ticker, "period": period})
    
    def metrics_snapshot(self, ticker: str) -> Dict[str, Any]:
        """Get real-time financial metrics snapshot."""
        return self._request("GET", "/financial/financial-metrics/snapshot", params={"ticker": ticker})
    
    def metrics_historical(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get historical financial metrics (period is required by the contract)."""
        return self._request("GET", "/financial/financial-metrics", params={"ticker": ticker, "period": period})
    
    def analyst_eps(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get earnings per share estimates."""
        return self._request("GET", "/financial/analyst-estimates", params={
            "ticker": ticker,
            "period": period
        })
    
    def insider_trades(self, ticker: str) -> Dict[str, Any]:
        """Get insider trades."""
        return self._request("GET", "/financial/insider-trades", params={"ticker": ticker})
    
    def institutional_ownership(self, ticker: str) -> Dict[str, Any]:
        """Get institutional ownership.

        Not in the published OpenAPI contract (https://aisa.one/openapi.json);
        this request may return 404.
        """
        return self._request("GET", "/financial/institutional/ownership", params={"ticker": ticker})
    
    def sec_filings(self, ticker: str) -> Dict[str, Any]:
        """Get SEC filings."""
        return self._request("GET", "/financial/filings", params={"ticker": ticker})
    
    def sec_items(self, ticker: str, filing_type: str, year: int) -> Dict[str, Any]:
        """Get SEC filing items (filing_type and year are required by the contract)."""
        return self._request("GET", "/financial/filings/items", params={
            "ticker": ticker,
            "filing_type": filing_type,
            "year": year,
        })
    
    def company_facts(self, ticker: str) -> Dict[str, Any]:
        """Get company facts."""
        return self._request("GET", "/financial/company/facts", params={"ticker": ticker})
    
    def rates_snapshot(self) -> Dict[str, Any]:
        """Get current interest rates."""
        return self._request("GET", "/financial/macro/interest-rates/snapshot")
    
    def rates_historical(self, bank: str = "fed") -> Dict[str, Any]:
        """Get historical interest rates."""
        return self._request("GET", "/financial/macro/interest-rates", params={"bank": bank})
    
    def screen_stocks(self, filters: List[Dict[str, Any]], limit: int = 10) -> Dict[str, Any]:
        """Screen for stocks matching criteria.

        filters: [{"field": <statement line item>, "operator": gt|lt|gte|lte|eq|in, "value": ...}]
        """
        return self._request(
            "POST",
            "/financial/financials/search/screener",
            data={"filters": filters, "limit": limit},
        )
    
    # ==================== Crypto APIs ====================
    
    def crypto_snapshot(self, ticker: str) -> Dict[str, Any]:
        """
        Get real-time price snapshot for a cryptocurrency.

        Not in the published OpenAPI contract (https://aisa.one/openapi.json);
        this request may return 404. Prefer the crypto-market-data skill.
        
        Args:
            ticker: Crypto ticker in format SYMBOL-USD (e.g., BTC-USD, ETH-USD)
        """
        return self._request("GET", "/financial/crypto/prices/snapshot", params={"ticker": ticker})
    
    def crypto_historical(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "day",
        interval_multiplier: int = 1
    ) -> Dict[str, Any]:
        """
        Get historical price data for a cryptocurrency.

        Not in the published OpenAPI contract (https://aisa.one/openapi.json);
        this request may return 404. Prefer the crypto-market-data skill.
                
        Args:
            ticker: Crypto ticker in format SYMBOL-USD (e.g., BTC-USD)
            start_date: Start date (YYYY-MM-DD) - required
            end_date: End date (YYYY-MM-DD) - required
            interval: second, minute, day, week, month, year (default: day)
            interval_multiplier: Multiplier for interval (default: 1)
        """
        return self._request("GET", "/financial/crypto/prices", params={
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
            "interval_multiplier": interval_multiplier
        })
    
    def crypto_portfolio(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Get prices for multiple cryptocurrencies.
        
        Args:
            tickers: List of crypto tickers in format SYMBOL-USD
        """
        results = {}
        for ticker in tickers:
            results[ticker] = self.crypto_snapshot(ticker)
        return {"portfolio": results}


def _normalize_crypto_ticker(symbol: str) -> str:
    """Convert simple symbol to ticker format (BTC -> BTC-USD)."""
    symbol = symbol.upper().strip()
    if not symbol.endswith("-USD"):
        return f"{symbol}-USD"
    return symbol


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AIsa Market - Complete market data (Stocks + Crypto)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s stock prices --ticker AAPL --start 2025-01-01 --end 2025-01-31
    %(prog)s stock prices --ticker AAPL --start 2025-01-01 --end 2025-01-31 --interval week
    %(prog)s stock news --ticker AAPL --count 5
    %(prog)s crypto snapshot --ticker BTC-USD
    %(prog)s crypto snapshot --ticker BTC  # Auto-converts to BTC-USD
    %(prog)s crypto historical --ticker ETH-USD --start 2025-01-01 --end 2025-01-15
        """
    )
    
    subparsers = parser.add_subparsers(dest="asset_type", help="Asset type")
    
    # ==================== Stock Commands ====================
    stock_parser = subparsers.add_parser("stock", help="Stock/Finance commands")
    stock_sub = stock_parser.add_subparsers(dest="command", help="Command")
    
    # prices
    prices = stock_sub.add_parser("prices", help="Get stock prices")
    prices.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    prices.add_argument("--start", "-s", required=True, help="Start date (YYYY-MM-DD)")
    prices.add_argument("--end", "-e", required=True, help="End date (YYYY-MM-DD)")
    prices.add_argument("--interval", "-i", default="day", 
                       choices=["second", "minute", "day", "week", "month", "year"],
                       help="Time interval (default: day)")
    prices.add_argument("--multiplier", "-m", type=int, default=1, 
                       help="Interval multiplier (default: 1)")
    
    # news
    news = stock_sub.add_parser("news", help="Get company news")
    news.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    news.add_argument("--count", "-c", type=int, default=10, help="Number of articles")
    
    # statements
    statements = stock_sub.add_parser("statements", help="Get financial statements")
    statements.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    statements.add_argument("--type", required=True, choices=["all", "income", "balance", "cash"], help="Statement type")
    statements.add_argument("--period", "-p", choices=["annual", "quarterly", "ttm"], default="annual", help="Reporting period (default: annual)")
    
    # metrics
    metrics = stock_sub.add_parser("metrics", help="Get financial metrics")
    metrics.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    metrics.add_argument("--historical", action="store_true", help="Get historical data")
    metrics.add_argument("--period", "-p", choices=["annual", "quarterly", "ttm"], default="annual", help="Reporting period for --historical (default: annual)")
    
    # analyst
    analyst = stock_sub.add_parser("analyst", help="Get analyst estimates")
    analyst.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    analyst.add_argument("--period", "-p", choices=["annual", "quarterly"], default="annual")
    
    # insider
    insider = stock_sub.add_parser("insider", help="Get insider trades")
    insider.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    
    # ownership
    ownership = stock_sub.add_parser("ownership", help="Get institutional ownership")
    ownership.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    
    # filings
    filings = stock_sub.add_parser("filings", help="Get SEC filings")
    filings.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    
    # facts
    facts = stock_sub.add_parser("facts", help="Get company facts")
    facts.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    
    # rates
    rates = stock_sub.add_parser("rates", help="Get interest rates")
    rates.add_argument("--bank", "-b", default="fed", help="Central bank (e.g., fed)")
    rates.add_argument("--historical", action="store_true", help="Get historical data")
    
    # screen
    screen = stock_sub.add_parser("screen", help="Stock screener (statement line-item filters)")
    screen.add_argument("--filter", "-f", action="append", default=[], metavar="FIELD:OP:VALUE",
                        help="Filter on a statement line item, e.g. revenue:gt:1000000000 (OP: gt|lt|gte|lte|eq); repeatable")
    screen.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    screen.add_argument("--pe-max", type=float, help=argparse.SUPPRESS)
    screen.add_argument("--pe-min", type=float, help=argparse.SUPPRESS)
    screen.add_argument("--growth-min", type=float, help=argparse.SUPPRESS)
    screen.add_argument("--growth-max", type=float, help=argparse.SUPPRESS)
    
    # ==================== Crypto Commands ====================
    crypto_parser = subparsers.add_parser("crypto", help="Cryptocurrency commands")
    crypto_sub = crypto_parser.add_subparsers(dest="command", help="Command")
    
    # snapshot
    snapshot = crypto_sub.add_parser("snapshot", help="Get real-time price")
    snapshot.add_argument("--ticker", "-t", required=True, 
                         help="Crypto ticker (e.g., BTC-USD or BTC)")
    
    # historical
    historical = crypto_sub.add_parser("historical", help="Get historical prices")
    historical.add_argument("--ticker", "-t", required=True, 
                           help="Crypto ticker (e.g., BTC-USD or BTC)")
    historical.add_argument("--start", "-s", required=True, help="Start date (YYYY-MM-DD)")
    historical.add_argument("--end", "-e", required=True, help="End date (YYYY-MM-DD)")
    historical.add_argument("--interval", "-i", default="day",
                           choices=["second", "minute", "day", "week", "month", "year"],
                           help="Time interval (default: day)")
    historical.add_argument("--multiplier", "-m", type=int, default=1,
                           help="Interval multiplier (default: 1)")
    
    # portfolio
    portfolio = crypto_sub.add_parser("portfolio", help="Get prices for multiple coins")
    portfolio.add_argument("--tickers", "-t", required=True, 
                          help="Tickers (comma-separated, e.g., BTC-USD,ETH-USD or BTC,ETH)")
    
    args = parser.parse_args()
    
    if not args.asset_type:
        parser.print_help()
        sys.exit(1)
    
    if not args.command:
        if args.asset_type == "stock":
            stock_parser.print_help()
        else:
            crypto_parser.print_help()
        sys.exit(1)
    
    try:
        client = MarketClient()
    except ValueError as e:
        print(json.dumps({"success": False, "error": {"code": "AUTH_ERROR", "message": str(e)}}))
        sys.exit(1)
    
    result = None
    
    # Stock commands
    if args.asset_type == "stock":
        if args.command == "prices":
            result = client.stock_prices(
                args.ticker, 
                args.start, 
                args.end,
                args.interval,
                args.multiplier
            )
        elif args.command == "news":
            result = client.company_news(args.ticker, args.count)
        elif args.command == "statements":
            if args.type == "all":
                result = client.statements_all(args.ticker, args.period)
            elif args.type == "income":
                result = client.statements_income(args.ticker, args.period)
            elif args.type == "balance":
                result = client.statements_balance(args.ticker, args.period)
            elif args.type == "cash":
                result = client.statements_cash(args.ticker, args.period)
        elif args.command == "metrics":
            if args.historical:
                result = client.metrics_historical(args.ticker, args.period)
            else:
                result = client.metrics_snapshot(args.ticker)
        elif args.command == "analyst":
            result = client.analyst_eps(args.ticker, args.period)
        elif args.command == "insider":
            result = client.insider_trades(args.ticker)
        elif args.command == "ownership":
            result = client.institutional_ownership(args.ticker)
        elif args.command == "filings":
            result = client.sec_filings(args.ticker)
        elif args.command == "facts":
            result = client.company_facts(args.ticker)
        elif args.command == "rates":
            if args.historical:
                result = client.rates_historical(args.bank)
            else:
                result = client.rates_snapshot()
        elif args.command == "screen":
            if any(v is not None for v in (args.pe_max, args.pe_min, args.growth_min, args.growth_max)):
                print(json.dumps({"success": False, "error": {
                    "code": "UNSUPPORTED_FILTER",
                    "message": "The published screener (/financial/financials/search/screener) filters statement "
                               "line items such as revenue or net_income; use --filter FIELD:OP:VALUE.",
                }}))
                sys.exit(2)
            filters = []
            for raw in args.filter:
                parts = raw.split(":", 2)
                if len(parts) != 3 or parts[1] not in {"gt", "lt", "gte", "lte", "eq"}:
                    print(json.dumps({"success": False, "error": {"code": "BAD_FILTER", "message": f"--filter must be FIELD:OP:VALUE with OP in gt|lt|gte|lte|eq, got {raw!r}"}}))
                    sys.exit(2)
                field, operator, value = parts
                try:
                    number: Any = float(value) if "." in value else int(value)
                except ValueError:
                    number = value
                filters.append({"field": field, "operator": operator, "value": number})
            if not filters:
                print(json.dumps({"success": False, "error": {"code": "BAD_FILTER", "message": "at least one --filter FIELD:OP:VALUE is required"}}))
                sys.exit(2)
            result = client.screen_stocks(filters, args.limit)
    
    # Crypto commands
    elif args.asset_type == "crypto":
        if args.command == "snapshot":
            ticker = _normalize_crypto_ticker(args.ticker)
            result = client.crypto_snapshot(ticker)
        elif args.command == "historical":
            ticker = _normalize_crypto_ticker(args.ticker)
            result = client.crypto_historical(
                ticker, 
                args.start, 
                args.end,
                args.interval,
                args.multiplier
            )
        elif args.command == "portfolio":
            tickers = [_normalize_crypto_ticker(t.strip()) for t in args.tickers.split(",")]
            result = client.crypto_portfolio(tickers)
    
    if result:
        output = json.dumps(result, indent=2, ensure_ascii=False)
        try:
            print(output)
        except UnicodeEncodeError:
            print(json.dumps(result, indent=2, ensure_ascii=True))
        sys.exit(0 if result.get("success", True) else 1)


if __name__ == "__main__":
    main()
