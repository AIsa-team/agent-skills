#!/usr/bin/env python3
"""
Unit tests for FinReport modules.

Uses unittest.mock.patch to mock urllib.request.urlopen — no live API calls.

Run:
    python -m pytest tests/test_finreport.py -v
    # or
    python tests/test_finreport.py
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Allow importing sibling modules from scripts/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import market_fetcher
import perplexity_fetcher
from report_builder import build_report


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_response(payload: dict) -> MagicMock:
    """Return a mock that behaves like urllib.request.urlopen context manager."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _mock_perplexity_response(content: str) -> MagicMock:
    return _mock_response({
        "choices": [{"message": {"content": content}}]
    })


# ── is_crypto ─────────────────────────────────────────────────────────────────

class TestIsCrypto(unittest.TestCase):
    def test_crypto_returns_true(self):
        self.assertTrue(market_fetcher.is_crypto("BTC-USD"))
        self.assertTrue(market_fetcher.is_crypto("ETH-USD"))
        self.assertTrue(market_fetcher.is_crypto("SOL-USD"))

    def test_case_insensitive(self):
        self.assertTrue(market_fetcher.is_crypto("btc-usd"))
        self.assertTrue(market_fetcher.is_crypto("Btc-Usd"))

    def test_equity_returns_false(self):
        self.assertFalse(market_fetcher.is_crypto("NVDA"))
        self.assertFalse(market_fetcher.is_crypto("AAPL"))
        self.assertFalse(market_fetcher.is_crypto("TSLA"))
        self.assertFalse(market_fetcher.is_crypto("BTC"))  # missing -USD suffix


# ── market_fetcher equity ─────────────────────────────────────────────────────

class TestMarketFetcherEquity(unittest.TestCase):
    ENV = {"AISA_API_KEY": "test_key"}

    @patch("market_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_get_stock_price(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            {"success": True, "data": {"results": [{"c": 800, "o": 790, "h": 810, "l": 785}]}}
        )
        result = market_fetcher.get_stock_price("NVDA")
        self.assertIsInstance(result, dict)
        mock_urlopen.assert_called_once()

    @patch("market_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_get_news(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            {"success": True, "data": {"news": [{"headline": "Test", "source": "Reuters", "date": "2024-01-01"}]}}
        )
        result = market_fetcher.get_news("NVDA", limit=5)
        self.assertIsInstance(result, dict)
        mock_urlopen.assert_called_once()

    @patch("market_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_get_financials(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            {"success": True, "data": {"snapshot": {"revenue": 44_870_000_000, "pe_ratio": 35.2}}}
        )
        result = market_fetcher.get_financials("NVDA")
        self.assertIsInstance(result, dict)

    @patch("market_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_get_sec_filings(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            {"success": True, "data": {"filings": [{"filing_type": "10-K", "filing_date": "2024-01-15"}]}}
        )
        result = market_fetcher.get_sec_filings("NVDA")
        self.assertIsInstance(result, dict)

    @patch("market_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_get_insider_trades(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            {"success": True, "data": {"insider_trades": [
                {"name": "Jensen Huang", "title": "CEO", "transaction_type": "Buy",
                 "shares": 1000, "price": 875.50, "date": "2024-01-10"}
            ]}}
        )
        result = market_fetcher.get_insider_trades("NVDA")
        self.assertIsInstance(result, dict)

    @patch("market_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_get_analyst_estimates(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            {"success": True, "data": {"analyst_estimates": [
                {"fiscal_period": "FY2025", "eps": 4.50, "revenue": 48_000_000_000}
            ]}}
        )
        result = market_fetcher.get_analyst_estimates("NVDA")
        self.assertIsInstance(result, dict)


# ── market_fetcher crypto ─────────────────────────────────────────────────────

