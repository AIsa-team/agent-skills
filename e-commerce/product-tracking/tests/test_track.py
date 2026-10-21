"""Offline behavioral tests of the shipped CLI; fixtures are synthetic."""

import copy
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "track.py"
ASIN = "B012345678"
OTHER = "B087654321"


def product(target=ASIN, detail=True, votes=100, price=20):
    return {"type": "amazon_product_info" if detail else "amazon_serp", "data_asin": target,
            "title": "Example exact variant", "domain": "www.amazon.com",
            "url": "https://www.amazon.com/dp/" + target, "currency": "USD", "price_from": price,
            "is_available": True, "bought_past_month": 1000,
            "rating": {"value": 4.5, "votes_count": votes, "rating_max": 5}}


def batch(identifier="one", family="asin", items=None, timestamp="2026-10-16 02:00:00 +00:00"):
    if items is None:
        items = [product(detail=family == "asin")]
    context = {"api": "merchant", "se": "amazon", "function": family, "se_domain": "amazon.com",
               "language_code": "en_US", "location_code": 2840, "device": "desktop", "os": "windows"}
    result = {"se_domain": "amazon.com", "language_code": "en_US", "location_code": 2840,
              "datetime": timestamp, "items_count": len(items), "items": items,
              "check_url": "https://www.amazon.com/dp/" + ASIN}
    if family == "products":
        context.update(keyword="Example product", depth=10, max_crawl_pages=1)
    else:
        context["asin"] = result["asin"] = ASIN
    return {"batch_id": "batch-" + identifier, "results": [{
        "call_id": "call-" + identifier, "request_id": "request-" + identifier,
        "tool": "synthetic-dataforseo", "successful": True, "upstream_status": 200,
        "data": {"status_code": 20000, "tasks_count": 1, "tasks_error": 0, "tasks": [{
            "id": "task-" + identifier, "status_code": 20000, "result_count": 1,
            "path": ["v3", "merchant", "amazon", family, "live", "advanced"],
            "data": context, "result": [result]}]}}]}


def call(value):
    return value["results"][0]


