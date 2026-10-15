"""Offline ledger invariants adapted from the audited last30days accounting."""
import json
import multiprocessing
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import costs

URL = "https://api.aisa.one/apis/v1/twitter/tweet/advanced_search?query=synthetic"
HEADERS = {"Authorization": "Bearer <fixture-only>"}


def quote(amount=100_000, variable=False, **overrides):
    return costs.Response(200, {}, json.dumps({"object": "cost_estimate", "estimated_cost_micros_usd": amount,
                          "may_exceed_estimate": variable, **overrides}).encode())


def response(amount="100000", status=200):
    return costs.Response(status, {} if amount is None else {"X-AISA-Customer-Cost-Micros-USD": amount}, b'{}')


def _process_spend(path, start, results):
    budget = costs.RunBudget(path)
    start.wait(5)
    def send(headers):
        if "X-AISA-Cost-Mode" in headers:
            return quote(70_000)
        time.sleep(0.02)
        return response("70000")
    try:
        budget.request("GET", URL, HEADERS, None, send)
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
        def send(values):
            seen.append(values)
            value = next(replies)
            if isinstance(value, Exception):
                raise value
            return value
        result = budget.request("GET", URL, headers or HEADERS, None, send)
        return result, seen

    def test_provider_request_header_cannot_persist_an_echoed_key(self):
        reply = response()
        reply.headers["X-Request-ID"] = "upstream-prefix " + HEADERS["Authorization"]
        self.call(self.budget(), [quote(), reply])
        ledger = self.path.read_text()
        self.assertNotIn("fixture-only", ledger)
        self.assertEqual(json.loads(ledger)["requests"][0]["provider_request_id"], "upstream-prefix [redacted]")

    def test_exact_money_and_rejections(self):
        self.assertEqual(costs.parse_usd("12345678901234567890.123456"), 12345678901234567890123456)
        self.assertEqual(costs.parse_usd("0.000001"), 1)
        self.assertEqual(costs.usd_text(1234567), "1.234567")
        for value in ("-1", "1e-3", "NaN", "inf", "0.0000001", ".1", "1.", " 1", True, 0.1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                costs.parse_usd(value)

    def test_immutable_budget_and_reopen(self):
        with self.assertRaises(costs.CostControlError):
            costs.RunBudget(self.path)
        self.budget()
        self.assertEqual(costs.RunBudget(self.path).summary()["budget_micros_usd"], 1_000_000)
        with self.assertRaises(costs.CostControlError):
            self.budget(2_000_000)

    def test_malformed_quotes_and_limit_rejections_never_dispatch(self):
        malformed = [quote(True), quote(-1), quote(0.1), quote(100_000, object="other"),
                     quote(100_000, may_exceed_estimate="false"), costs.Response(200, {}, b"[]"),
                     costs.Response(500, {}, quote().body), costs.Response(200, {}, b'\xff'),
                     costs.Response(200, {}, quote().body, read_error="truncated"),
                     quote(success=False), quote(error="synthetic provider error")]
        for bad in malformed:
            with self.subTest(body=bad.body), self.assertRaises(costs.CostControlError):
                self.call(self.budget(), [bad])
            self.assertEqual(self.budget().summary()["request_count"], 0)
        with self.assertRaises(costs.CostControlError):
            self.call(self.budget(), [quote(2_000_000)])
        self.assertEqual(self.budget().summary()["request_count"], 0)

    def test_variable_quote_needs_acceptance_and_actual_overshoot_is_retained(self):
        budget = self.budget(200_000)
        with self.assertRaises(costs.CostControlError):
            self.call(budget, [quote(50_000, True)])
        budget = self.budget(200_000, allow_variable_cost=True)
        self.call(budget, [quote(50_000, True), response("250000")])
        summary = budget.summary()
        self.assertEqual(summary["spent_micros_usd"], 250_000)
        self.assertTrue(summary["budget_exceeded"])
        self.assertEqual(summary["remaining_micros_usd"], 0)
        with self.assertRaises(costs.CostControlError):
            self.call(budget, [])

    def test_pending_record_durable_before_execution_and_no_secrets_stored(self):
        budget = self.budget()
        def send(headers):
            if "X-AISA-Cost-Mode" in headers:
                return quote()
            ledger = json.loads(self.path.read_text())
            record = ledger["requests"][0]
            self.assertEqual(record["outcome"], "pending")
            self.assertIsNone(record["cost_micros_usd"])
            self.assertEqual(record["request_id"], headers["Idempotency-Key"])
            self.assertEqual(headers["X-AISA-Max-Price-USD"], "1.000000")
            return response()
        budget.request("GET", URL + "&api_key=fixture-only", HEADERS, b'{"aisa_api_key":"fixture-only"}', send)
        self.assertNotIn("fixture-only", self.path.read_text())
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_timeout_unknown_blocks_reopened_ledger(self):
        budget = self.budget()
        with self.assertRaises(costs.CostControlError):
            self.call(budget, [quote(), TimeoutError("fixture")])
        self.assertEqual(budget.summary()["request_count"], 1)
        self.assertIsNone(budget.summary()["spent_micros_usd"])
        with self.assertRaises(costs.CostControlError):
            self.call(costs.RunBudget(self.path), [])

    def test_unknown_header_reconciliation_uses_explicit_evidence(self):
        budget = self.budget()
        self.call(budget, [quote(), response(None)])
        self.assertEqual(budget.summary()["known_cost_micros_usd"], 0)
        self.assertIsNone(budget.summary()["run_cost_micros_usd"])
        request_id = budget.summary()["unknown_requests"][0]
        with self.assertRaises(costs.CostControlError):
            self.call(budget, [])
        with self.assertRaises(costs.CostControlError):
            costs.reconcile(self.path, request_id, 25_000, "")
        costs.reconcile(self.path, request_id, 25_000, "SYNTHETIC TEST request-specific provider log")
        self.call(budget, [quote(), response()])
        self.assertEqual(budget.summary()["spent_micros_usd"], 125_000)

    def test_invalid_cost_headers_remain_unknown(self):
        for header in ("-1", "NaN", "0.1", "True"):
            with self.subTest(header=header):
                budget = costs.RunBudget(Path(self.temp.name) / (header + ".json"), 1_000_000)
                self.call(budget, [quote(), response(header)])
                self.assertIsNone(budget.summary()["spent_micros_usd"])

    def test_same_idempotency_key_is_not_redispatched(self):
        budget = self.budget()
        headers = {**HEADERS, "Idempotency-Key": "fixture-stable-request"}
        self.call(budget, [quote(), response()], headers)
        with self.assertRaises(costs.CostControlError):
            self.call(budget, [quote()], headers)
        self.assertEqual(budget.summary()["request_count"], 1)

    def test_two_budget_objects_share_lock(self):
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
                budget.request("GET", URL, HEADERS, None, send)
                return "paid"
            except costs.CostControlError:
                return "refused"
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(worker, budgets))
        self.assertCountEqual(outcomes, ["paid", "refused"])
        self.assertEqual(len(paid), 1)
        self.assertEqual(budgets[0].summary()["spent_micros_usd"], 70_000)

    def test_processes_share_durable_lock(self):
        self.budget(100_000)
        context = multiprocessing.get_context("spawn")
        start, results = context.Event(), context.Queue()
        processes = [context.Process(target=_process_spend, args=(self.path, start, results)) for _ in range(2)]
        for process in processes:
            process.start()
        start.set()
        outcomes = [results.get(timeout=10) for _ in processes]
        for process in processes:
            process.join(10)
            self.assertEqual(process.exitcode, 0)
        self.assertCountEqual(outcomes, ["paid", "refused"])
        self.assertEqual(costs.ledger_summary(self.path)["spent_micros_usd"], 70_000)

    def test_run_attribution_separate_from_cumulative_charge(self):
        first, second = self.budget(), self.budget()
        self.call(first, [quote(), response("30000")])
        self.call(second, [quote(), response("70000")])
        self.assertEqual(first.summary()["spent_micros_usd"], 100_000)
        self.assertEqual(first.summary()["run_cost_micros_usd"], 30_000)
        self.assertEqual(second.summary()["run_cost_micros_usd"], 70_000)


if __name__ == "__main__":
    unittest.main()
