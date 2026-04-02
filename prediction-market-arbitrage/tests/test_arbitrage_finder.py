"""
Tests for arbitrage_finder.py

Covers pure-logic functions (no network calls) and mocked API interactions.
"""

import json
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Ensure the script directory is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "script"))

import arbitrage_finder as af
from arbitrage_finder import (
    AIsaClient,
    calculate_spread,
    compute_orderbook_liquidity,
    extract_kalshi_price,
    extract_polymarket_price,
    parse_matched_pairs,
    analyze_pair,
)


# ──────────────────────────────────────────────────────────────────────────────
# extract_polymarket_price
# ──────────────────────────────────────────────────────────────────────────────

class TestExtractPolymarketPrice(unittest.TestCase):
    def test_direct_price_field(self):
        self.assertAlmostEqual(extract_polymarket_price({"price": 0.65}), 0.65)

    def test_price_as_string(self):
        self.assertAlmostEqual(extract_polymarket_price({"price": "0.72"}), 0.72)

    def test_nested_data_price(self):
        self.assertAlmostEqual(extract_polymarket_price({"data": {"price": 0.45}}), 0.45)

    def test_nested_data_mid(self):
        self.assertAlmostEqual(extract_polymarket_price({"data": {"mid": 0.55}}), 0.55)

    def test_nested_data_last(self):
        self.assertAlmostEqual(extract_polymarket_price({"data": {"last": 0.30}}), 0.30)

    def test_error_response_returns_none(self):
        self.assertIsNone(extract_polymarket_price({"error": {"code": "NOT_FOUND"}}))

    def test_empty_response_returns_none(self):
        self.assertIsNone(extract_polymarket_price({}))

    def test_zero_price(self):
        # price=0: the code checks `if price is not None`, so 0 is returned as 0.0
        result = extract_polymarket_price({"price": 0})
        self.assertAlmostEqual(result, 0.0)


# ──────────────────────────────────────────────────────────────────────────────
# extract_kalshi_price
# ──────────────────────────────────────────────────────────────────────────────

class TestExtractKalshiPrice(unittest.TestCase):
    def test_yes_price_in_cents(self):
        # Kalshi prices > 1 are in cents and should be normalized
        result = extract_kalshi_price({"yes_price": 65})
        self.assertAlmostEqual(result, 0.65)

    def test_yes_price_already_decimal(self):
        result = extract_kalshi_price({"yes_price": 0.65})
        self.assertAlmostEqual(result, 0.65)

    def test_price_field(self):
        result = extract_kalshi_price({"price": 72})
        self.assertAlmostEqual(result, 0.72)

    def test_last_price_field(self):
        result = extract_kalshi_price({"last_price": 45})
        self.assertAlmostEqual(result, 0.45)

    def test_yes_ask_field(self):
        result = extract_kalshi_price({"yes_ask": 30})
        self.assertAlmostEqual(result, 0.30)

    def test_nested_data_price(self):
        result = extract_kalshi_price({"data": {"yes_price": 55}})
        self.assertAlmostEqual(result, 0.55)

    def test_error_response_returns_none(self):
        self.assertIsNone(extract_kalshi_price({"error": {"code": "NOT_FOUND"}}))

    def test_empty_response_returns_none(self):
        self.assertIsNone(extract_kalshi_price({}))


# ──────────────────────────────────────────────────────────────────────────────
# calculate_spread
# ──────────────────────────────────────────────────────────────────────────────

class TestCalculateSpread(unittest.TestCase):
    def test_no_arbitrage_when_prices_equal(self):
        result = calculate_spread(0.5, 0.5)
        self.assertAlmostEqual(result["spread_pct"], 0.0)
        self.assertAlmostEqual(result["total_cost"], 1.0)

    def test_arbitrage_direction_a(self):
        # poly_yes=0.40, kalshi_yes=0.55 → buy YES poly + NO kalshi = 0.40+0.45=0.85 → profit 15%
        result = calculate_spread(0.40, 0.55)
        self.assertAlmostEqual(result["spread_pct"], 15.0, places=1)
        self.assertEqual(result["buy_yes_platform"], "Polymarket")
        self.assertEqual(result["buy_no_platform"], "Kalshi")
        self.assertAlmostEqual(result["total_cost"], 0.85, places=4)

    def test_arbitrage_direction_b(self):
        # poly_yes=0.55, kalshi_yes=0.40 → buy YES kalshi + NO poly = 0.40+0.45=0.85 → profit 15%
        result = calculate_spread(0.55, 0.40)
        self.assertAlmostEqual(result["spread_pct"], 15.0, places=1)
        self.assertEqual(result["buy_yes_platform"], "Kalshi")
        self.assertEqual(result["buy_no_platform"], "Polymarket")

    def test_zero_spread_when_no_discrepancy(self):
        # calculate_spread always picks the best direction; with identical prices
        # cost = p + (1-p) = 1.0, so spread is always 0 (never negative).
        result = calculate_spread(0.60, 0.60)
        self.assertAlmostEqual(result["spread_pct"], 0.0)

    def test_output_keys_present(self):
        result = calculate_spread(0.50, 0.50)
        for key in ("spread_pct", "profit_per_dollar", "direction",
                    "buy_yes_platform", "buy_yes_price", "buy_no_platform",
                    "buy_no_price", "total_cost"):
            self.assertIn(key, result)


