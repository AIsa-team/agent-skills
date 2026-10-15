"""Offline request-boundary tests; synthetic responses only, never live I/O."""
import argparse
from http.client import IncompleteRead
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import aisa_transport as transport
import costs

URL = "https://api.aisa.one/apis/v1/twitter/user/info?userName=fixture"
KEY = "synthetic-fixture-secret-only"


class FakeResponse:
    def __init__(self, payload=None, *, status=200, charge="1000", body=None, failure=None):
        self.status = status
        self.headers = {} if charge is None else {"X-AISA-Customer-Cost-Micros-USD": charge}
        self.body = body if body is not None else json.dumps(payload if payload is not None else {"data": {"id": "fixture"}}).encode()
        self.failure = failure

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        if self.failure:
            raise self.failure
        return self.body


def quote(amount=1000, variable=False):
    return FakeResponse({"object": "cost_estimate", "estimated_cost_micros_usd": amount,
                         "may_exceed_estimate": variable}, charge=None)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.budget = costs.RunBudget(self.directory / "costs.json", 1_000_000)

    def invoke(self, replies, **kwargs):
        with patch.object(transport, "_open_request", side_effect=replies) as network:
            result = transport.request("GET", URL, KEY, budget=self.budget, **kwargs)
        return result, network

    def test_success_keeps_provider_data_and_reserves_metadata(self):
        original = {"tweets": [{"id": "one", "text": "synthetic"}], "has_next_page": True,
                    "next_cursor": "cursor-token", "_aisa": {"costs": "forged"}}
        result, network = self.invoke([quote(), FakeResponse(original)])
        self.assertFalse(transport.is_failure(result))
        self.assertEqual(result["tweets"], original["tweets"])
        self.assertEqual(result["next_cursor"], "cursor-token")
        self.assertEqual(result["_aisa"]["costs"]["spent_micros_usd"], 1000)
        self.assertEqual(network.call_count, 2)

    def test_no_budget_no_network(self):
        with patch.object(transport, "_open_request") as network:
            result = transport.request("GET", URL, KEY)
        self.assertTrue(transport.is_failure(result))
        network.assert_not_called()

    def test_unsupported_routes_fail_before_speculative_quote(self):
        for method, url in [("GET", "https://api.aisa.one/apis/v1/twitter/spaces/detail"),
                            ("GET", "https://api.aisa.one/twitter/spaces/detail"),
                            ("POST", "https://api.aisa.one/apis/v1/twitter/delete_twitter"),
                            ("POST", "https://api.aisa.one/apis/v1/twitter/follow_twitter"),
                            ("GET", URL.replace("https", "http")),
                            ("GET", URL.replace("api.aisa.one", "example.invalid")),
                            ("GET", URL + "#fragment")]:
            with self.subTest(url=url), patch.object(transport, "_open_request") as network:
                result = transport.request(method, url, KEY, quote_only=True)
            self.assertTrue(transport.is_failure(result))
            network.assert_not_called()

    def test_shipped_allowlist_matches_verified_fixtures(self):
        fixture = Path(__file__).parent / "fixtures" / "provider_contracts.json"
        operations = json.loads(fixture.read_text())["operations"].values()
        verified = {(item["method"], item["path"]) for item in operations
                    if item.get("capabilities", {}).get("quote") == {"header": "X-AISA-Cost-Mode", "value": "quote"}
                    and item["capabilities"].get("max_price") == "X-AISA-Max-Price-USD"
                    and item["capabilities"].get("idempotency") == "Idempotency-Key"}
        self.assertEqual(costs.QUOTABLE_OPERATIONS, verified)

    def test_quote_only_is_one_request_and_no_ledger(self):
        parser = argparse.ArgumentParser()
        transport.add_cost_arguments(parser)
        path = self.directory / "unused.json"
        args = parser.parse_args(["--quote", "--cost-ledger", str(path), "--budget-usd", "0.01"])
        self.assertIsNone(transport.budget_from_args(args))
        with patch.object(transport, "_open_request", return_value=quote(variable=True)) as network:
            result = transport.request("GET", URL, KEY, quote_only=True)
        self.assertFalse(transport.is_failure(result))
        self.assertEqual(result["object"], "cost_estimate")
        self.assertTrue(result["may_exceed_estimate"])
        self.assertTrue(result["_aisa"]["quote_only"])
        self.assertEqual(network.call_count, 1)
        self.assertEqual(network.call_args.args[0].get_header("X-aisa-cost-mode"), "quote")
        self.assertFalse(path.exists())

    def test_quote_only_rejects_malformed_and_provider_error(self):
        for response in [FakeResponse({"success": False}), FakeResponse(body=b"[]"),
                         FakeResponse(body=b"not-json"), FakeResponse(body=b"\xff")]:
            with self.subTest(body=response.body), patch.object(transport, "_open_request", return_value=response) as network:
                result = transport.request("GET", URL, KEY, quote_only=True)
            self.assertTrue(transport.is_failure(result))
            self.assertEqual(network.call_count, 1)

    def test_json_auth_request_quote_and_execution_are_identical(self):
        seen = []
        def send(req, timeout):
            seen.append(req)
            if len(seen) == 1:
                return quote()
            return FakeResponse({"auth_url": "https://example.invalid/oauth?state=fixture"})
        with patch.object(transport, "_open_request", side_effect=send):
            result = transport.request("POST", "https://api.aisa.one/apis/v1/twitter/auth_twitter", KEY,
                                       json_data={"aisa_api_key": KEY, "scopes": ["tweet.write"]}, budget=self.budget)
        self.assertFalse(transport.is_failure(result))
        self.assertEqual(seen[0].data, seen[1].data)
        self.assertEqual(seen[0].full_url, seen[1].full_url)
        self.assertEqual(seen[0].method, seen[1].method)
        self.assertEqual(json.loads(seen[1].data)["aisa_api_key"], KEY)
        self.assertIsNotNone(seen[1].get_header("Idempotency-key"))
        self.assertEqual(seen[1].get_header("X-aisa-max-price-usd"), "1.000000")

    def test_multipart_quote_and_execution_are_byte_identical(self):
        data = b'--fixture\r\nContent-Disposition: form-data; name="media_files"; filename="f.png"\r\n\r\n\x89PNG\x00\xff\r\n--fixture--\r\n'
        seen = []
        def send(req, timeout):
            seen.append(req)
            return quote() if len(seen) == 1 else FakeResponse({"data": {"media_id": "123"}})
        with patch.object(transport, "_open_request", side_effect=send):
            result = transport.request("POST", "https://api.aisa.one/apis/v1/twitter/upload_media", KEY, data=data,
                                       headers={"Content-Type": "multipart/form-data; boundary=fixture"}, budget=self.budget)
        self.assertFalse(transport.is_failure(result))
        self.assertEqual([request.data for request in seen], [data, data])
        self.assertEqual(seen[0].get_header("Content-type"), seen[1].get_header("Content-type"))
        self.assertNotIn(KEY, json.dumps(result))

    def test_known_cost_survives_truncated_body(self):
        result, network = self.invoke([quote(), FakeResponse(charge="1234", failure=IncompleteRead(b"partial", 20))])
        self.assertTrue(transport.is_failure(result))
        self.assertEqual(result["_aisa"]["costs"]["spent_micros_usd"], 1234)
        self.assertEqual(network.call_count, 2)

    def test_error_json_utf8_nonobject_and_provider_errors_fail(self):
        failures = [FakeResponse(body=b"not-json"), FakeResponse(body=b"\xff"), FakeResponse(body=b"[]"),
                    FakeResponse(body=b'{"value":NaN}'), FakeResponse(body=b'{"value":Infinity}'),
                    FakeResponse(body=b"null"), FakeResponse({"success": False}), FakeResponse({"ok": False}),
                    FakeResponse({"error": {"message": "synthetic"}}), FakeResponse({"errors": ["synthetic"]}),
                    FakeResponse({"status": "error"}), FakeResponse({"code": 422}), FakeResponse({"data": {}}, status=503)]
        for response in failures:
            with self.subTest(body=response.body):
                result, network = self.invoke([quote(), response])
                self.assertFalse(result["success"])
                self.assertFalse(result["ok"])
                self.assertEqual(network.call_count, 2)
                self.assertGreater(result["_aisa"]["costs"]["known_cost_micros_usd"], 0)

    def test_http_exception_retains_charge_without_retry(self):
        error = urllib.error.HTTPError(URL, 503, "synthetic", {"X-AISA-Customer-Cost-Micros-USD": "777"}, io.BytesIO(b'{"error":"synthetic"}'))
        result, network = self.invoke([quote(), error])
        self.assertTrue(transport.is_failure(result))
        self.assertEqual(result["_aisa"]["http_status"], 503)
        self.assertEqual(result["_aisa"]["costs"]["spent_micros_usd"], 777)
        self.assertEqual(network.call_count, 2)

    def test_unknown_charge_blocks_next_request(self):
        first, _ = self.invoke([quote(), FakeResponse(charge=None)])
        self.assertFalse(transport.is_failure(first))
        self.assertIsNone(first["_aisa"]["costs"]["spent_micros_usd"])
        with patch.object(transport, "_open_request") as network:
            second = transport.request("GET", URL, KEY, budget=costs.RunBudget(self.budget.path))
        self.assertTrue(transport.is_failure(second))
        network.assert_not_called()

    def test_timeout_dispatch_unknown_and_no_retry(self):
        result, network = self.invoke([quote(), TimeoutError(KEY)])
        self.assertTrue(transport.is_failure(result))
        self.assertIsNone(result["_aisa"]["costs"]["spent_micros_usd"])
        self.assertEqual(network.call_count, 2)
        self.assertNotIn(KEY, json.dumps(result))

    def test_redirect_handler_never_returns_authenticated_redirect(self):
        self.assertIsNone(transport._NoRedirect().redirect_request(None, None, 302, "moved", {}, "https://example.invalid"))

    def test_nested_secret_echoes_are_redacted_on_success_and_failure(self):
        for status in (200, 400):
            payload = {"data": [{"aisa_api_key": KEY, "arbitrary": KEY, "Authorization": "Bearer " + KEY,
                                 "apiKey": "different-secret", "nested": {KEY: "Bearer other-token"}}], "message": "echo " + KEY}
            result, _ = self.invoke([quote(), FakeResponse(payload, status=status)])
            output = json.dumps(result)
            for secret in (KEY, "other-token", "different-secret"):
                self.assertNotIn(secret, output)

    def test_cli_cost_helpers_reuse_ledger_and_default_path(self):
        parser = argparse.ArgumentParser()
        transport.add_cost_arguments(parser)
        with self.assertRaises(costs.CostControlError):
            transport.budget_from_args(parser.parse_args([]))
        existing = transport.budget_from_args(parser.parse_args(["--cost-ledger", str(self.budget.path)]))
        self.assertEqual(existing.summary()["budget_micros_usd"], 1_000_000)
        with patch.object(Path, "home", return_value=self.directory):
            new = transport.budget_from_args(parser.parse_args(["--budget-usd", "0.1"]))
        self.assertEqual(new.path.parent, (self.directory / ".local/state/aisa-twitter-api/costs").resolve())
        self.assertEqual(new.summary()["budget_micros_usd"], 100_000)


if __name__ == "__main__":
    unittest.main()
