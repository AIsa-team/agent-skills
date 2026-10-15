"""Keep paid evidence when a later request in the same batch is refused."""

from contextlib import ExitStack
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lib import aisa, costs, http, pipeline, schema, youtube_yt


class Reply:
    def __init__(self, body, headers=None):
        self.status = 200
        self.headers = headers or {}
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.body


class PartialCostResultsTests(unittest.TestCase):
    def youtube_pipeline(self, late_timeout=False):
        with tempfile.TemporaryDirectory() as temp, ExitStack() as stack:
            budget = costs.RunBudget(Path(temp) / "ledger.json", 100_000)
            today = datetime.now(timezone.utc).date().isoformat()
            config = {"AISA_API_KEY": "fixture-only", "AISA_MODEL": "fixture-model"}
            stack.enter_context(costs.activate(budget))
            stack.enter_context(patch.object(youtube_yt.env, "get_config", return_value=config))
            queries = stack.enter_context(patch.object(youtube_yt, "expand_youtube_queries", return_value=["first", "second", "third"]))
            quote_payload = {"object": "cost_estimate", "estimated_cost_micros_usd": 50_000,
                             "may_exceed_estimate": False}
            responses = [Reply(quote_payload), Reply({"video_results": [{
                "videoId": "one", "title": "Alpha launch", "publishedDate": today,
                "link": "https://www.youtube.com/watch?v=one", "views": 100,
            }]}, {"X-AISA-Customer-Cost-Micros-USD": "50000"})]
            if late_timeout:
                responses.extend([Reply(quote_payload), TimeoutError("lost response")])
            else:
                responses.append(Reply({**quote_payload, "estimated_cost_micros_usd": 60_000}))
            network = stack.enter_context(patch.object(http, "_open_aisa", side_effect=responses))
            report = pipeline.run(
                topic="Alpha", config=config, depth="default", requested_sources=["youtube"],
                web_backend="none", external_plan={
                    "intent": "factual", "source_weights": {"youtube": 1},
                    "subqueries": [{"label": "primary", "search_query": "Alpha", "ranking_query": "Alpha",
                                    "sources": ["youtube"]}],
                },
            )
            self.assertEqual(queries.call_count, 1)
            self.assertEqual(network.call_count, 4 if late_timeout else 3)
            self.assertEqual(len(report.items_by_source["youtube"]), 1)
            self.assertEqual(len(report.ranked_candidates), 1)
            self.assertIn("cost controls", report.errors_by_source["youtube"])
            self.assertEqual(report.artifacts["source_coverage"]["youtube"]["status"], "partial")
            self.assertEqual(budget.summary()["known_cost_micros_usd"], 50_000)
            self.assertEqual(budget.summary()["spent_micros_usd"], None if late_timeout else 50_000)

    def test_later_quote_refusal_preserves_earlier_paid_youtube_evidence(self):
        self.youtube_pipeline()

    def test_later_unknown_charge_preserves_evidence_and_remains_unknown(self):
        self.youtube_pipeline(late_timeout=True)

    def supplemental(self, related=False):
        today = datetime.now(timezone.utc).date().isoformat()
        plan = schema.QueryPlan("factual", "strict_recent", "none", "Alpha",
                                [schema.SubQuery("primary", "Alpha", "Alpha", ["x"])], {"x": 1})
        bundle = schema.RetrievalBundle()
        runtime = schema.ProviderRuntime("local", "deterministic", "local-score", "aisa")
        entities = {"x_handles": [] if related else ["first", "second", "third"]}
        kwargs = {"x_related": ["first", "second", "third"]} if related else {"x_handle": "first", "x_related": ["later"]}
        with patch.object(pipeline.entity_extract, "extract_entities", return_value=entities), patch.object(
                aisa, "search_twitter", side_effect=[{"tweets": [{
                    "text": "Alpha research", "url": "https://x.com/first/status/1", "date": today,
                    "author_handle": "first", "likes": 12,
                }]}, costs.CostControlError("remaining budget exhausted")]) as search:
            pipeline._run_supplemental_searches(
                topic="Alpha", bundle=bundle, plan=plan, config={"AISA_API_KEY": "fixture-only"},
                depth="default", date_range=(today, today), runtime=runtime, mock=False,
                rate_limited_sources=set(), rate_limit_lock=threading.Lock(), **kwargs,
            )
        self.assertEqual(search.call_count, 2)
        self.assertEqual(len(bundle.items_by_source["x"]), 1)
        self.assertIn("remaining budget exhausted", bundle.errors_by_source["x"])
        if related:
            self.assertIn(("supplemental-related", "x"), bundle.items_by_source_and_query)

    def test_primary_handle_batch_keeps_success_and_skips_related_after_refusal(self):
        self.supplemental()

    def test_related_handle_batch_keeps_success_after_refusal(self):
        self.supplemental(related=True)

    def test_handle_hint_cannot_expand_the_selected_sources(self):
        plan = schema.QueryPlan("factual", "strict_recent", "none", "Alpha",
                                [schema.SubQuery("primary", "Alpha", "Alpha", ["youtube"])], {"youtube": 1})
        runtime = schema.ProviderRuntime("local", "deterministic", "local-score", "aisa")
        with patch.object(aisa, "search_twitter") as search:
            pipeline._run_supplemental_searches(
                topic="Alpha", bundle=schema.RetrievalBundle(), plan=plan,
                config={"AISA_API_KEY": "fixture-only"}, depth="default", date_range=("2026-09-15", "2026-10-15"),
                runtime=runtime, mock=False, rate_limited_sources=set(), rate_limit_lock=threading.Lock(),
                x_handle="hinted", x_related=["related"],
            )
        search.assert_not_called()


if __name__ == "__main__":
    unittest.main()