def task(value):
    return call(value)["data"]["tasks"][0]


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "tracking.sqlite"
        self.run_cli("add", "--asin", ASIN, "--label", "Exact variant")

    def run_cli(self, command, *args, status=0):
        result = subprocess.run([sys.executable, str(SCRIPT), command, "--db", str(self.db), *args],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, status, result.stdout + result.stderr)
        return json.loads(result.stdout or result.stderr)

    def ingest(self, value, status=0, collected_at="2026-10-16T05:00:00Z"):
        path = Path(self.temp.name) / "response.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return self.run_cli("ingest", "--input", str(path), "--collected-at", collected_at, status=status)

    def report(self):
        return self.run_cli("report", "--asin", ASIN)

    def comparison(self):
        return self.report()["series"][0]["comparison"]["rows"][0]

    def seed_snapshot(self, observation, identifier="legacy"):
        with sqlite3.connect(self.db) as connection:
            input_id = "input-" + identifier
            connection.execute("INSERT INTO inputs VALUES (?, ?, ?)", (input_id, observation["collected_at"], "{}"))
            connection.execute("""INSERT INTO snapshots (input_id, asin, marketplace, family, series,
                observed_at, collected_at, request_id, task_id, result_index, normalized_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (input_id, ASIN, "amazon.com", observation["family"], observation["series"],
                 observation["observed_at"], observation["collected_at"], "request-" + identifier,
                 "task-" + identifier, 0, json.dumps(observation)))

    def test_watchlist_strict_identity_and_idempotent_add(self):
        self.run_cli("init")
        self.run_cli("add", "--asin", ASIN)
        self.assertEqual(len(self.run_cli("list")), 1)
        self.assertEqual(self.run_cli("list")[0]["label"], "Exact variant")
        for invalid in ("b012345678", "B01234567", "B0123456789", " B012345678"):
            self.run_cli("add", "--asin", invalid, status=2)
        self.run_cli("add", "--asin", ASIN, "--marketplace", "amazon.com.evil.test", status=2)

    def test_wrapped_product_input_retains_unknowns_and_omits_unsupported_fields(self):
        item = product(price=None)
        item.update(is_available=None, seller_name="Unsupported", seller={"id": "SECRET"},
                    product_information={"seller": "SECRET", "brand": "Example"})
        self.ingest({"structuredContent": batch(items=[item])})
        report = self.report()
        observation = report["series"][0]["latest"]
        row = observation["rows"][0]
        self.assertIsNone(row["price_from"])
        self.assertIsNone(row["price_to"])
        self.assertIsNone(row["is_available"])
        self.assertEqual(row["rating"]["votes_count"], 100)
        self.assertEqual(observation["time_basis"], "provider_datetime")
        for key in ("seller", "seller_name", "seller_rating", "seller_units_sold", "seller_revenue", "product_information"):
            self.assertNotIn('"' + key + '"', json.dumps(report))
        self.assertNotIn("SECRET", json.dumps(report))

    def test_sellers_endpoint_is_rejected(self):
        value = batch(family="sellers", items=[{"type": "amazon_seller_item", "seller_name": "Unsupported"}])
        result = self.ingest(value, status=2)
        self.assertEqual(result["inserted_snapshots"], 0)
        self.assertIn("unsupported task path", result["rejected_calls"][0]["reason"])
        self.assertEqual(self.report()["series"], [])

    def test_nonproduct_detail_rows_reject_entire_call(self):
        for index, unexpected in enumerate(({"type": "amazon_seller_item"}, {"type": "amazon_serp"}, {"type": "unknown"})):
            result = self.ingest(batch(str(index), items=[product(), unexpected]), status=2)
            self.assertEqual(result["inserted_snapshots"], 0)
            self.assertIn("non-product detail", result["rejected_calls"][0]["reason"])
        self.assertEqual(self.report()["series"], [])

    def test_legacy_offer_history_is_ignored_and_preserved(self):
        self.ingest(batch())
        legacy = copy.deepcopy(self.report()["series"][0]["latest"])
        legacy.update(family="offers", series="offers:legacy", observed_at="2026-10-18T00:00:00Z",
                      rows=[{"row_type": "amazon_seller_item", "seller": {"name": "OLD SECRET"}}])
        self.seed_snapshot(legacy)
        report = self.report()
        self.assertEqual(len(report["series"]), 1)
        self.assertEqual(report["series"][0]["latest"]["family"], "detail")
        self.assertNotIn("OLD SECRET", json.dumps(report))
        with sqlite3.connect(self.db) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM snapshots WHERE family='offers'").fetchone()[0], 1)

    def test_legacy_product_rows_are_projected_to_supported_fields(self):
        self.ingest(batch())
        legacy = copy.deepcopy(self.report()["series"][0]["latest"])
        legacy["observed_at"] = "2026-10-17T00:00:00Z"
        legacy["rows"][0].update(seller={"name": "OLD SECRET"}, seller_name="OLD SECRET",
                                  product_information={"sold_by": "OLD SECRET"})
        legacy["rows"][0]["rating"]["seller_feedback"] = "OLD SECRET"
        legacy["rows"][0]["rating"]["rating_type"] = {"seller_feedback": "OLD SECRET"}
        legacy["rows"][0]["title"] = {"seller_name": "OLD SECRET"}
        legacy["rows"][0]["demand_signal"]["seller_units_sold"] = 100
        legacy["rows"].append({"row_type": "amazon_seller_item", "seller": "OLD SECRET"})
        self.seed_snapshot(legacy)
        report = self.report()
        self.assertNotIn("OLD SECRET", json.dumps(report))
        self.assertNotIn("seller_units_sold", json.dumps(report))
        self.assertEqual(len(report["series"][0]["latest"]["rows"]), 1)
        self.assertEqual(self.comparison()["price_delta"], 0)

    def test_duplicate_task_or_request_never_adds_a_snapshot(self):
        original = batch()
        self.assertEqual(self.ingest(original)["inserted_snapshots"], 1)
        self.assertEqual(self.ingest(original)["duplicate_snapshots"], 1)
        same_task = copy.deepcopy(original)
        call(same_task)["request_id"] = "different-request"
        self.assertEqual(self.ingest(same_task)["duplicate_snapshots"], 1)
        same_request = copy.deepcopy(original)
        task(same_request)["id"] = "different-task"
        self.assertEqual(self.ingest(same_request)["duplicate_snapshots"], 1)
        self.assertIsNone(self.report()["series"][0]["comparison"]["previous_observed_at"])

    def test_legacy_snapshot_replay_ignores_removed_fields(self):
        value = batch()
        self.ingest(value)
        with sqlite3.connect(self.db) as connection:
            row = connection.execute("SELECT * FROM snapshots").fetchone()
            normalized = json.loads(row[-1])
            normalized["rows"][0]["product_information"] = {"seller_name": "OLD SECRET"}
            normalized["rows"][0]["demand_signal"]["meaning"] = "old interpretation"
            # Simulate an existing database created by the previous version.
            connection.execute("DROP TRIGGER immutable_snapshot_update")
            connection.execute("UPDATE snapshots SET normalized_json=?", (json.dumps(normalized),))
        self.assertEqual(self.ingest(value)["duplicate_snapshots"], 1)
        self.assertNotIn("OLD SECRET", json.dumps(self.report()))

    def test_missing_provider_time_replay_keeps_first_collection_time(self):
        original = batch(timestamp=None)
        self.ingest(original, collected_at="2026-10-16T05:00:00Z")
        self.assertEqual(self.ingest(original, collected_at="2026-10-17T05:00:00Z")["duplicate_snapshots"], 1)
        latest = self.report()["series"][0]["latest"]
        self.assertEqual(latest["observed_at"], "2026-10-16T05:00:00.000000+00:00")
        self.assertEqual(latest["time_basis"], "collection_time")
        task(original)["result"][0]["items"][0]["price_from"] = 999
        self.assertEqual(self.ingest(original, status=2)["inserted_snapshots"], 0)

    def test_failure_and_partial_items_never_replace_last_good(self):
        self.ingest(batch())
        invalid = []
        value = batch("failed-aisa")
        call(value)["successful"] = False
        invalid.append(value)
        value = batch("failed-http")
        call(value)["upstream_status"] = 500
        invalid.append(value)
        value = batch("failed-provider")
        call(value)["data"]["status_code"] = 50000
        invalid.append(value)
        value = batch("failed-task")
        task(value)["status_code"] = 40100
        invalid.append(value)
        value = batch("partial")
        task(value)["result"][0]["items_count"] = 2
        invalid.append(value)
        invalid.append(batch("empty", items=[]))
        for value in invalid:
            result = self.ingest(value, status=2)
            self.assertEqual(result["inserted_snapshots"], 0)
            self.assertEqual(len(result["rejected_calls"]), 1)
        self.assertEqual(self.report()["series"][0]["latest"]["provenance"]["request_id"], "request-one")

    def test_marketplace_asin_and_url_mismatches_are_rejected(self):
        cases = []
        for field, replacement in (("asin", OTHER), ("se_domain", "amazon.co.uk"), ("location_code", 2826)):
            value = batch(field)
            task(value)["result"][0][field] = replacement
            cases.append(value)
        value = batch("url")
        task(value)["result"][0]["check_url"] = "https://www.amazon.com/dp/" + OTHER
        cases.append(value)
        value = batch("item-url")
        task(value)["result"][0]["items"][0]["url"] = "https://amazon.com/dp/" + OTHER
        cases.append(value)
        cases.append(batch("detail", items=[product(target=OTHER)]))
        for value in cases:
            self.assertEqual(self.ingest(value, status=2)["inserted_snapshots"], 0)
        self.assertEqual(self.report()["series"], [])

    def test_unwatched_and_unrelated_search_rows_are_not_imported(self):
        value = batch(family="products", items=[product(detail=False), product(OTHER, detail=False), {"type": "amazon_seller_item"}])
        result = self.ingest(value)
        self.assertEqual(result["inserted_snapshots"], 1)
        rows = self.report()["series"][0]["latest"]["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["demand_signal"]["bought_past_month"], 1000)
        self.assertIn("not exact units", rows[0]["demand_signal"]["meaning"])
        self.run_cli("report", "--asin", OTHER, status=2)

    def test_search_ad_domains_and_unwatched_external_rows(self):
        watched = product(detail=False)
        watched["domain"] = "sponsored-ads.amazon.com"
        watched["url"] = "https://sponsored-ads.amazon.com/ad/product"
        other = product(OTHER, detail=False)
        other["domain"] = "an-external-untracked.example"
        other["url"] = "https://an-external-untracked.example/product"
        self.assertEqual(self.ingest(batch(family="products", items=[watched, other]))["inserted_snapshots"], 1)
        watched["domain"] = "amazon.com.evil.example"
        self.assertEqual(self.ingest(batch("evil", "products", items=[watched]), status=2)["inserted_snapshots"], 0)

    def test_product_url_scheme_userinfo_negative_and_reversed_prices_rejected(self):
        for index, url in enumerate(("ftp://amazon.com/dp/" + ASIN, "https://user@amazon.com/dp/" + ASIN)):
            item = product()
            item["url"] = url
            self.assertEqual(self.ingest(batch(str(index), items=[item]), status=2)["inserted_snapshots"], 0)
        self.assertEqual(self.ingest(batch("negative", items=[product(price=-5)]), status=2)["inserted_snapshots"], 0)
        item = product()
        item["price_to"] = "unparsed range"
        self.assertEqual(self.ingest(batch("malformed-range", items=[item]), status=2)["inserted_snapshots"], 0)
        item = product()
        item["price_to"] = 19
        self.assertEqual(self.ingest(batch("reversed", items=[item]), status=2)["inserted_snapshots"], 0)

    def test_missing_locale_is_rejected(self):
        for field in ("location_code", "language_code"):
            value = batch(field)
            task(value)["data"].pop(field)
            task(value)["result"][0].pop(field)
            self.assertEqual(self.ingest(value, status=2)["inserted_snapshots"], 0)

    def test_product_price_rating_availability_and_demand_changes(self):
        self.ingest(batch(items=[product(votes=100, price=20)]))
        changed = product(votes=110, price=19)
        changed.update(is_available=False, bought_past_month=2000)
        changed["rating"]["value"] = 4.6
        self.ingest(batch("two", items=[changed], timestamp="2026-10-17T02:00:00Z"))
        comparison = self.comparison()
        self.assertEqual(comparison["status"], "observed_product_changed")
        self.assertEqual(comparison["price_status"], "changed")
        self.assertEqual(comparison["price_delta"], -1)
        self.assertEqual(comparison["rating_count_delta"], 10)
        self.assertEqual(comparison["rating_value_delta"], 0.1)
        self.assertTrue(comparison["availability_changed"])
        self.assertNotIn("sales_delta", json.dumps(self.report()))
        self.assertNotIn("revenue", comparison)

    def test_unknown_changed_currency_and_missing_price_suppress_delta(self):
        cases = [(None, None, 19, "unknown_currency"), ("USD", "EUR", 19, "currency_changed"),
                 ("USD", "USD", None, "unknown_price"), ("usd", "usd", 19, "unknown_currency")]
        for index, (old_currency, new_currency, new_price, expected) in enumerate(cases):
            first, second = product(), product(price=new_price)
            first["currency"], second["currency"] = old_currency, new_currency
            self.ingest(batch(str(index) + "old", items=[first], timestamp=f"2026-10-{16+index}T01:00:00Z"))
            self.ingest(batch(str(index) + "new", items=[second], timestamp=f"2026-10-{16+index}T02:00:00Z"))
            self.assertIsNone(self.comparison()["price_delta"])
            self.assertEqual(self.comparison()["price_status"], expected)

    def test_price_ranges_remain_ranges_without_scalar_delta(self):
        first, second = product(), product(price=19)
        first["price_to"], second["price_to"] = 25, 24
        self.ingest(batch(items=[first]))
        self.ingest(batch("two", items=[second], timestamp="2026-10-17T02:00:00Z"))
        comparison = self.comparison()
        self.assertEqual(comparison["current_price_ranges"], [{"price_from": 19, "price_to": 24, "currency": "USD"}])
        self.assertEqual(comparison["previous_price_ranges"], [{"price_from": 20, "price_to": 25, "currency": "USD"}])
        self.assertEqual(comparison["price_status"], "range_observed")
        self.assertIsNone(comparison["price_delta"])

    def test_duplicate_rows_prevent_arbitrary_price_and_rating_pairing(self):
        self.ingest(batch(items=[product(price=20), product(price=21)]))
        self.ingest(batch("two", items=[product(price=21), product(price=19)], timestamp="2026-10-17T02:00:00Z"))
        comparison = self.comparison()
        self.assertEqual(comparison["status"], "not_comparable")
        self.assertEqual(comparison["price_status"], "ambiguous_rows")
        self.assertEqual(comparison["current_row_count"], 2)
        self.assertIsNone(comparison["price_delta"])
        self.assertIsNone(comparison["rating_count_delta"])
        self.assertIsNone(comparison["availability_changed"])

    def test_search_paid_and_organic_prices_are_not_mixed(self):
        organic, paid = product(detail=False), product(detail=False, price=30)
        paid["type"] = "amazon_paid"
        self.ingest(batch(family="products", items=[organic, paid]))
        organic["price_from"] = 19
        paid["price_from"] = 32
        self.ingest(batch("two", "products", items=[paid, organic], timestamp="2026-10-17T02:00:00Z"))
        rows = {r["row_type"]: r for r in self.report()["series"][0]["comparison"]["rows"]}
        self.assertEqual(rows["amazon_serp"]["price_delta"], -1)
        self.assertEqual(rows["amazon_paid"]["price_delta"], 2)

    def test_missing_search_row_type_only_means_not_observed(self):
        organic, paid = product(detail=False), product(detail=False)
        paid["type"] = "amazon_paid"
        self.ingest(batch(family="products", items=[organic, paid]))
        self.ingest(batch("two", "products", items=[organic], timestamp="2026-10-17T02:00:00Z"))
        rows = {r["row_type"]: r for r in self.report()["series"][0]["comparison"]["rows"]}
        self.assertEqual(rows["amazon_paid"]["status"], "not_observed_now")
        self.assertIsNone(rows["amazon_paid"]["availability_changed"])

    def test_conflicting_replay_rejected_without_overwrite(self):
        original = batch()
        self.ingest(original)
        task(original)["result"][0]["items"][0]["price_from"] = 999
        result = self.ingest(original, status=2)
        self.assertIn("conflicting replay", result["rejected_calls"][0]["reason"])
        self.assertEqual(self.report()["series"][0]["latest"]["rows"][0]["price_from"], 20)

    def test_other_marketplace_is_not_imported(self):
        value = batch()
        task(value)["data"]["se_domain"] = "amazon.co.uk"
        result = task(value)["result"][0]
        result["se_domain"] = "amazon.co.uk"
        result["check_url"] = result["check_url"].replace("amazon.com", "amazon.co.uk")
        result["items"][0]["url"] = result["items"][0]["url"].replace("amazon.com", "amazon.co.uk")
        result["items"][0]["domain"] = "amazon.co.uk"
        self.assertEqual(self.ingest(value)["inserted_snapshots"], 0)

    def test_source_time_wins_over_import_order(self):
        self.ingest(batch("new", items=[product(price=19)], timestamp="2026-10-17T02:00:00Z"))
        self.ingest(batch("old", items=[product(price=20)]))
        latest = self.report()["series"][0]
        self.assertEqual(latest["latest"]["provenance"]["request_id"], "request-new")
        self.assertEqual(self.comparison()["price_delta"], -1)

    def test_source_and_locale_ratings_never_cross_series(self):
        values = [batch("search", "products"), batch("detail", "asin")]
        other_location = batch("locale")
        task(other_location)["data"]["location_code"] = 21176
        task(other_location)["result"][0]["location_code"] = 21176
        values.append(other_location)
        other_keyword = batch("keyword", "products")
        task(other_keyword)["data"]["keyword"] = "Different query"
        values.append(other_keyword)
        self.ingest({"responses": values})
        series = self.report()["series"]
        self.assertEqual(len(series), 4)
        self.assertTrue(all(s["comparison"]["previous_observed_at"] is None for s in series))
        self.assertTrue(all(s["comparison"]["rows"][0]["price_delta"] is None for s in series))

    def test_malformed_optional_rating_and_unknown_availability_remain_unknown(self):
        item = product()
        item["rating"] = "unparsed upstream text"
        item["is_available"] = None
        self.ingest(batch("old", items=[item]))
        self.ingest(batch("new", items=[item], timestamp="2026-10-17T00:00:00Z"))
        series = self.report()["series"][0]
        self.assertIsNone(series["latest"]["rows"][0]["rating"])
        self.assertIsNone(self.comparison()["rating_count_delta"])
        self.assertIsNone(self.comparison()["rating_value_delta"])
        self.assertIsNone(self.comparison()["availability_changed"])

    def test_changed_rating_scale_suppresses_value_delta(self):
        self.ingest(batch())
        item = product()
        item["rating"].update(value=9, rating_max=10)
        self.ingest(batch("new", items=[item], timestamp="2026-10-17T00:00:00Z"))
        self.assertIsNone(self.comparison()["rating_value_delta"])

    def test_raw_evidence_is_immutable_and_provenance_retrievable(self):
        value = batch()
        result = self.ingest(value)
        with sqlite3.connect(self.db) as connection:
            raw = connection.execute("SELECT raw_json FROM inputs WHERE id=?", (result["input_id"],)).fetchone()[0]
            self.assertEqual(json.loads(raw), value)
            for sql in ("UPDATE inputs SET raw_json='{}'", "DELETE FROM inputs", "DELETE FROM snapshots"):
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(sql)

    def test_partial_batch_imports_good_calls_but_exits_nonzero(self):
        value = batch()
        bad = batch("failed", "sellers")
        value["results"].append(call(bad))
        result = self.ingest(value, status=2)
        self.assertEqual(result["inserted_snapshots"], 1)
        self.assertEqual(len(result["rejected_calls"]), 1)

    def test_invalid_timestamp_is_rejected(self):
        self.ingest(batch(), status=2, collected_at="2026-10-16T05:00:00")
        self.assertEqual(self.ingest(batch(timestamp="not a time"), status=2)["inserted_snapshots"], 0)


if __name__ == "__main__":
    unittest.main()
