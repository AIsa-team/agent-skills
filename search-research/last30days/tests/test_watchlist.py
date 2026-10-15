"""Offline durable daily-budget and SQLite reporting regressions."""

import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import store
import watchlist
from lib import costs


def dispatch(budget, amount=None, estimate=50_000):
    def send(headers):
        if "X-AISA-Cost-Mode" in headers:
            return costs.Response(200, {}, json.dumps({
                "object": "cost_estimate", "estimated_cost_micros_usd": estimate,
                "may_exceed_estimate": False,
            }).encode())
        return costs.Response(200, {} if amount is None else {
            "x-aisa-customer-cost-micros-usd": str(amount)}, b"{}")
    return budget.request("POST", "https://api.aisa.one/apis/v1/tavily/search", {}, b"{}", send)


class WatchlistTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.patch = patch.object(store, "_db_override", Path(self.temp.name) / "research.db")
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.day = patch.object(costs, "utc_day", return_value="2026-10-15")
        self.day.start()
        self.addCleanup(self.day.stop)
        store.init_db()
        self.args = argparse.Namespace(budget_usd=None, allow_variable_cost=False)

    def authorize(self, amount="1.00"):
        with redirect_stdout(io.StringIO()):
            watchlist.cmd_config(argparse.Namespace(key="budget", value=amount))

    def test_old_automatic_budget_is_not_authorization(self):
        store.set_setting("daily_budget", "5.00")
        with self.assertRaises(costs.CostControlError):
            watchlist._daily_budget(self.args)
        self.assertIsNone(watchlist._daily_state()["budget_micros_usd"])
        self.authorize()
        self.assertEqual(watchlist._daily_budget(self.args).summary()["budget_micros_usd"], 1_000_000)

    def test_run_argument_authorizes_without_creating_implicit_default(self):
        self.args.budget_usd = 25_000
        budget = watchlist._daily_budget(self.args)
        self.assertEqual(budget.summary()["budget_micros_usd"], 25_000)
        self.assertIsNone(store.get_setting("daily_budget_authorized"))

    def test_pending_previous_utc_day_blocks_new_spending_until_reconciled(self):
        self.authorize()
        yesterday = watchlist._ledger_dir() / "2026-10-14.json"
        old = costs.RunBudget(yesterday, 1_000_000, period="2026-10-14")
        dispatch(old)
        with self.assertRaisesRegex(costs.CostControlError, "Unresolved watchlist"):
            watchlist._daily_budget(self.args)
        self.assertEqual(len(watchlist._daily_state()["unresolved_ledgers"]), 1)
        request_id = old.summary()["unknown_requests"][0]
        costs.reconcile(yesterday, request_id, 10_000, "Request-specific provider invoice record")
        current = watchlist._daily_budget(self.args)
        self.assertEqual(current.summary()["period"], "2026-10-15")
        self.assertEqual(current.summary()["spent_micros_usd"], 0)

    def test_known_previous_day_does_not_consume_current_daily_budget(self):
        self.authorize("0.10")
        old = costs.RunBudget(watchlist._ledger_dir() / "2026-10-14.json", 100_000, period="2026-10-14")
        dispatch(old, amount=100_000)
        current = watchlist._daily_budget(self.args)
        self.assertEqual(current.summary()["remaining_micros_usd"], 100_000)

    def test_sqlite_unknown_is_not_summed_as_zero(self):
        topic = store.add_topic("fixture")
        run_id = store.record_run(topic["id"])
        self.assertIsNone(store.get_daily_cost())
        self.assertIsNone(store.get_stats()["cost_7d"])
        store.update_run(run_id, cost_micros_usd=123_456)
        self.assertEqual(store.get_daily_cost(), 0.123456)
        self.assertEqual(store.get_stats()["cost_7d"], 0.123456)

    def test_paid_child_actual_cost_persists_even_if_child_exits_nonzero(self):
        self.authorize()
        budget = watchlist._daily_budget(self.args)
        topic = store.add_topic("fixture")
        commands = []

        def child(command, **kwargs):
            commands.append(command)
            child_budget = costs.RunBudget(budget.path, run_id=kwargs["env"]["LAST30DAYS_COST_RUN_ID"])
            dispatch(child_budget, amount=12_345)
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="fixture failure")

        with patch.object(watchlist.subprocess, "run", side_effect=child):
            result = watchlist._run_topic(topic, budget)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["costs"]["run_cost_micros_usd"], 12_345)
        self.assertEqual(store.get_daily_cost(), 0.012345)
        self.assertIn("--cost-ledger", commands[0])
        self.assertEqual(commands[0][commands[0].index("--budget-usd") + 1], "1.000000")

    def test_child_timeout_keeps_unknown_and_blocks_later_topics(self):
        self.authorize()
        budget = watchlist._daily_budget(self.args)
        topic = store.add_topic("fixture")

        def child(command, **kwargs):
            child_budget = costs.RunBudget(budget.path, run_id=kwargs["env"]["LAST30DAYS_COST_RUN_ID"])
            dispatch(child_budget)
            raise subprocess.TimeoutExpired(command, 300)

        with patch.object(watchlist.subprocess, "run", side_effect=child):
            result = watchlist._run_topic(topic, budget)
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["costs"]["run_cost_micros_usd"])
        self.assertIsNone(store.get_daily_cost())
        with self.assertRaises(costs.CostControlError):
            watchlist._daily_budget(self.args)

    def test_run_all_stops_after_reported_actual_overshoot(self):
        self.authorize("0.10")
        store.add_topic("one")
        store.add_topic("two")

        def child(command, **kwargs):
            path = command[command.index("--cost-ledger") + 1]
            child_budget = costs.RunBudget(path, run_id=kwargs["env"]["LAST30DAYS_COST_RUN_ID"])
            dispatch(child_budget, amount=110_000)
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="fixture failure")

        output = io.StringIO()
        with patch.object(watchlist.subprocess, "run", side_effect=child) as run, redirect_stdout(output):
            watchlist.cmd_run_all(self.args)
        result = json.loads(output.getvalue())
        self.assertEqual(run.call_count, 1)
        self.assertEqual([row["status"] for row in result["results"]], ["failed", "skipped"])
        self.assertEqual(result["costs"]["spent_micros_usd"], 110_000)

    def test_invalid_config_budget_does_not_authorize(self):
        for value in ("NaN", "-5", "0.0000001"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                watchlist.cmd_config(argparse.Namespace(key="budget", value=value))
        self.assertIsNone(store.get_setting("daily_budget_authorized"))


if __name__ == "__main__":
    unittest.main()