# ──────────────────────────────────────────────────────────────────────────────
# compute_orderbook_liquidity
# ──────────────────────────────────────────────────────────────────────────────

class TestComputeOrderbookLiquidity(unittest.TestCase):
    def _ob(self, bids, asks):
        return {"bids": bids, "asks": asks}

    def test_basic_dict_levels(self):
        ob = self._ob(
            bids=[{"price": 0.60, "size": 100}],
            asks=[{"price": 0.65, "size": 200}],
        )
        result = compute_orderbook_liquidity(ob)
        expected = 0.60 * 100 + 0.65 * 200
        self.assertAlmostEqual(result, expected)

    def test_tuple_levels(self):
        ob = self._ob(bids=[(0.55, 50)], asks=[(0.60, 100)])
        result = compute_orderbook_liquidity(ob)
        expected = 0.55 * 50 + 0.60 * 100
        self.assertAlmostEqual(result, expected)

    def test_kalshi_cents_price(self):
        # Prices > 1 are in cents (e.g. 55 cents)
        ob = self._ob(bids=[{"price": 55, "size": 100}], asks=[])
        result = compute_orderbook_liquidity(ob)
        expected = 100 * 0.55
        self.assertAlmostEqual(result, expected)

    def test_nested_data_key(self):
        ob = {"data": {"bids": [{"price": 0.50, "size": 200}], "asks": []}}
        result = compute_orderbook_liquidity(ob)
        self.assertAlmostEqual(result, 100.0)

    def test_nested_orderbook_key(self):
        ob = {"orderbook": {"bids": [{"price": 0.50, "size": 100}], "asks": []}}
        result = compute_orderbook_liquidity(ob)
        self.assertAlmostEqual(result, 50.0)

    def test_empty_orderbook_returns_none(self):
        ob = {"bids": [], "asks": []}
        result = compute_orderbook_liquidity(ob)
        self.assertIsNone(result)

    def test_error_response_returns_none(self):
        self.assertIsNone(compute_orderbook_liquidity({"error": "not found"}))

    def test_quantity_field_fallback(self):
        ob = {"bids": [{"price": 0.50, "quantity": 80}], "asks": []}
        result = compute_orderbook_liquidity(ob)
        self.assertAlmostEqual(result, 40.0)


# ──────────────────────────────────────────────────────────────────────────────
# parse_matched_pairs
# ──────────────────────────────────────────────────────────────────────────────

