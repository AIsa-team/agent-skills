#!/usr/bin/env python3
"""
finreport_client.py — FinReport CLI

Chains MarketPulse real-time data with Perplexity Sonar qualitative analysis
to produce a publication-quality investment research report in one session.

Usage:
  python3 finreport_client.py --ticker NVDA --name "NVIDIA Corporation" --sector "Technology"
  python3 finreport_client.py --ticker BTC-USD --name "Bitcoin" --sector "Crypto"
  python3 finreport_client.py --ticker TSLA --name "Tesla Inc." --sector "Consumer Discretionary" --out reports/tsla.md
"""

import argparse
import os
import sys
from datetime import date

# Allow sibling modules to be imported when running from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from market_fetcher import (
    get_analyst_estimates,
    get_crypto_snapshot,
    get_financials,
    get_insider_trades,
    get_news,
    get_sec_filings,
    get_stock_price,
    is_crypto,
)
from perplexity_fetcher import get_macro_context, get_market_narrative, get_risk_factors
from report_builder import build_report


def _status(msg: str) -> None:
    print(msg, flush=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FinReport — Automated investment research reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --ticker NVDA --name "NVIDIA Corporation" --sector "Technology"
  %(prog)s --ticker BTC-USD --name "Bitcoin" --sector "Crypto"
  %(prog)s --ticker TSLA --name "Tesla Inc." --sector "Consumer Discretionary" --out reports/tsla.md
        """,
    )
    parser.add_argument(
        "--ticker", "-t", required=True,
        help="Asset ticker symbol (e.g. NVDA, BTC-USD)"
    )
    parser.add_argument(
        "--name", "-n", required=True,
        help="Company or asset name (e.g. 'NVIDIA Corporation', 'Bitcoin')"
    )
    parser.add_argument(
        "--sector", "-s", required=True,
        help="Sector for macro analysis (e.g. Technology, Crypto)"
    )
    parser.add_argument(
        "--out", "-o",
        help="Output file path. Default: reports/{TICKER}_{YYYYMMDD}.md"
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    ticker = args.ticker.strip().upper()
    company_name = args.name.strip()
    sector = args.sector.strip()
    today_str = date.today().strftime("%Y%m%d")
    out_path = args.out or f"reports/{ticker}_{today_str}.md"

    # ── Phase 1: Market Data ──────────────────────────────────────────────────
    _status(f"Fetching financial data for {ticker}...")

    try:
        if is_crypto(ticker):
            market_data = {
                "price_history": get_crypto_snapshot(ticker),
                "news": get_news(ticker),
            }
        else:
            market_data = {
                "price_history": get_stock_price(ticker),
                "news": get_news(ticker),
                "financials": get_financials(ticker),
                "sec_filings": get_sec_filings(ticker),
                "insider_trades": get_insider_trades(ticker),
                "analyst_estimates": get_analyst_estimates(ticker),
            }
    except RuntimeError as exc:
        print(f"ERROR fetching market data: {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Phase 2: Perplexity Analysis ─────────────────────────────────────────
    _status("Running Perplexity analysis...")

    try:
        narrative = get_market_narrative(ticker, company_name)
        macro = get_macro_context(ticker, sector)
    except RuntimeError as exc:
        print(f"ERROR fetching Perplexity analysis: {exc}", file=sys.stderr)
        sys.exit(1)

    _status("Extracting risk factors...")

    try:
        risks = get_risk_factors(ticker, narrative)
    except RuntimeError as exc:
        print(f"WARNING: risk factor extraction failed ({exc}); using fallbacks.", file=sys.stderr)
        risks = {}

    # ── Phase 3: Assemble Report ──────────────────────────────────────────────
    _status("Assembling report...")

    report_md = build_report(ticker, market_data, narrative, macro, risks)

    # ── Phase 4: Output ───────────────────────────────────────────────────────
    print("\n" + report_md)

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(report_md)

    _status(f"Saved to {out_path}")
    _status("FinReport complete.")


if __name__ == "__main__":
    main()