class TestMarketFetcherCrypto(unittest.TestCase):
    @patch("market_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_get_crypto_snapshot_returns_dict(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            {"success": True, "data": {"price": 95_000.00, "ticker": "BTC-USD"}}
        )
        result = market_fetcher.get_crypto_snapshot("BTC-USD")
        self.assertIsInstance(result, dict)
        mock_urlopen.assert_called_once()

    @patch("market_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_get_crypto_snapshot_eth(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            {"success": True, "data": {"price": 3_200.00, "ticker": "ETH-USD"}}
        )
        result = market_fetcher.get_crypto_snapshot("ETH-USD")
        self.assertIsInstance(result, dict)


# ── perplexity_fetcher ────────────────────────────────────────────────────────

class TestPerplexityFetcher(unittest.TestCase):
    @patch("perplexity_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_get_market_narrative_returns_string(self, mock_urlopen):
        mock_urlopen.return_value = _mock_perplexity_response(
            "## NVIDIA Analysis\n\nNVIDIA dominates the AI chip market with 80% share."
        )
        result = perplexity_fetcher.get_market_narrative("NVDA", "NVIDIA Corporation")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("perplexity_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_get_macro_context_returns_string(self, mock_urlopen):
        mock_urlopen.return_value = _mock_perplexity_response(
            "The technology sector faces headwinds from rising interest rates."
        )
        result = perplexity_fetcher.get_macro_context("NVDA", "Technology")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("perplexity_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_narrative_uses_sonar_pro_endpoint(self, mock_urlopen):
        mock_urlopen.return_value = _mock_perplexity_response("Analysis here.")
        perplexity_fetcher.get_market_narrative("AAPL", "Apple Inc.")
        call_args = mock_urlopen.call_args
        request_obj = call_args[0][0]
        self.assertIn("sonar-pro", request_obj.full_url)

    @patch("perplexity_fetcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"AISA_API_KEY": "test_key"})
    def test_macro_uses_sonar_endpoint(self, mock_urlopen):
        mock_urlopen.return_value = _mock_perplexity_response("Macro context here.")
        perplexity_fetcher.get_macro_context("AAPL", "Technology")
        call_args = mock_urlopen.call_args
        request_obj = call_args[0][0]
        # sonar endpoint (not sonar-pro)
        self.assertIn("/perplexity/sonar", request_obj.full_url)


# ── report_builder ────────────────────────────────────────────────────────────

class TestReportBuilder(unittest.TestCase):
    def setUp(self):
        self.ticker = "NVDA"
        self.market_data = {
            "price_history": {
                "data": {
                    "results": [
                        {"c": 800.0, "o": 795.0, "h": 810.0, "l": 790.0},
                        {"c": 850.0, "o": 800.0, "h": 860.0, "l": 800.0},
                        {"c": 880.0, "o": 850.0, "h": 890.0, "l": 845.0},
                    ]
                }
            },
            "news": {
                "data": {
                    "news": [
                        {"headline": "NVIDIA Reports Record Revenue", "source": "Reuters", "date": "2024-01-15"},
                        {"headline": "AI Chip Demand Surges", "source": "Bloomberg", "date": "2024-01-14"},
                    ]
                }
            },
            "financials": {
                "data": {
                    "snapshot": {
                        "price_to_earnings_ratio": 35.2,
                        "enterprise_value": 1_115_000_000_000,
                        "enterprise_value_to_revenue_ratio": 24.85,  # → revenue ≈ $44.87B
                        "net_margin": 0.468,
                        "earnings_per_share": 16.84,
                    }
                }
            },
            "sec_filings": {
                "data": {
                    "filings": [
                        {"filing_type": "10-K", "filing_date": "2024-01-15", "url": "https://sec.gov/example"},
                        {"filing_type": "10-Q", "filing_date": "2023-10-20"},
                    ]
                }
            },
            "insider_trades": {
                "data": {
                    "insider_trades": [
                        {"name": "Jensen Huang", "title": "CEO", "transaction_type": "Buy",
                         "transaction_shares": 1000, "transaction_price_per_share": 875.50,
                         "transaction_value": 875_500, "transaction_date": "2024-01-10"},
                    ]
                }
            },
            "analyst_estimates": {
                "data": {
                    "analyst_estimates": [
                        {"fiscal_period": "2027-01-31", "earnings_per_share": 4.50, "revenue": 48_000_000_000},
                        {"fiscal_period": "2028-01-31", "earnings_per_share": 6.20, "revenue": 56_000_000_000},
                    ]
                }
            },
        }
        self.narrative = (
            "## NVIDIA Analysis\n\n"
            "NVIDIA dominates the AI chip market with approximately 80% market share. "
            "Strong demand from hyperscalers poses a challenge as competitors risk eroding margins."
        )
        self.macro = (
            "Technology sector faces headwinds from rising interest rates and regulatory uncertainty."
        )

    def test_report_contains_all_six_sections(self):
        report = build_report(self.ticker, self.market_data, self.narrative, self.macro)
        self.assertIn("## Executive Summary", report)
        self.assertIn("## 1. Financial Snapshot", report)
        self.assertIn("## 2. Market Narrative & Qualitative Analysis", report)
        self.assertIn("## 3. Macro & Sector Context", report)
        self.assertIn("## 4. Recent News", report)
        self.assertIn("## 5. Risk Factors", report)
        self.assertIn("## 6. Data Sources", report)

    def test_report_contains_ticker(self):
        report = build_report(self.ticker, self.market_data, self.narrative, self.macro)
        self.assertIn("NVDA", report)

    def test_report_contains_narrative_text(self):
        report = build_report(self.ticker, self.market_data, self.narrative, self.macro)
        self.assertIn("NVIDIA dominates the AI chip market", report)

    def test_report_contains_macro_text(self):
        report = build_report(self.ticker, self.market_data, self.narrative, self.macro)
        self.assertIn("Technology sector faces headwinds", report)

    def test_report_contains_news_headline(self):
        report = build_report(self.ticker, self.market_data, self.narrative, self.macro)
        self.assertIn("NVIDIA Reports Record Revenue", report)

    def test_crypto_report_skips_equity_sections(self):
        crypto_market_data = {
            "price_history": {"data": {"price": 95_000.00}},
            "news": {"data": {"news": [{"headline": "BTC Hits New High", "source": "CoinDesk", "date": "2024-01-15"}]}},
        }
        report = build_report("BTC-USD", crypto_market_data, self.narrative, self.macro)
        self.assertIn("Not applicable for crypto assets", report)
        self.assertIn("## 6. Data Sources", report)

    def test_price_calculation(self):
        report = build_report(self.ticker, self.market_data, self.narrative, self.macro)
        # Last close is 880, first is 800 → +10%
        self.assertIn("$880.00", report)

    def test_revenue_back_calculated(self):
        # EV $1.115T ÷ EV/Rev 24.85 ≈ $44.87B
        report = build_report(self.ticker, self.market_data, self.narrative, self.macro)
        self.assertIn("$44.87B", report)

    def test_pe_ratio_field(self):
        report = build_report(self.ticker, self.market_data, self.narrative, self.macro)
        self.assertIn("35.2x", report)

    def test_eps_from_analyst_estimates(self):
        # analyst_estimates[0].earnings_per_share = 4.50 with period label
        report = build_report(self.ticker, self.market_data, self.narrative, self.macro)
        self.assertIn("$4.50", report)
        self.assertIn("2027-01-31", report)

    def test_forward_revenue_row(self):
        # analyst_estimates[0].revenue = $48B with period label
        report = build_report(self.ticker, self.market_data, self.narrative, self.macro)
        self.assertIn("Forward Revenue Est.", report)
        self.assertIn("$48.00B", report)
        self.assertNotIn("Analyst Price Target", report)

    def test_insider_trade_exact_fields(self):
        report = build_report(self.ticker, self.market_data, self.narrative, self.macro)
        self.assertIn("Jensen Huang", report)
        self.assertIn("$875.50/share", report)
        self.assertIn("2024-01-10", report)
        self.assertIn("$875,500.00", report)  # transaction_value formatted (< $1M threshold)


if __name__ == "__main__":
    unittest.main(verbosity=2)
