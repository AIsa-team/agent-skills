"""Offline contract and freshness regression tests; HTTP boundaries are mocked."""

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lib import aisa, dates, instagram, normalize, pinterest, threads, tiktok, youtube_yt


FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "provider_contracts.json").read_text())
WINDOW = ("2026-09-15", "2026-10-15")


class AdapterTests(unittest.TestCase):
    def fixture(self, name):
        return copy.deepcopy(FIXTURES[name])

    def test_x_current_fields_survive_normalization(self):
        raw = aisa.parse_twitter_response(self.fixture("twitter"), query="example")
        item = normalize.normalize_source_items("x", raw, *WINDOW)[0]
        self.assertEqual(item.author, "example")
        self.assertEqual(item.published_at, "2026-10-15")
        self.assertEqual(item.engagement, {"likes": 23, "reposts": 4, "replies": 3, "quotes": 0})

    def test_x_nested_author_can_construct_url_and_missing_metrics_stay_unknown(self):
        payload = self.fixture("twitter")
        tweet = payload["tweets"][0]
        del tweet["url"]
        for key in ("likeCount", "retweetCount", "replyCount", "quoteCount"):
            del tweet[key]
        item = normalize.normalize_source_items("x", aisa.parse_twitter_response(payload), *WINDOW)[0]
        self.assertEqual(item.url, "https://x.com/example/status/123")
        self.assertEqual(item.engagement, {})

    def test_youtube_nested_channel_relative_date_and_no_evergreen_fallback(self):
        raw = aisa.parse_youtube_response(self.fixture("youtube"), topic="example", from_date=WINDOW[0], to_date=WINDOW[1])
        self.assertEqual(len(raw), 1)
        self.assertEqual(raw[0]["date"], "2026-10-13")
        self.assertEqual(raw[0]["channel_name"], "Example Channel")
        self.assertEqual(raw[0]["duration"], "12:30")
        item = normalize.normalize_source_items("youtube", raw, *WINDOW)[0]
        self.assertEqual(item.date_confidence, "med")
        self.assertEqual(item.engagement, {"views": 42})

    def test_youtube_end_date_is_enforced(self):
        raw = aisa.parse_youtube_response(self.fixture("youtube"), topic="example", from_date="2026-10-01", to_date="2026-10-12")
        self.assertEqual(raw, [])

    def test_youtube_request_uses_documented_parameters(self):
        with patch.object(aisa.http, "get", return_value={"videos": []}) as get:
            response = aisa.search_youtube("test-key", "example", depth="deep")
        self.assertEqual(parse_qs(urlparse(get.call_args.args[0]).query), {"engine": ["youtube"], "q": ["example"]})
        self.assertIsNotNone(dates.parse_date(response["_observed_at"]))

    def test_youtube_wrapper_forwards_end_date_and_handles_unknown_views(self):
        payload = self.fixture("youtube")
        del payload["videos"][0]["views"]
        with patch.object(youtube_yt.env, "get_config", return_value={"AISA_API_KEY": "test-key"}), \
                patch.object(aisa, "search_youtube", return_value=payload):
            result = youtube_yt.search_youtube("example", *WINDOW)
            excluded = youtube_yt.search_youtube("example", "2026-10-01", "2026-10-12")
        self.assertIsNone(result["items"][0]["engagement"]["views"])
        self.assertEqual(excluded["items"], [])

    def test_market_search_route_and_observation_time(self):
        with patch.object(aisa.http, "get", return_value={"events": []}) as get:
            response = aisa.search_polymarket("test-key", "example")
        url = urlparse(get.call_args.args[0])
        self.assertEqual(url.path, "/apis/v1/polymarket/public-search")
        self.assertEqual(parse_qs(url.query)["q"], ["example"])
        self.assertEqual(parse_qs(url.query)["events_status"], ["active"])
        self.assertIsNotNone(dates.parse_date(response["_observed_at"]))

    def test_market_search_flattens_events_and_preserves_observed_vs_resolution(self):
        raw = aisa.parse_polymarket_response(self.fixture("polymarket"), topic="example")
        self.assertEqual(len(raw), 1)
        self.assertEqual(raw[0]["probability"], 0.75)
        self.assertEqual(raw[0]["url"], "https://polymarket.com/event/example-event/example-question")
        item = normalize.normalize_source_items("polymarket", raw, *WINDOW)[0]
        self.assertIsNone(item.published_at)
        self.assertEqual(item.metadata["observed_at"], "2026-10-15T12:00:00+00:00")
        self.assertEqual(item.metadata["end_date"], "2026-12-31")
        self.assertEqual(item.metadata["outcome_prices"], [("Yes", 0.75), ("No", 0.25)])
        self.assertEqual(item.engagement, {"volume": 1000.0, "liquidity": 25.0})
        self.assertEqual(item.metadata["date_kind"], "market_observation")

    def test_market_top_level_array_and_native_price_arrays(self):
        market = self.fixture("polymarket")["events"][0]["markets"][0]
        market["outcomes"] = ["Yes", "No"]
        market["outcomePrices"] = [0, 1]
        raw = aisa.parse_polymarket_response([market], observed_at="2026-10-14T12:00:00Z")
        self.assertEqual(raw[0]["probability"], 0)
        self.assertEqual(len(normalize.normalize_source_items("polymarket", raw, *WINDOW)), 1)

    def test_market_cached_or_missing_observation_is_not_refreshed_by_parsing(self):
        for stamp in (None, "2026-09-01T12:00:00Z", "2026-10-16T12:00:00Z"):
            with self.subTest(stamp=stamp):
                payload = self.fixture("polymarket")
                payload["_observed_at"] = stamp
                raw = aisa.parse_polymarket_response(payload)
                self.assertEqual(normalize.normalize_source_items("polymarket", raw, *WINDOW), [])

    def test_market_closed_and_duplicate_markets_are_excluded(self):
        payload = self.fixture("polymarket")
        market = payload["events"][0]["markets"][0]
        payload["events"][0]["markets"] += [copy.deepcopy(market), {**market, "id": "closed", "closed": True}]
        self.assertEqual(len(aisa.parse_polymarket_response(payload)), 1)

    def test_market_invalid_price_and_volume_are_unknown_not_nan_or_percent(self):
        payload = self.fixture("polymarket")
        market = payload["events"][0]["markets"][0]
        market.update(outcomePrices='["NaN", "150"]', volume="NaN", volumeNum="NaN", liquidity="-1")
        raw = aisa.parse_polymarket_response(payload)
        self.assertIsNone(raw[0]["probability"])
        item = normalize.normalize_source_items("polymarket", raw, *WINDOW)[0]
        self.assertEqual(item.metadata["outcome_prices"], [])
        self.assertEqual(item.engagement, {})

    def test_tavily_parameters_dates_and_result_limit(self):
        with patch.object(aisa.http, "post", return_value={"results": []}) as post:
            aisa.search_tavily("test-key", "example", WINDOW, limit=40, topic="general")
        payload = post.call_args.args[1]
        self.assertEqual(payload["max_results"], 20)
        self.assertEqual((payload["start_date"], payload["end_date"]), WINDOW)
        self.assertEqual(payload["topic"], "general")

    def test_social_discovery_keeps_provenance_unknown_metrics_and_date_filter(self):
        for module, host in ((tiktok, "www.tiktok.com"), (instagram, "www.instagram.com"),
                             (threads, "www.threads.net"), (pinterest, "www.pinterest.com")):
            with self.subTest(source=module.__name__):
                response = self.fixture("tavily")
                response["results"][0]["url"] = f"https://{host}/post/example"
                with patch.object(aisa, "search_tavily", return_value=response) as search:
                    raw = module._search_via_aisa("example", *WINDOW, "deep", "test-key")["items"]
                self.assertEqual(search.call_args.kwargs["date_range"], WINDOW)
                self.assertEqual(search.call_args.kwargs["limit"], 20)
                self.assertEqual(search.call_args.kwargs["topic"], "general")
                source = module.__name__.split(".")[-1]
                item = normalize.normalize_source_items(source, raw, *WINDOW)[0]
                self.assertEqual(item.engagement, {})
                self.assertEqual(item.metadata["retrieval_method"], "web_discovery")

    def test_all_ranked_sources_require_valid_in_window_date(self):
        sources = ("reddit", "x", "youtube", "tiktok", "instagram", "hackernews", "threads", "pinterest", "grounding", "github")
        for source in sources:
            for value in (None, "", "not-a-date", "2026-09-14", "2026-10-16"):
                with self.subTest(source=source, date=value):
                    raw = [{"date": value, "title": "Example", "url": "https://example.com"}]
                    self.assertEqual(normalize.normalize_source_items(source, raw, *WINDOW, freshness_mode="evergreen_ok"), [])
            for boundary in WINDOW:
                with self.subTest(source=source, boundary=boundary):
                    raw = [{"date": boundary, "title": "Example", "url": "https://example.com"}]
                    self.assertEqual(len(normalize.normalize_source_items(source, raw, *WINDOW)), 1)

    def test_date_relative_formats_and_invalid_timestamps(self):
        reference = datetime(2026, 10, 15, 12, tzinfo=timezone.utc)
        for text, expected in (("Streamed 2 days ago", "2026-10-13"), ("1 week ago", "2026-10-08"),
                               ("1 month ago", "2026-09-15"), ("Premiered Oct 12, 2026", "2026-10-12")):
            self.assertEqual(dates.parse_date(text, reference_time=reference).date().isoformat(), expected)
        for value in ("NaN", "inf", "1e100", "garbage", True):
            self.assertIsNone(dates.parse_date(value))


if __name__ == "__main__":
    unittest.main()
