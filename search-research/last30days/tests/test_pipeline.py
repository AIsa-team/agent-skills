"""Integration invariants for source coverage, dispatch and reported evidence."""
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lib import http, pipeline, providers, render, schema, signals


def plan(source="x", queries=("alpha", "beta")):
    return {"intent": "comparison", "freshness_mode": "strict_recent", "cluster_mode": "debate",
            "subqueries": [{"label": str(i), "search_query": q, "ranking_query": q,
                            "sources": [source]} for i, q in enumerate(queries)],
            "source_weights": {source: 1.0}}


def tweet():
    return {"id": "one", "text": "alpha beta research", "url": "https://x.com/example/status/1",
            "date": datetime.now(timezone.utc).date().isoformat(), "author_handle": "example",
            "engagement": {"likes": 12}, "relevance": .9}


class PipelineTests(unittest.TestCase):
    def run_pipeline(self, source="x", queries=("alpha", "beta"), side_effect=None, requested=None):
        with ExitStack() as stack:
            stack.enter_context(patch.object(pipeline.providers, "resolve_runtime", return_value=(providers.mock_runtime({}, "quick"), None)))
            stack.enter_context(patch.object(pipeline, "available_sources", return_value=[source]))
            stack.enter_context(patch.object(pipeline, "_run_supplemental_searches"))
            stack.enter_context(patch.object(pipeline, "_retry_thin_sources"))
            retrieve = stack.enter_context(patch.object(pipeline, "_retrieve_stream", side_effect=side_effect))
            report = pipeline.run(topic="alpha versus beta", config={}, depth="default",
                                  requested_sources=requested or [source], external_plan=plan(source, queries))
        return report, retrieve

    def test_partial_failure_retains_success_and_failure_evidence(self):
        def retrieve(**kw):
            if kw["subquery"].search_query == "beta":
                raise http.HTTPError("503 upstream", 503, retryable=False)
            return [tweet()], {}
        report, retrieve = self.run_pipeline(side_effect=retrieve)
        self.assertEqual(retrieve.call_count, 2)
        self.assertEqual(len(report.items_by_source["x"]), 1)
        self.assertIn("x", report.errors_by_source)
        self.assertEqual(report.artifacts["source_coverage"]["x"]["status"], "partial")
        self.assertIn("partial", render.render_compact(report))

    def test_paid_http_failure_is_not_automatically_redispatched(self):
        report, retrieve = self.run_pipeline(queries=("alpha",), side_effect=http.HTTPError("503 admitted failure", 503, retryable=False))
        self.assertEqual(retrieve.call_count, 1)
        self.assertEqual(report.artifacts["source_coverage"]["x"]["status"], "failed")
        self.assertIn("No source returned usable items.", report.warnings)

    def test_identical_requests_dispatched_once(self):
        report, retrieve = self.run_pipeline(queries=("alpha", "alpha"), side_effect=lambda **kw: ([tweet()], {}))
        self.assertEqual(retrieve.call_count, 1)
        self.assertEqual(len(report.ranked_candidates), 1)

    def test_unavailable_requested_source_is_reported(self):
        report, _ = self.run_pipeline(queries=("alpha",), requested=["x", "youtube"], side_effect=lambda **kw: ([tweet()], {}))
        self.assertEqual(report.artifacts["source_coverage"]["youtube"]["status"], "unavailable")
        self.assertTrue(any("youtube" in warning for warning in report.warnings))

    def test_planned_queries_reach_youtube_adapter(self):
        runtime = providers.mock_runtime({}, "quick")
        import threading
        with patch.object(pipeline.youtube_yt, "search_and_transcribe", return_value={"items": []}) as search:
            for query in ("alpha", "beta"):
                pipeline._retrieve_stream(topic="alpha vs beta", raw_topic="alpha vs beta",
                    subquery=schema.SubQuery(query, query, query, ["youtube"]), source="youtube", config={},
                    depth="quick", date_range=("2026-09-15", "2026-10-15"), runtime=runtime, mock=False,
                    rate_limited_sources=set(), rate_limit_lock=threading.Lock())
        self.assertEqual([c.args[0] for c in search.call_args_list], ["alpha", "beta"])

    def test_invalid_window_rejected_before_runtime(self):
        with patch.object(pipeline.providers, "resolve_runtime") as resolve:
            for days in (0, -1, 366):
                with self.assertRaises(ValueError):
                    pipeline.run(topic="alpha", config={}, depth="quick", lookback_days=days)
            resolve.assert_not_called()

    def test_explicit_source_restriction_cannot_be_expanded_by_web_backend(self):
        with self.assertRaisesRegex(ValueError, "source restriction"):
            pipeline.run(topic="alpha", config={}, depth="quick", mock=True,
                         requested_sources=["reddit"], web_backend="aisa")

    def test_mock_pipeline_has_no_network(self):
        with patch.object(http, "request", side_effect=AssertionError("network forbidden")):
            report=pipeline.run(topic="alpha", config={}, depth="default", mock=True)
        self.assertTrue(report.ranked_candidates)
        self.assertEqual(set(report.items_by_source), {"reddit", "x", "grounding"})

    def test_market_observation_is_not_rendered_as_publication(self):
        item=schema.SourceItem("pm", "polymarket", "market", "market", "https://polymarket.com/event/test",
            metadata={"date_kind": "market_observation", "observed_at": datetime.now(timezone.utc).isoformat()})
        self.assertGreater(signals.freshness(item, "strict_recent"), 0)
        self.assertIn("current market snapshot", render._format_date(item))
        self.assertIsNone(item.published_at)

    def test_cost_output_does_not_call_unknown_charges_zero(self):
        report, _ = self.run_pipeline(queries=("alpha",), side_effect=lambda **kw: ([tweet()], {}))
        report.artifacts["costs"]={"known_cost_micros_usd":125000, "spent_micros_usd":None,
            "unknown_requests":["request-a"], "ledger_path":"/tmp/ledger.json"}
        for renderer in (render.render_compact, render.render_full, render.render_context):
            output=renderer(report)
            self.assertIn("$0.125000", output)
            self.assertIn("Unresolved requests: 1", output)
            self.assertIn("final charges can exceed", output)


if __name__ == "__main__":
    unittest.main()
