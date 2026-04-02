"""
Tests for prediction_market_client.py

Covers PredictionMarketClient API methods and CLI argument parsing.
All network calls are mocked so no real HTTP requests are made.
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call
import urllib.error

# Ensure the script directory is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "script"))

import prediction_market_client as pmc
from prediction_market_client import PredictionMarketClient


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def make_client(api_key="test-key"):
    with patch.dict(os.environ, {"AISA_API_KEY": api_key}):
        return PredictionMarketClient()


def mock_urlopen(response_data: dict):
    """Return a context-manager mock that yields response_data as JSON bytes."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ──────────────────────────────────────────────────────────────────────────────
# PredictionMarketClient initialization
# ──────────────────────────────────────────────────────────────────────────────

class TestClientInit(unittest.TestCase):
    def test_reads_api_key_from_env(self):
        with patch.dict(os.environ, {"AISA_API_KEY": "env-key"}):
            client = PredictionMarketClient()
            self.assertEqual(client.api_key, "env-key")

    def test_explicit_key_takes_precedence(self):
        with patch.dict(os.environ, {"AISA_API_KEY": "env-key"}):
            client = PredictionMarketClient(api_key="override")
            self.assertEqual(client.api_key, "override")

    def test_missing_key_raises_value_error(self):
        env = {k: v for k, v in os.environ.items() if k != "AISA_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ValueError):
                PredictionMarketClient()


# ──────────────────────────────────────────────────────────────────────────────
# _request (base HTTP method)
# ──────────────────────────────────────────────────────────────────────────────

class TestRequest(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    def test_successful_get(self):
        payload = {"success": True, "data": []}
        with patch("urllib.request.urlopen", return_value=mock_urlopen(payload)):
            result = self.client._request("/polymarket/markets")
        self.assertEqual(result, payload)

    def test_http_error_returns_json_body(self):
        error_payload = {"success": False, "error": {"code": "401", "message": "Unauthorized"}}
        http_err = urllib.error.HTTPError(
            url="http://x", code=401, msg="Unauthorized",
            hdrs=None, fp=MagicMock(read=lambda: json.dumps(error_payload).encode()),
        )
        with patch("urllib.request.urlopen", side_effect=http_err):
            result = self.client._request("/polymarket/markets")
        self.assertIn("error", result)

    def test_network_error_returns_error_dict(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            result = self.client._request("/polymarket/markets")
        self.assertEqual(result["error"]["code"], "NETWORK_ERROR")

    def test_params_are_url_encoded(self):
        captured_urls = []

        def fake_urlopen(req, timeout=None):
            captured_urls.append(req.full_url)
            return mock_urlopen({"success": True})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            self.client._request("/polymarket/markets", params={"search": "NBA Finals", "limit": 10})

        self.assertTrue(len(captured_urls) == 1)
        self.assertIn("search=NBA+Finals", captured_urls[0])
        self.assertIn("limit=10", captured_urls[0])

    def test_none_params_are_excluded(self):
        captured_urls = []

        def fake_urlopen(req, timeout=None):
            captured_urls.append(req.full_url)
            return mock_urlopen({"success": True})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            self.client._request("/polymarket/markets", params={"search": None, "limit": 5})

        self.assertNotIn("search", captured_urls[0])
        self.assertIn("limit=5", captured_urls[0])


# ──────────────────────────────────────────────────────────────────────────────
# Polymarket methods
# ──────────────────────────────────────────────────────────────────────────────

class TestPolymarketMethods(unittest.TestCase):
    def setUp(self):
        self.client = make_client()
        self.ok = {"success": True, "data": []}

    def _patch(self, resp=None):
        return patch("urllib.request.urlopen",
                     return_value=mock_urlopen(resp or self.ok))

    def test_polymarket_price_uses_correct_path(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen({"price": 0.65})
        with patch("urllib.request.urlopen", side_effect=fake_open):
            result = self.client.polymarket_price("tok123")
        self.assertIn("/polymarket/market-price/tok123", captured[0])
        self.assertEqual(result["price"], 0.65)

    def test_polymarket_price_with_at_time(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen({"price": 0.50})
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.polymarket_price("tok123", at_time=1700000000)
        self.assertIn("at_time=1700000000", captured[0])

    def test_polymarket_markets_search(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.polymarket_markets(search="election", status="open", limit=5)
        url = captured[0]
        self.assertIn("search=election", url)
        self.assertIn("status=open", url)
        self.assertIn("limit=5", url)

    def test_polymarket_markets_multi_slugs(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.polymarket_markets(market_slug=["slug-a", "slug-b"])
        url = captured[0]
        self.assertIn("market_slug=slug-a", url)
        self.assertIn("market_slug=slug-b", url)

    def test_polymarket_orderbooks(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.polymarket_orderbooks("tok999")
        self.assertIn("token_id=tok999", captured[0])

    def test_polymarket_positions(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.polymarket_positions("0xWALLET")
        self.assertIn("/polymarket/positions/wallet/0xWALLET", captured[0])

    def test_polymarket_pnl(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.polymarket_pnl("0xWALLET", granularity="day")
        url = captured[0]
        self.assertIn("/polymarket/wallet/pnl/0xWALLET", url)
        self.assertIn("granularity=day", url)

    def test_polymarket_candlesticks(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.polymarket_candlesticks("cond123", 1700000000, 1700086400, interval=60)
        url = captured[0]
        self.assertIn("/polymarket/candlesticks/cond123", url)
        self.assertIn("interval=60", url)


# ──────────────────────────────────────────────────────────────────────────────
# Kalshi methods
# ──────────────────────────────────────────────────────────────────────────────

class TestKalshiMethods(unittest.TestCase):
    def setUp(self):
        self.client = make_client()
        self.ok = {"success": True, "data": []}

    def test_kalshi_price_uses_correct_path(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen({"yes_price": 55})
        with patch("urllib.request.urlopen", side_effect=fake_open):
            result = self.client.kalshi_price("KXNBA-25-A")
        self.assertIn("/kalshi/market-price/KXNBA-25-A", captured[0])
        self.assertEqual(result["yes_price"], 55)

    def test_kalshi_markets_search(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.kalshi_markets(search="fed rate", status="open")
        url = captured[0]
        # kalshi_markets uses urllib.parse.quote which encodes spaces as %20
        self.assertIn("search=fed%20rate", url)
        self.assertIn("status=open", url)

    def test_kalshi_markets_multi_tickers(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.kalshi_markets(market_ticker=["KXNBA-25-A", "KXNBA-25-B"])
        url = captured[0]
        self.assertIn("market_ticker=KXNBA-25-A", url)
        self.assertIn("market_ticker=KXNBA-25-B", url)

    def test_kalshi_orderbooks(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.kalshi_orderbooks("KXNBA-25-A")
        self.assertIn("ticker=KXNBA-25-A", captured[0])

    def test_kalshi_trades(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.kalshi_trades(ticker="KXNBA-25-A", limit=50)
        url = captured[0]
        self.assertIn("ticker=KXNBA-25-A", url)
        self.assertIn("limit=50", url)


# ──────────────────────────────────────────────────────────────────────────────
# Cross-platform sports methods
# ──────────────────────────────────────────────────────────────────────────────

class TestSportsMethods(unittest.TestCase):
    def setUp(self):
        self.client = make_client()
        self.ok = {"success": True, "data": []}

    def test_sports_matching_by_slug(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.sports_matching(polymarket_slugs=["nba-lakers-vs-celtics"])
        self.assertIn("polymarket_market_slug=nba-lakers-vs-celtics", captured[0])

    def test_sports_matching_by_ticker(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.sports_matching(kalshi_tickers=["KXNBA-25-LAL-BOS"])
        self.assertIn("kalshi_event_ticker=KXNBA-25-LAL-BOS", captured[0])

    def test_sports_by_date(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.sports_by_date("nba", "2025-04-01")
        url = captured[0]
        self.assertIn("/matching-markets/sports/nba", url)
        self.assertIn("date=2025-04-01", url)

    def test_sports_matching_multiple_slugs(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return mock_urlopen(self.ok)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.sports_matching(polymarket_slugs=["slug-a", "slug-b"])
        url = captured[0]
        self.assertIn("polymarket_market_slug=slug-a", url)
        self.assertIn("polymarket_market_slug=slug-b", url)


# ──────────────────────────────────────────────────────────────────────────────
# Authorization header
# ──────────────────────────────────────────────────────────────────────────────

class TestAuthorizationHeader(unittest.TestCase):
    def test_bearer_token_sent(self):
        client = make_client("my-secret-key")
        captured_headers = []

        def fake_open(req, timeout=None):
            captured_headers.append(dict(req.headers))
            return mock_urlopen({"success": True})

        with patch("urllib.request.urlopen", side_effect=fake_open):
            client.polymarket_price("tok123")

        auth = captured_headers[0].get("Authorization", "")
        self.assertEqual(auth, "Bearer my-secret-key")


# ──────────────────────────────────────────────────────────────────────────────
# CLI argument parsing
# ──────────────────────────────────────────────────────────────────────────────

class TestCLI(unittest.TestCase):
    def _run(self, argv):
        """Run main() with patched sys.argv and mocked client methods."""
        results = {}

        def fake_open(req, timeout=None):
            results["url"] = req.full_url
            return mock_urlopen({"success": True, "data": []})

        with patch.dict(os.environ, {"AISA_API_KEY": "test-key"}):
            with patch("urllib.request.urlopen", side_effect=fake_open):
                with patch("sys.argv", ["prediction_market_client.py"] + argv):
                    try:
                        pmc.main()
                    except SystemExit:
                        pass
        return results

    def test_polymarket_markets_command(self):
        r = self._run(["polymarket", "markets", "--search", "election", "--limit", "5"])
        self.assertIn("polymarket/markets", r.get("url", ""))

    def test_polymarket_price_command(self):
        r = self._run(["polymarket", "price", "tok123"])
        self.assertIn("polymarket/market-price/tok123", r.get("url", ""))

    def test_kalshi_markets_command(self):
        r = self._run(["kalshi", "markets", "--search", "fed"])
        self.assertIn("kalshi/markets", r.get("url", ""))

    def test_kalshi_price_command(self):
        r = self._run(["kalshi", "price", "KXNBA-25-A"])
        self.assertIn("kalshi/market-price/KXNBA-25-A", r.get("url", ""))

    def test_sports_by_date_command(self):
        r = self._run(["sports", "by-date", "nba", "--date", "2025-04-01"])
        self.assertIn("matching-markets/sports/nba", r.get("url", ""))

    def test_sports_matching_command(self):
        r = self._run(["sports", "matching", "--polymarket-slug", "some-slug"])
        self.assertIn("matching-markets/sports", r.get("url", ""))

    def test_no_platform_exits(self):
        with patch.dict(os.environ, {"AISA_API_KEY": "key"}):
            with patch("sys.argv", ["prediction_market_client.py"]):
                with self.assertRaises(SystemExit):
                    pmc.main()

    def test_missing_api_key_exits(self):
        env = {k: v for k, v in os.environ.items() if k != "AISA_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with patch("sys.argv", ["prediction_market_client.py",
                                    "polymarket", "price", "tok123"]):
                with self.assertRaises(SystemExit):
                    pmc.main()


if __name__ == "__main__":
    unittest.main()