class TestParseMatchedPairs(unittest.TestCase):
    def _sample_item(self, title="Game A"):
        return {
            "title": title,
            "polymarket": {
                "market_slug": "game-a",
                "condition_id": "0xabc",
                "side_a": {"id": "token-yes"},
                "side_b": {"id": "token-no"},
            },
            "kalshi": {
                "market_ticker": "KXNBA-25-A",
                "event_ticker": "KXNBA-25",
            },
        }

    def test_top_level_list(self):
        resp = [self._sample_item()]
        pairs = parse_matched_pairs(resp)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["title"], "Game A")

    def test_data_wrapper(self):
        resp = {"data": [self._sample_item("Game B")]}
        pairs = parse_matched_pairs(resp)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["title"], "Game B")

    def test_matches_wrapper(self):
        resp = {"matches": [self._sample_item("Game C")]}
        pairs = parse_matched_pairs(resp)
        self.assertEqual(len(pairs), 1)

    def test_markets_wrapper(self):
        resp = {"markets": [self._sample_item("Game D")]}
        pairs = parse_matched_pairs(resp)
        self.assertEqual(len(pairs), 1)

    def test_polymarket_fields_extracted(self):
        pairs = parse_matched_pairs([self._sample_item()])
        poly = pairs[0]["polymarket"]
        self.assertEqual(poly["market_slug"], "game-a")
        self.assertEqual(poly["token_id_yes"], "token-yes")
        self.assertEqual(poly["token_id_no"], "token-no")
        self.assertEqual(poly["condition_id"], "0xabc")

    def test_kalshi_fields_extracted(self):
        pairs = parse_matched_pairs([self._sample_item()])
        kal = pairs[0]["kalshi"]
        self.assertEqual(kal["market_ticker"], "KXNBA-25-A")
        self.assertEqual(kal["event_ticker"], "KXNBA-25")

    def test_missing_polymarket_key_yields_empty_fields(self):
        # When "polymarket" key is absent the parser falls back to an empty dict,
        # so the pair is still included but with blank token IDs.
        item = self._sample_item()
        del item["polymarket"]
        pairs = parse_matched_pairs([item])
        # Pair is added; polymarket fields default to empty strings
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["polymarket"]["token_id_yes"], "")

    def test_missing_kalshi_key_yields_empty_fields(self):
        # When "kalshi" key is absent the parser falls back to an empty dict,
        # so the pair is still included but with a blank market_ticker.
        item = self._sample_item()
        del item["kalshi"]
        pairs = parse_matched_pairs([item])
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["kalshi"]["market_ticker"], "")

    def test_empty_response(self):
        self.assertEqual(parse_matched_pairs([]), [])
        self.assertEqual(parse_matched_pairs({}), [])

    def test_multiple_pairs(self):
        items = [self._sample_item(f"Game {i}") for i in range(3)]
        pairs = parse_matched_pairs(items)
        self.assertEqual(len(pairs), 3)

    def test_polymarket_as_list(self):
        item = self._sample_item()
        item["polymarket"] = [item["polymarket"]]
        pairs = parse_matched_pairs([item])
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["polymarket"]["market_slug"], "game-a")

    def test_kalshi_as_list(self):
        item = self._sample_item()
        item["kalshi"] = [item["kalshi"]]
        pairs = parse_matched_pairs([item])
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["kalshi"]["market_ticker"], "KXNBA-25-A")


# ──────────────────────────────────────────────────────────────────────────────
# AIsaClient – requires AISA_API_KEY
# ──────────────────────────────────────────────────────────────────────────────

