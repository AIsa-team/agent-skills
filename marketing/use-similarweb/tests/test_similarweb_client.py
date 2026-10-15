"""Offline regression tests; no API key or network access is required.

Run: python3 -m unittest discover -s marketing/use-similarweb/tests -v
"""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from decimal import Decimal
from http.client import HTTPException, IncompleteRead


SKILL = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "similarweb_client", SKILL / "scripts" / "similarweb_client.py"
)
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)
LOAD_CONTRACT = client.load_contract
FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "contract-2026-10-15.json").read_text())
TRAFFIC = "/website/traffic-engagement"
TECHNOLOGIES = "/website/technologies"
TRAFFIC_PARAMS = {
    "domain": "example.com",
    "start_date": "2026-09",
    "end_date": "2026-09",
    "metrics": "visits",
}


class ClientTestCase(unittest.TestCase):
    def setUp(self):
        self.contract = copy.deepcopy(FIXTURE)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        cache = mock.patch.object(client, "CACHE", Path(self.temp.name) / "cache")
        cache.start()
        self.addCleanup(cache.stop)
        contract = mock.patch.object(client, "load_contract", return_value=self.contract)
        self.load_contract = contract.start()
        self.addCleanup(contract.stop)
        network = mock.patch.object(client, "http", side_effect=AssertionError("unexpected HTTP request"))
        self.http = network.start()
        self.addCleanup(network.stop)

    def run_cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(client.sys, "argv", ["similarweb_client.py", *args]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    client.main()
                    code = 0
                except SystemExit as exc:
                    code = exc.code
        return code, stdout.getvalue(), stderr.getvalue()

    def run_json(self, *args):
        code, stdout, stderr = self.run_cli(*args)
        self.assertTrue(stdout.strip(), f"No JSON output; exit={code!r}, stderr={stderr!r}")
        return code, json.loads(stdout)

    def traffic_args(self):
        return [f"{key}={value}" for key, value in TRAFFIC_PARAMS.items()]


class ContractCompatibilityTests(ClientTestCase):
    def test_unknown_route_refreshes_contract_once_before_validation(self):
        stale = copy.deepcopy(self.contract)
        del stale["paths"]["/apis/v1/similarweb" + TRAFFIC]
        self.load_contract.side_effect = [stale, self.contract]
        code, result = self.run_json("check", TRAFFIC, *self.traffic_args())
        self.assertEqual(code, 0)
        self.assertTrue(result["valid"])
        self.assertEqual(self.load_contract.call_args_list, [mock.call(), mock.call(refresh=True)])
        self.http.assert_not_called()

    def test_corrupt_contract_cache_is_replaced_by_public_fetch(self):
        client.CACHE.mkdir(parents=True)
        (client.CACHE / "contract.json").write_text("{broken json")
        (client.CACHE / "contract.meta.json").write_text("{also broken")
        self.http.side_effect = None
        self.http.return_value = (200, {"cache-control": "max-age=3600"}, self.contract)
        with contextlib.redirect_stderr(io.StringIO()):
            restored = LOAD_CONTRACT()
        self.assertEqual(restored, self.contract)
        self.http.assert_called_once_with(client.CONTRACT_URL, {}, auth=False)
        self.assertEqual(json.loads((client.CACHE / "contract.json").read_text()), self.contract)
        self.assertEqual(json.loads((client.CACHE / "contract.meta.json").read_text())["max_age"], 3600)

    def test_current_routes_accept_all_documented_aliases(self):
        expected = "/apis/v1/similarweb" + TRAFFIC
        for alias in (TRAFFIC, TRAFFIC.lstrip("/"), "/similarweb" + TRAFFIC, expected):
            with self.subTest(alias=alias):
                path, _ = client.get_op(self.contract, alias)
                self.assertEqual(path, expected)
        self.assertEqual(set(client.ops(self.contract)), {TRAFFIC, TECHNOLOGIES, "/search/website-keywords"})

    def test_old_and_current_contract_urls_have_one_prefix(self):
        for server, path in (
            ("https://api.aisa.one", "/apis/v1/similarweb" + TRAFFIC),
            ("https://api.aisa.one/apis/v1", "/similarweb" + TRAFFIC),
        ):
            with self.subTest(server=server, path=path):
                spec = {"servers": [{"url": server}], "paths": {path: {"get": {"summary": "Example"}}}}
                resolved, _ = client.get_op(spec, TRAFFIC)
                url = client.build_url(spec, resolved, {"domain": "example.com"})
                self.assertEqual(url, "https://api.aisa.one/apis/v1/similarweb" + TRAFFIC + "?domain=example.com")

    def test_describe_preserves_constraints_parameter_examples_and_responses(self):
        code, result = self.run_json("describe", TECHNOLOGIES)
        self.assertEqual(code, 0)
        _, op = client.get_op(self.contract, TECHNOLOGIES)
        self.assertEqual(result["constraints"], op["x-aisa-constraints"])
        self.assertEqual(result["responses"], op["responses"])
        required = {p["name"]: p for p in result["required"]}
        self.assertEqual(required["domain"]["examples"]["minimal"]["value"], "example.com")
        self.assertEqual(required["limit"]["schema"], {"minimum": 1, "maximum": 20, "type": "integer"})
        self.assertEqual(result["url"], "https://api.aisa.one/apis/v1/similarweb" + TECHNOLOGIES)
        self.assertTrue(result["response_definitions"])

    def test_valid_current_request_and_explicit_false_are_accepted(self):
        code, result = self.run_json("check", TRAFFIC, *self.traffic_args(), "main_domain_only=false")
        self.assertEqual(code, 0)
        self.assertTrue(result["valid"])
        self.http.assert_not_called()

    def test_schema_lengths_booleans_enums_and_delimited_counts_are_checked(self):
        _, op = client.get_op(self.contract, TRAFFIC)
        invalid = {
            "empty domain": {"domain": ""},
            "too long domain": {"domain": "a" * 254},
            "invalid boolean": {"main_domain_only": "banana"},
            "invalid enum": {"web_source": "phone"},
            "empty metrics": {"metrics": ""},
            "too many metrics": {"metrics": ",".join("metric" + str(i) for i in range(9))},
            "unknown parameter": {"not_a_parameter": "value"},
        }
        for label, override in invalid.items():
            with self.subTest(case=label):
                self.assertTrue(client.check_request(op, dict(TRAFFIC_PARAMS, **override)))
        for metrics in ("visits", ",".join("metric" + str(i) for i in range(8))):
            with self.subTest(valid_metrics=metrics):
                self.assertEqual(client.check_request(op, dict(TRAFFIC_PARAMS, metrics=metrics)), [])

    def test_live_integer_minimum_maximum_and_syntax(self):
        _, op = client.get_op(self.contract, TECHNOLOGIES)
        params = dict(TRAFFIC_PARAMS)
        del params["metrics"]
        params["granularity"] = "monthly"
        for limit in ("0", "-1", "21", "1.5", "one"):
            with self.subTest(limit=limit):
                self.assertTrue(client.check_request(op, dict(params, limit=limit)))
        for limit in ("1", "20"):
            with self.subTest(limit=limit):
                self.assertEqual(client.check_request(op, dict(params, limit=limit)), [])

    def test_missing_required_parameters_are_rejected(self):
        _, op = client.get_op(self.contract, TRAFFIC)
        problems = client.check_request(op, {"domain": "example.com"})
        self.assertTrue(any("start_date" in error for error in problems))
        self.assertTrue(any("metrics" in error for error in problems))

    def test_malformed_and_duplicate_cli_parameters_fail_cleanly_before_http(self):
        for bad in (["domain"], ["=example.com"], ["domain=a.com", "domain=b.com"]):
            with self.subTest(arguments=bad):
                code, stdout, stderr = self.run_cli("check", TRAFFIC, *bad)
                self.assertNotEqual(code, 0)
                self.assertNotIn("Traceback", stdout + stderr)
                self.http.assert_not_called()

    def test_window_provides_only_an_unverified_candidate_without_authenticated_http(self):
        code, result = self.run_json("window")
        self.assertEqual(code, 0)
        self.assertIsNone(result["latest_month"])
        self.assertEqual(result["availability"], "unverified")
        self.assertRegex(result["candidate_month"], r"^\d{4}-\d{2}$")
        self.assertTrue(result["constraints"])
        self.http.assert_not_called()


class CostAndRecoveryTests(ClientTestCase):
    @staticmethod
    def quote_body(micros=75_000, may_exceed=False):
        return {
            "object": "cost_estimate",
            "estimated_cost_micros_usd": micros,
            "may_exceed_estimate": may_exceed,
        }

    def serve(self, *, quote_micros=75_000, charge="75000", status=200, paid_error=None):
        """Mock a free quote and paid request while keeping their accounting separate."""
        paid_calls = []

        def response(url, headers=None, **kwargs):
            headers = headers or {}
            if headers.get("X-AISA-Cost-Mode") == "quote":
                return 200, {}, self.quote_body(quote_micros)
            paid_calls.append((url, headers))
            if paid_error:
                raise paid_error
            response_headers = {"x-request-id": "request-test-1"}
            if charge is not None:
                response_headers["x-aisa-customer-cost-micros-usd"] = charge
            return status, response_headers, {"meta": {"last_updated": "2026-09-30"}, "data": []}

        self.http.side_effect = response
        return paid_calls

    def test_prices_use_exact_micro_usd(self):
        for value, expected in (("0", 0), ("0.000001", 1), ("0.1", 100_000), ("1.234567", 1_234_567)):
            with self.subTest(value=value):
                self.assertEqual(client.price_micros(value), expected)

    def test_invalid_budget_arguments_fail_before_any_http(self):
        for value in ("-1", "NaN", "Infinity", "0.0000001", "word"):
            with self.subTest(value=value):
                code, _, _ = self.run_cli("call", TRAFFIC, *self.traffic_args(), "--max-usd", value)
                self.assertNotEqual(code, 0)
                self.http.assert_not_called()

    def test_quotes_validate_envelope_and_integer_micros(self):
        invalid = [
            [], {}, {"object": "response", "estimated_cost_micros_usd": 75_000},
            *[self.quote_body(value) for value in (None, True, -1, 1.5, "75000")],
        ]
        self.http.side_effect = None
        for body in invalid:
            with self.subTest(body=body):
                self.http.return_value = (200, {}, body)
                self.assertFalse(client.quote_request("https://api.aisa.one/example")["ok"])
        self.http.return_value = (500, {}, self.quote_body())
        self.assertFalse(client.quote_request("https://api.aisa.one/example")["ok"])

    def test_quote_preserves_estimate_uncertainty_and_exact_micros(self):
        self.http.side_effect = None
        for may_exceed in (True, False):
            with self.subTest(may_exceed=may_exceed):
                self.http.return_value = (200, {}, self.quote_body(1, may_exceed))
                result = client.quote_request("https://api.aisa.one/example")
                self.assertTrue(result["ok"])
                self.assertEqual(result["estimated_cost_micros_usd"], 1)
                self.assertEqual(Decimal(str(result["usd"])), Decimal("0.000001"))
                self.assertIs(result["may_exceed_estimate"], may_exceed)
                self.assertEqual(self.http.call_args.args[1]["X-AISA-Cost-Mode"], "quote")

    def test_no_budget_returns_quote_without_paid_dispatch(self):
        paid = self.serve()
        code, result = self.run_json("call", TRAFFIC, *self.traffic_args())
        self.assertNotEqual(code, 0)
        self.assertTrue(result["needs_budget"])
        self.assertEqual(paid, [])
        self.assertEqual(self.http.call_count, 1)

    def test_quote_above_cap_prevents_paid_dispatch(self):
        paid = self.serve(quote_micros=75_001)
        code, result = self.run_json("call", TRAFFIC, *self.traffic_args(), "--max-usd", "0.075000")
        self.assertNotEqual(code, 0)
        self.assertTrue(result["refused"])
        self.assertEqual(paid, [])

    def test_idempotency_and_request_record_are_durable_before_dispatch(self):
        paid_headers = []

        def response(url, headers=None, **kwargs):
            if headers.get("X-AISA-Cost-Mode") == "quote":
                return 200, {}, self.quote_body(1)
            records = list((client.CACHE / "requests").glob("*.json"))
            self.assertEqual(len(records), 1)
            record = json.loads(records[0].read_text())
            self.assertEqual(record["idempotency_key"], headers["Idempotency-Key"])
            self.assertEqual(record["outcome"], "pending")
            self.assertEqual(record["url"], url)
            self.assertEqual(headers["X-AISA-Max-Price-USD"], "0.000001")
            paid_headers.append(headers)
            return 200, {"x-aisa-customer-cost-micros-usd": "1"}, {"data": []}

        self.http.side_effect = response
        code, result = self.run_json("call", TRAFFIC, *self.traffic_args(), "--max-usd", "0.000001")
        self.assertEqual(code, 0)
        self.assertEqual(result["outcome"], "succeeded")
        self.assertEqual(result["cost_micros_usd"], 1)
        record = json.loads(Path(result["request_record"]).read_text())
        self.assertEqual(record["idempotency_key"], result["idempotency_key"])
        self.assertEqual(record["outcome"], "succeeded")
        self.assertEqual(len(paid_headers), 1)

    def test_transport_failures_preserve_unknown_outcome_and_do_not_retry(self):
        for error in (TimeoutError("timed out"), HTTPException("connection closed"), IncompleteRead(b"partial", 100)):
            with self.subTest(error=type(error).__name__):
                paid = self.serve(paid_error=error)
                code, result = self.run_json("call", TRAFFIC, *self.traffic_args(), "--max-usd", "1")
                self.assertNotEqual(code, 0)
                self.assertEqual(result["outcome"], "unknown")
                self.assertIsNone(result["cost_micros_usd"])
                self.assertEqual(len(paid), 1)
                self.assertTrue(result["idempotency_key"])
                record = json.loads(Path(result["request_record"]).read_text())
                self.assertEqual(record["outcome"], "unknown")
                self.assertEqual(record["idempotency_key"], result["idempotency_key"])

    def test_output_file_failure_retains_full_paid_response_and_record_location(self):
        paid = self.serve()
        out = Path(self.temp.name) / "output.json"
        save = client.save_execution

        def fail_output_only(path, data, **kwargs):
            if path.resolve() == out.resolve():
                raise OSError("disk full while writing output")
            return save(path, data, **kwargs)

        with mock.patch.object(client, "save_execution", side_effect=fail_output_only):
            code, result = self.run_json("call", TRAFFIC, *self.traffic_args(), "--max-usd", "1", "--out", str(out))
        self.assertNotEqual(code, 0)
        self.assertEqual(result["outcome"], "succeeded")
        self.assertIn("output_error", result)
        self.assertEqual(len(paid), 1)
        saved = json.loads(Path(result["request_record"]).read_text())
        self.assertEqual(saved["outcome"], "succeeded")
        self.assertEqual(saved["data"], result["data"])
        self.assertEqual(saved["cost_micros_usd"], 75_000)

    def test_existing_task_lock_blocks_paid_dispatch_and_remains_untouched(self):
        ledger = Path(self.temp.name) / "locked-task.json"
        lock = ledger.with_name(ledger.name + ".lock")
        lock.write_text("other process")
        paid = self.serve()
        code, result = self.run_json("call", TRAFFIC, *self.traffic_args(), "--max-usd", "1",
                                    "--task-ledger", str(ledger), "--task-budget-usd", "1")
        self.assertNotEqual(code, 0)
        self.assertIn("lock", result["error"])
        self.assertEqual(paid, [])
        self.assertEqual(lock.read_text(), "other process")

    def test_requested_dates_and_response_coverage_are_reported_separately(self):
        for data, month in (([], None), ({"month": "2026-08"}, "2026-08")):
            with self.subTest(data=data):
                self.http.side_effect = [
                    (200, {}, self.quote_body()),
                    (200, {"x-aisa-customer-cost-micros-usd": "75000"},
                     {"meta": {"last_updated": "2026-10-01"}, "data": data}),
                ]
                code, result = self.run_json("call", TRAFFIC, *self.traffic_args(), "--max-usd", "1")
                self.assertEqual(code, 0)
                self.assertEqual(result["requested_period"], {"start_date": "2026-09", "end_date": "2026-09"})
                self.assertEqual(result["data_period"], {"start_date": None, "end_date": None})
                self.assertEqual(result["data_month"], month)
                self.assertEqual(result["last_updated"], "2026-10-01")

    def test_recorded_idempotency_key_cannot_redispatch_or_overwrite_request(self):
        paid = self.serve()
        args = ["call", TRAFFIC, *self.traffic_args(), "--max-usd", "1", "--idem", "test-fixed-key"]
        code, result = self.run_json(*args)
        self.assertEqual(code, 0)
        path = Path(result["request_record"])
        original = path.read_text()
        for changed in (False, True):
            with self.subTest(changed_request=changed):
                retry = [arg.replace("example.com", "other.com") if changed else arg for arg in args]
                code, _ = self.run_json(*retry)
                self.assertNotEqual(code, 0)
                self.assertEqual(len(paid), 1)
                self.assertEqual(path.read_text(), original)

    def test_actual_charge_can_exceed_estimate_and_is_reported_without_clipping(self):
        paid = self.serve(quote_micros=75_000, charge="100000")
        code, result = self.run_json("call", TRAFFIC, *self.traffic_args(), "--max-usd", "0.075")
        self.assertEqual(code, 0)
        self.assertEqual(result["cost_micros_usd"], 100_000)
        self.assertEqual(Decimal(str(result["cost_usd"])), Decimal("0.1"))
        self.assertEqual(len(paid), 1)

    def test_task_budget_deducts_actual_charges_and_blocks_next_oversized_quote(self):
        ledger = str(Path(self.temp.name) / "task.json")
        args = ["call", TRAFFIC, *self.traffic_args(), "--max-usd", "1", "--task-ledger", ledger]
        first_paid = self.serve(quote_micros=100_000, charge="700000")
        code, result = self.run_json(*args, "--task-budget-usd", "1")
        self.assertEqual(code, 0)
        self.assertEqual(len(first_paid), 1)
        saved = json.loads(Path(ledger).read_text())
        self.assertEqual(saved["budget_micros_usd"], 1_000_000)
        self.assertEqual(saved["requests"][0]["request_record"], result["request_record"])
        second_paid = self.serve(quote_micros=400_000)
        code, result = self.run_json(*args)
        self.assertNotEqual(code, 0)
        self.assertTrue(result["refused"])
        self.assertEqual(second_paid, [])

    def test_unresolved_charge_blocks_further_task_spending(self):
        for label, charge, paid_error in (
            ("missing", None, None), ("invalid", "not-money", None),
            ("timeout", None, TimeoutError("timed out")),
        ):
            with self.subTest(case=label):
                ledger = str(Path(self.temp.name) / (label + ".json"))
                args = ["call", TRAFFIC, *self.traffic_args(), "--max-usd", "1", "--task-ledger", ledger]
                self.serve(charge=charge, paid_error=paid_error)
                _, result = self.run_json(*args, "--task-budget-usd", "1")
                self.assertIsNone(result["cost_micros_usd"])
                paid = self.serve()
                code, _ = self.run_json(*args)
                self.assertNotEqual(code, 0)
                self.assertEqual(paid, [])

    def test_reconciliation_records_evidence_and_allows_remaining_budget_to_be_used(self):
        ledger = str(Path(self.temp.name) / "reconcile-task.json")
        args = ["call", TRAFFIC, *self.traffic_args(), "--max-usd", "1", "--task-ledger", ledger]
        self.serve(paid_error=TimeoutError("timed out"))
        _, original = self.run_json(*args, "--task-budget-usd", "1")
        self.http.reset_mock()
        self.http.side_effect = AssertionError("reconcile must not call the API")
        code, result = self.run_json("reconcile", original["request_record"], "--charged-usd", "0.6",
                                    "--evidence", "Usage & Logs: request-test-1 charged USD 0.60")
        self.assertEqual(code, 0)
        self.assertEqual(result["cost_micros_usd"], 600_000)
        self.http.assert_not_called()
        record = json.loads(Path(original["request_record"]).read_text())
        self.assertEqual(record["cost_status"], "reconciled")
        self.assertIn("request-test-1", record["reconciliations"][0]["evidence"])
        paid = self.serve(quote_micros=400_000, charge="400000")
        code, result = self.run_json(*args)
        self.assertEqual(code, 0)
        self.assertEqual(len(paid), 1)
        self.assertEqual(paid[0][1]["X-AISA-Max-Price-USD"], "0.400000")
        self.assertEqual(result["task_remaining_micros_usd"], 0)

    def test_http_failure_reports_charge_without_assuming_it_is_free(self):
        paid = self.serve(status=503, charge="75000")
        code, result = self.run_json("call", TRAFFIC, *self.traffic_args(), "--max-usd", "1")
        self.assertNotEqual(code, 0)
        self.assertEqual(result["outcome"], "http_error")
        self.assertEqual(result["cost_micros_usd"], 75_000)
        self.assertEqual(len(paid), 1)
        self.assertNotIn("not billed", json.dumps(result))

    def test_usage_failures_have_nonzero_exit_status(self):
        self.http.side_effect = None
        for status, body in ((401, {"error": "unauthorized"}), (500, {"totals": {"charged_micros_usd": 0}}), (200, {})):
            with self.subTest(status=status, body=body):
                self.http.return_value = status, {}, body
                code, _ = self.run_json("usage")
                self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
