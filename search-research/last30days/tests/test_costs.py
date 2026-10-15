"""Offline request-boundary tests: no credentials or network are used."""

from http.client import IncompleteRead
import json
import multiprocessing
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lib import costs, http


URL = "https://api.aisa.one/apis/v1/tavily/search"
HEADERS = {"Authorization": "Bearer <fixture-only>"}


def quote(amount=100_000, variable=False, **overrides):
    payload = {"object": "cost_estimate", "estimated_cost_micros_usd": amount,
               "may_exceed_estimate": variable, **overrides}
    return costs.Response(200, {}, json.dumps(payload).encode())


def response(amount="100000", body=b'{"results": []}', status=200):
    return costs.Response(status, {"X-AISA-Customer-Cost-Micros-USD": amount} if amount is not None else {}, body)


class FakeHTTPResponse:
    def __init__(self, payload, *, failure=None):
        self.status, self.headers, self.body = payload.status, payload.headers, payload.body
        self.failure = failure

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        if self.failure:
            raise self.failure
        return self.body


def _process_spend(path, start, results):
    budget = costs.RunBudget(path)
    start.wait(5)

    def send(headers):
        if "X-AISA-Cost-Mode" in headers:
            return quote(70_000)
        time.sleep(0.02)
        return response("70000")

    try:
        budget.request("POST", URL, HEADERS, b"{}", send)
        results.put("paid")
    except costs.CostControlError:
        results.put("refused")


class CostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "ledger.json"

    def budget(self, amount=1_000_000, **kwargs):
        return costs.RunBudget(self.path, amount, **kwargs)

    def call(self, budget, replies, headers=None):
        replies = iter(replies)
        seen = []

        def send(hdrs):
            seen.append(hdrs)
            item = next(replies)
            if isinstance(item, Exception):
                raise item
            return item

        result = budget.request("POST", URL, headers or HEADERS, b'{"query":"test"}', send)
        return result, seen

    def test_exact_money_and_rejection(self):
        self.assertEqual(costs.parse_usd("12345678901234567890.123456"), 12345678901234567890123456)
        self.assertEqual(costs.parse_usd("0.000001"), 1)
        self.assertEqual(costs.usd_text(1234567), "1.234567")
        for value in ("-1", "1e-3", "NaN", "inf", "0.0000001", ".1", "1.", " 1", True, 0.1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                costs.parse_usd(value)

    def test_no_budget_means_no_network(self):
        with patch.object(http, "_open_aisa") as network:
            with self.assertRaises(costs.CostControlError):
                http.post(URL, {"query": "test"}, headers=HEADERS)
            network.assert_not_called()

    def test_new_ledger_needs_budget_and_existing_budget_is_immutable(self):
        with self.assertRaises(costs.CostControlError):
            costs.RunBudget(self.path)
        self.budget()
        self.assertEqual(costs.RunBudget(self.path).summary()["budget_micros_usd"], 1_000_000)
        with self.assertRaises(costs.CostControlError):
            self.budget(2_000_000)

    def test_quote_rejections_never_dispatch(self):
        malformed = [quote(True), quote(-1), quote(0.1), quote(100_000, object="other"),
                     quote(100_000, may_exceed_estimate="false"), costs.Response(200, {}, b"[]"),
                     costs.Response(500, {}, quote().body)]
        for bad in malformed:
            with self.subTest(bad=bad.body), self.assertRaises(costs.CostControlError):
                self.call(self.budget(), [bad])
            self.assertEqual(self.budget().summary()["request_count"], 0)

    def test_variable_quotes_require_explicit_acceptance(self):
        with self.assertRaises(costs.CostControlError):
            self.call(self.budget(), [quote(variable=True)])
        self.call(self.budget(allow_variable_cost=True), [quote(variable=True), response()])
        self.assertEqual(self.budget().summary()["spent_micros_usd"], 100_000)

    def test_over_budget_quote_is_not_dispatched(self):
        with self.assertRaises(costs.CostControlError):
            self.call(self.budget(99_999), [quote(100_000)])
        self.assertEqual(costs.ledger_summary(self.path)["request_count"], 0)

    def test_exact_request_quoted_pending_record_precedes_dispatch(self):
        budget = self.budget()
        seen = []

        def open_request(req, timeout):
            seen.append((req.method, req.full_url, req.data, dict(req.header_items())))
            if len(seen) == 1:
                return FakeHTTPResponse(quote())
            ledger = json.loads(self.path.read_text())
            record = ledger["requests"][0]
            self.assertEqual(record["outcome"], "pending")
            self.assertIsNone(record["cost_micros_usd"])
            self.assertEqual(record["request_id"], req.get_header("Idempotency-key"))
            return FakeHTTPResponse(response())

        with costs.activate(budget), patch.object(http, "_open_aisa", side_effect=open_request):
            self.assertEqual(http.post(URL, {"query": "exact topic"}, headers=HEADERS), {"results": []})
        self.assertEqual(seen[0][:3], seen[1][:3])
        self.assertEqual(seen[0][3]["X-aisa-cost-mode"], "quote")
        self.assertNotIn("X-aisa-cost-mode", seen[1][3])
        self.assertEqual(seen[1][3]["X-aisa-max-price-usd"], "1.000000")
        self.assertNotIn("fixture-only", self.path.read_text())
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_timeout_is_one_paid_dispatch_and_blocks_reopened_ledger(self):
        budget = self.budget()
        with costs.activate(budget), patch.object(http, "_open_aisa", side_effect=[FakeHTTPResponse(quote()), TimeoutError()]) as network:
            with self.assertRaises(costs.CostControlError):
                http.post(URL, {"query": "test"}, headers=HEADERS)
            self.assertEqual(network.call_count, 2)  # One free quote, one paid attempt.
        self.assertIsNone(budget.summary()["spent_micros_usd"])
        with self.assertRaises(costs.CostControlError):
            self.call(costs.RunBudget(self.path), [])

    def test_unknown_header_blocks_until_evidence_reconciliation(self):
        budget = self.budget()
        self.call(budget, [quote(), response(None)])
        self.assertEqual(budget.summary()["known_cost_micros_usd"], 0)
        self.assertIsNone(budget.summary()["run_cost_micros_usd"])
        request_id = budget.summary()["unknown_requests"][0]
        with self.assertRaises(costs.CostControlError):
            self.call(budget, [])
        with self.assertRaises(costs.CostControlError):
            costs.reconcile(self.path, request_id, 25_000, "")
        costs.reconcile(self.path, request_id, 25_000, "Provider log request abc: charged 25000 micro-USD")
        self.call(budget, [quote(), response()])
        self.assertEqual(budget.summary()["spent_micros_usd"], 125_000)

    def test_invalid_cost_header_is_unknown_not_zero(self):
        for header in ("-1", "NaN", "0.1", "True"):
            with self.subTest(header=header):
                path = Path(self.temp.name) / (header.replace(".", "_") + ".json")
                budget = costs.RunBudget(path, 1_000_000)
                self.call(budget, [quote(), response(header)])
                self.assertIsNone(budget.summary()["spent_micros_usd"])

    def test_actual_cost_not_estimate_is_deducted_and_overshoot_is_visible(self):
        budget = self.budget(200_000, allow_variable_cost=True)
        self.call(budget, [quote(50_000, True), response("250000")])
        summary = budget.summary()
        self.assertEqual(summary["spent_micros_usd"], 250_000)
        self.assertTrue(summary["budget_exceeded"])
        self.assertEqual(summary["remaining_micros_usd"], 0)
        with self.assertRaises(costs.CostControlError):
            self.call(budget, [])

    def test_known_cost_survives_truncated_and_malformed_response(self):
        for failure, body in ((IncompleteRead(b"partial", 10), b""), (None, b"not json")):
            with self.subTest(failure=failure):
                path = Path(self.temp.name) / ("partial.json" if failure else "malformed.json")
                budget = costs.RunBudget(path, 1_000_000)
                with costs.activate(budget), patch.object(http, "_open_aisa", side_effect=[
                        FakeHTTPResponse(quote()), FakeHTTPResponse(response("12345", body), failure=failure)]):
                    with self.assertRaises(http.HTTPError) as caught:
                        http.post(URL, {"query": "test"}, headers=HEADERS)
                    self.assertFalse(caught.exception.retryable)
                self.assertEqual(budget.summary()["spent_micros_usd"], 12_345)

    def test_http_error_charge_is_retained_without_retry(self):
        budget = self.budget()
        with costs.activate(budget), patch.object(http, "_open_aisa", side_effect=[
                FakeHTTPResponse(quote()), FakeHTTPResponse(response("75000", status=503))]) as network:
            with self.assertRaises(http.HTTPError) as caught:
                http.post(URL, {"query": "test"}, headers=HEADERS)
            self.assertFalse(caught.exception.retryable)
            self.assertEqual(network.call_count, 2)
        self.assertEqual(budget.summary()["spent_micros_usd"], 75_000)

    def test_same_idempotency_key_cannot_be_redispatched(self):
        budget = self.budget()
        headers = {**HEADERS, "Idempotency-Key": "stable-request"}
        self.call(budget, [quote(), response()], headers)
        with self.assertRaises(costs.CostControlError):
            self.call(budget, [quote()], headers)
        self.assertEqual(budget.summary()["request_count"], 1)

    def test_two_budget_objects_share_file_lock_and_cannot_overspend(self):
        budgets = [self.budget(100_000), self.budget(100_000)]
        barrier = threading.Barrier(2)
        paid = []

        def worker(budget):
            barrier.wait()

            def send(headers):
                if "X-AISA-Cost-Mode" in headers:
                    return quote(70_000)
                paid.append(headers)
                time.sleep(0.02)
                return response("70000")

            try:
                budget.request("POST", URL, HEADERS, b"{}", send)
                return "paid"
            except costs.CostControlError:
                return "refused"

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(worker, budgets))
        self.assertCountEqual(outcomes, ["paid", "refused"])
        self.assertEqual(len(paid), 1)
        self.assertEqual(budgets[0].summary()["spent_micros_usd"], 70_000)

    def test_run_attribution_does_not_include_other_invocations(self):
        a, b = self.budget(), self.budget()
        self.call(a, [quote(), response("30000")])
        self.call(b, [quote(), response("70000")])
        self.assertEqual(a.summary()["spent_micros_usd"], 100_000)
        self.assertEqual(a.summary()["run_cost_micros_usd"], 30_000)
        self.assertEqual(costs.run_summary(self.path, b.run_id)["run_cost_micros_usd"], 70_000)

    def test_separate_processes_cannot_admit_against_the_same_remaining_budget(self):
        budget = self.budget(100_000)
        context = multiprocessing.get_context("fork")
        start, results = context.Event(), context.Queue()
        processes = [context.Process(target=_process_spend, args=(self.path, start, results)) for _ in range(2)]
        try:
            for process in processes:
                process.start()
            start.set()
            outcomes = [results.get(timeout=5) for _ in processes]
            for process in processes:
                process.join(timeout=5)
                self.assertEqual(process.exitcode, 0)
            self.assertCountEqual(outcomes, ["paid", "refused"])
            self.assertEqual(budget.summary()["spent_micros_usd"], 70_000)
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)
            results.close()

    def test_only_explicit_free_catalog_path_bypasses_budget(self):
        with patch.object(http, "_open_aisa", return_value=FakeHTTPResponse(costs.Response(200, {}, b"{}"))) as network:
            self.assertEqual(http.get("https://api.aisa.one/v1/models", headers=HEADERS), {})
            self.assertEqual(network.call_count, 1)
        for url in ("https://api.aisa.one/v1/models?query=x", "https://api.aisa.one/v1/anything"):
            with self.assertRaises(costs.CostControlError), patch.object(http, "_open_aisa") as network:
                http.get(url, headers=HEADERS)
            network.assert_not_called()

    def test_undeclared_quote_capability_is_refused_before_network(self):
        budget = self.budget()
        with costs.activate(budget), patch.object(http, "_open_aisa") as network:
            with self.assertRaisesRegex(costs.CostControlError, "no verified free-quote"):
                http.post("https://api.aisa.one/v1/chat/completions", {"model": "fixture"}, headers=HEADERS)
            network.assert_not_called()

    def test_authenticated_redirects_are_not_followed(self):
        handler = http._NoAIsaRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, "redirect", {}, "https://other.example/"))


if __name__ == "__main__":
    unittest.main()