class TestAIsaClientInit(unittest.TestCase):
    def test_picks_up_env_var(self):
        with patch.dict(os.environ, {"AISA_API_KEY": "test-key"}):
            client = AIsaClient()
            self.assertEqual(client.api_key, "test-key")

    def test_explicit_key_overrides_env(self):
        with patch.dict(os.environ, {"AISA_API_KEY": "env-key"}):
            client = AIsaClient(api_key="explicit-key")
            self.assertEqual(client.api_key, "explicit-key")

    def test_missing_key_exits(self):
        env = {k: v for k, v in os.environ.items() if k != "AISA_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit):
                AIsaClient()


# ──────────────────────────────────────────────────────────────────────────────
# analyze_pair (mocked network)
# ──────────────────────────────────────────────────────────────────────────────

class TestAnalyzePair(unittest.TestCase):
    def _make_client(self):
        client = MagicMock(spec=AIsaClient)
        client.polymarket_price.return_value = {"price": 0.60}
        client.kalshi_price.return_value = {"yes_price": 40}   # 40 cents → 0.40
        client.polymarket_orderbook.return_value = {
            "bids": [{"price": 0.59, "size": 500}],
            "asks": [{"price": 0.61, "size": 500}],
        }
        client.kalshi_orderbook.return_value = {
            "bids": [{"price": 39, "size": 300}],
            "asks": [{"price": 41, "size": 300}],
        }
        return client

    def _pair(self):
        return {
            "title": "Test Game",
            "polymarket": {"market_slug": "test-game", "token_id_yes": "tok123", "token_id_no": "tok456"},
            "kalshi": {"market_ticker": "KXTEST-25", "event_ticker": "KXTEST"},
        }

    def test_returns_result_with_spread(self):
        client = self._make_client()
        result = analyze_pair(client, self._pair(), min_spread=0.0, min_liquidity=0.0)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Test Game")
        # poly=0.60, kalshi=0.40 → buy YES kalshi + NO poly = 0.40+0.40=0.80 → 20% spread
        self.assertGreater(result["spread_pct"], 0)

    def test_spread_below_minimum_returns_none(self):
        client = self._make_client()
        # 20% spread but require 30%
        result = analyze_pair(client, self._pair(), min_spread=30.0, min_liquidity=0.0)
        self.assertIsNone(result)

    def test_missing_token_id_returns_none(self):
        client = self._make_client()
        pair = self._pair()
        pair["polymarket"]["token_id_yes"] = ""
        result = analyze_pair(client, pair, min_spread=0.0, min_liquidity=0.0)
        self.assertIsNone(result)

    def test_missing_market_ticker_returns_none(self):
        client = self._make_client()
        pair = self._pair()
        pair["kalshi"]["market_ticker"] = ""
        result = analyze_pair(client, pair, min_spread=0.0, min_liquidity=0.0)
        self.assertIsNone(result)

    def test_price_error_returns_none(self):
        client = self._make_client()
        client.polymarket_price.return_value = {"error": {"code": "NOT_FOUND"}}
        result = analyze_pair(client, self._pair(), min_spread=0.0, min_liquidity=0.0)
        self.assertIsNone(result)

    def test_insufficient_liquidity_marks_not_actionable(self):
        client = self._make_client()
        # orderbooks return very small liquidity
        client.polymarket_orderbook.return_value = {
            "bids": [{"price": 0.59, "size": 1}],
            "asks": [],
        }
        client.kalshi_orderbook.return_value = {
            "bids": [{"price": 39, "size": 1}],
            "asks": [],
        }
        result = analyze_pair(client, self._pair(), min_spread=0.0, min_liquidity=10000.0)
        self.assertIsNotNone(result)
        self.assertFalse(result["actionable"])
        self.assertIn("Insufficient liquidity", result["reason"])

    def test_result_contains_expected_keys(self):
        client = self._make_client()
        result = analyze_pair(client, self._pair(), min_spread=0.0, min_liquidity=0.0)
        self.assertIsNotNone(result)
        for key in ("title", "spread_pct", "direction", "total_cost",
                    "polymarket_yes_price", "kalshi_yes_price", "actionable"):
            self.assertIn(key, result)


# ──────────────────────────────────────────────────────────────────────────────
# CLI integration (subprocess-free argument parsing)
# ──────────────────────────────────────────────────────────────────────────────

class TestCLIParsing(unittest.TestCase):
    """Test that the argparse setup handles valid and invalid arguments."""

    def _run_main(self, argv, env_key="dummy-key"):
        with patch.dict(os.environ, {"AISA_API_KEY": env_key}):
            with patch("arbitrage_finder.run_scan", return_value=[]) as mock_scan, \
                 patch("arbitrage_finder.run_match", return_value=[]) as mock_match, \
                 patch("arbitrage_finder.print_summary"):
                with patch("sys.argv", ["arbitrage_finder.py"] + argv):
                    try:
                        af.main()
                    except SystemExit:
                        pass
                return mock_scan, mock_match

    def test_scan_command_calls_run_scan(self):
        mock_scan, _ = self._run_main(["scan", "nba", "--date", "2025-04-01"])
        mock_scan.assert_called_once()
        call_kwargs = mock_scan.call_args
        self.assertEqual(call_kwargs[0][1], "nba")
        self.assertEqual(call_kwargs[0][2], "2025-04-01")

    def test_scan_with_filters(self):
        mock_scan, _ = self._run_main([
            "scan", "nba", "--date", "2025-04-01",
            "--min-spread", "3.0", "--min-liquidity", "500",
        ])
        mock_scan.assert_called_once()
        args = mock_scan.call_args[0]
        self.assertAlmostEqual(args[3], 3.0)
        self.assertAlmostEqual(args[4], 500.0)

    def test_match_with_polymarket_slug(self):
        _, mock_match = self._run_main(["match", "--polymarket-slug", "some-slug"])
        mock_match.assert_called_once()

    def test_match_with_kalshi_ticker(self):
        _, mock_match = self._run_main(["match", "--kalshi-ticker", "KXNBA-25"])
        mock_match.assert_called_once()

    def test_no_command_exits(self):
        with patch.dict(os.environ, {"AISA_API_KEY": "key"}):
            with patch("sys.argv", ["arbitrage_finder.py"]):
                with self.assertRaises(SystemExit):
                    af.main()


if __name__ == "__main__":
    unittest.main()
