#!/usr/bin/env python3
"""Offline, append-only Amazon observation store. Python 3.10+, standard library.

Consumes saved AIsa batch_use JSON; never authenticates or makes network calls.
Provider text is data only. Every normalized snapshot points to immutable input.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
from urllib.parse import parse_qs, urlparse


ASIN = re.compile(r"[A-Z0-9]{10}\Z")
MARKETS = {
    "amazon.com", "amazon.ca", "amazon.com.mx", "amazon.com.br", "amazon.co.uk",
    "amazon.de", "amazon.fr", "amazon.it", "amazon.es", "amazon.nl", "amazon.se",
    "amazon.pl", "amazon.com.be", "amazon.ie", "amazon.co.jp", "amazon.in",
    "amazon.com.au", "amazon.sg", "amazon.ae", "amazon.sa", "amazon.com.tr",
    "amazon.eg", "amazon.co.za",
}
FAMILIES = {"products": "search", "asin": "detail"}
ROW_TYPES = {"search": {"amazon_serp", "amazon_paid"}, "detail": {"amazon_product_info"}}
DEMAND_MEANING = "approximate product-level past-month customer purchase signal; not exact units or revenue"
PRODUCT_FIELDS = (
    "source_row", "row_type", "title", "parent_asin", "url", "price_from", "price_to",
    "currency", "rank_group", "rank_absolute", "is_available", "is_amazon_choice", "is_best_seller",
)


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(dumps(value).encode()).hexdigest()


def utc(value=None):
    if value is None:
        return datetime.now(timezone.utc).isoformat(timespec="microseconds")
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO timestamp with timezone")
    # DataForSEO returns 'YYYY-MM-DD HH:MM:SS +00:00'.
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00").replace(" +", "+"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp requires an explicit timezone")
    return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds")


def asin(value):
    if not isinstance(value, str) or not ASIN.fullmatch(value):
        raise ValueError("ASIN must be exactly 10 uppercase ASCII letters/digits")
    return value


def market(value):
    if not isinstance(value, str):
        raise ValueError("marketplace must be an Amazon domain")
    value = value.lower().removeprefix("www.")
    if value not in MARKETS:
        raise ValueError("unsupported Amazon marketplace domain: " + value)
    return value


def number(value):
    return value if type(value) in (int, float) and math.isfinite(value) else None


def money(value):
    parsed = number(value)
    if value is not None and parsed is None:
        raise ValueError("monetary value must be numeric or null")
    if parsed is not None and parsed < 0:
        raise ValueError("negative monetary value is invalid")
    return parsed


def text_value(value):
    return value if isinstance(value, str) else None


def rating(value):
    if not isinstance(value, dict):
        return None
    return {"value": number(value.get("value")), "votes_count": number(value.get("votes_count")),
            "rating_max": number(value.get("rating_max")), "rating_type": text_value(value.get("rating_type"))}


def amazon_host(host, marketplace, allow_subdomains=False):
    if not isinstance(host, str):
        return False
    host = host.lower().removeprefix("www.")
    return host == marketplace or (allow_subdomains and host.endswith("." + marketplace))


def validate_url_identity(raw_url, marketplace, expected_asin=None, allow_subdomains=False):
    if raw_url is None:
        return
    if not isinstance(raw_url, str):
        raise ValueError("identity URL must be text")
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or parsed.username is not None or parsed.password is not None or not amazon_host(parsed.hostname, marketplace, allow_subdomains):
        raise ValueError("URL marketplace conflicts with result")
    query_asin = parse_qs(parsed.query).get("asin", [None])[0]
    path_asin = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})(?:/|$)", parsed.path)
    for value in (query_asin, path_asin.group(1) if path_asin else None):
        if value is not None and expected_asin is not None and value != expected_asin:
            raise ValueError("URL ASIN conflicts with result")


def db_open(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS watch (
            asin TEXT NOT NULL, marketplace TEXT NOT NULL, label TEXT,
            added_at TEXT NOT NULL, PRIMARY KEY (asin, marketplace));
        CREATE TABLE IF NOT EXISTS inputs (
            id TEXT PRIMARY KEY, collected_at TEXT NOT NULL, raw_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY, input_id TEXT NOT NULL REFERENCES inputs(id),
            asin TEXT NOT NULL, marketplace TEXT NOT NULL, family TEXT NOT NULL,
            series TEXT NOT NULL, observed_at TEXT NOT NULL, collected_at TEXT NOT NULL,
            request_id TEXT NOT NULL, task_id TEXT NOT NULL, result_index INTEGER NOT NULL,
            normalized_json TEXT NOT NULL,
            UNIQUE (task_id, asin, marketplace, series, result_index),
            UNIQUE (request_id, asin, marketplace, series, result_index));
        CREATE INDEX IF NOT EXISTS snapshot_product
            ON snapshots (asin, marketplace, series, observed_at);
        CREATE TRIGGER IF NOT EXISTS immutable_input_update BEFORE UPDATE ON inputs
            BEGIN SELECT RAISE(ABORT, 'inputs are append-only'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_input_delete BEFORE DELETE ON inputs
            BEGIN SELECT RAISE(ABORT, 'inputs are append-only'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_snapshot_update BEFORE UPDATE ON snapshots
            BEGIN SELECT RAISE(ABORT, 'snapshots are append-only'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_snapshot_delete BEFORE DELETE ON snapshots
            BEGIN SELECT RAISE(ABORT, 'snapshots are append-only'); END;
    """)
    return connection


def batches(value):
    if isinstance(value, list):
        for item in value:
            yield from batches(item)
    elif isinstance(value, dict) and isinstance(value.get("structuredContent"), dict):
        if value.get("isError") is True:
            raise ValueError("MCP response isError is true")
        yield from batches(value["structuredContent"])
    elif isinstance(value, dict) and isinstance(value.get("responses"), list):
        yield from batches(value["responses"])
    elif isinstance(value, dict) and isinstance(value.get("results"), list):
        yield value
    else:
        raise ValueError("expected batch_use results[], structuredContent, or responses[]")


def product(item, index):
    price_from, price_to = money(item.get("price_from")), money(item.get("price_to"))
    if price_from is not None and price_to is not None and price_to < price_from:
        raise ValueError("product price range is reversed")
    return {
        "source_row": index, "row_type": item.get("type"), "title": text_value(item.get("title")),
        "parent_asin": text_value(item.get("parent_asin")), "url": text_value(item.get("url")),
        "price_from": price_from, "price_to": price_to,
        "currency": text_value(item.get("currency")), "rating": rating(item.get("rating")),
        "rank_group": number(item.get("rank_group")),
        "rank_absolute": number(item.get("rank_absolute")),
        "is_available": item.get("is_available"),
        "is_amazon_choice": item.get("is_amazon_choice"),
        "is_best_seller": item.get("is_best_seller"),
        "demand_signal": {"bought_past_month": number(item.get("bought_past_month")),
                          "meaning": DEMAND_MEANING},
    }


def project_observation(observation):
    """Expose only supported product fields, including for older saved snapshots."""
    family = observation.get("family")
    if family not in ROW_TYPES:
        return None
    rows = []
    for row in observation.get("rows", []):
        if not isinstance(row, dict) or row.get("row_type") not in ROW_TYPES[family]:
            continue
        projected = {field: row.get(field) for field in PRODUCT_FIELDS}
        for field in ("source_row", "price_from", "price_to", "rank_group", "rank_absolute"):
            projected[field] = number(projected[field])
        for field in ("row_type", "title", "parent_asin", "url", "currency"):
            projected[field] = text_value(projected[field])
        for field in ("is_available", "is_amazon_choice", "is_best_seller"):
            projected[field] = projected[field] if type(projected[field]) is bool else None
        projected["rating"] = rating(row.get("rating"))
        demand = row.get("demand_signal")
        projected["demand_signal"] = {
            "bought_past_month": number(demand.get("bought_past_month")) if isinstance(demand, dict) else None,
            "meaning": DEMAND_MEANING,
        }
        rows.append(projected)
    if not rows:
        return None
    result = {key: observation.get(key) for key in (
        "family", "asin", "marketplace", "series", "observed_at", "collected_at", "time_basis",
        "coverage", "declared_items_count", "returned_items_count", "title",
    )}
    scope = observation.get("scope") or {}
    result["scope"] = {key: scope.get(key) for key in (
        "location_code", "language_code", "device", "os",
        *(("keyword", "depth", "max_crawl_pages") if family == "search" else ()),
    )}
    provenance = observation.get("provenance") or {}
    result["provenance"] = {key: provenance.get(key) for key in (
        "provider", "tool", "batch_id", "call_id", "request_id", "task_id", "path", "result_index",
        "check_url", "customer_cost_micros_usd", "input_id",
    )}
    result["rows"] = rows
    return result


def validate_call(call):
    if not isinstance(call, dict) or call.get("successful") is not True:
        raise ValueError("AIsa call did not succeed")
    if type(call.get("upstream_status")) is not int or not 200 <= call["upstream_status"] < 300:
        raise ValueError("AIsa upstream HTTP status is not successful")
    data = call.get("data")
    if not isinstance(data, dict) or data.get("status_code") != 20000:
        raise ValueError("DataForSEO outer status is not 20000")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("missing DataForSEO tasks")
    if data.get("tasks_error", 0) != 0 or data.get("tasks_count", len(tasks)) != len(tasks):
        raise ValueError("DataForSEO tasks are failed or incomplete")
    if not isinstance(call.get("request_id"), str) or not call["request_id"]:
        raise ValueError("missing AIsa request_id; cannot safely deduplicate")
    return tasks


def normalize_task(task, call, batch, watched, collected_at):
    if not isinstance(task, dict) or task.get("status_code") != 20000:
        raise ValueError("DataForSEO task status is not 20000")
    if not isinstance(task.get("id"), str) or not task["id"]:
        raise ValueError("missing DataForSEO task id")
    path = task.get("path")
    if not isinstance(path, list) or len(path) != 6 or path[:3] != ["v3", "merchant", "amazon"] or path[4:] != ["live", "advanced"] or path[3] not in FAMILIES:
        raise ValueError("unsupported task path; expected Amazon products/asin live advanced")
    function, family = path[3], FAMILIES[path[3]]
    context = task.get("data")
    if not isinstance(context, dict) or context.get("se") != "amazon" or context.get("function") != function:
        raise ValueError("task data does not match endpoint")
    if type(context.get("location_code")) is not int or context["location_code"] <= 0 or not isinstance(context.get("language_code"), str) or not context["language_code"].strip():
        raise ValueError("MVP requires explicit location_code and language_code")
    marketplace = market(context.get("se_domain"))
    requested_asin = asin(context.get("asin")) if family != "search" else None
    results = task.get("result")
    if not isinstance(results, list) or not results or task.get("result_count") != len(results):
        raise ValueError("task results are missing or incomplete")
    result_snapshots = []
    for result_index, result in enumerate(results):
        if not isinstance(result, dict) or market(result.get("se_domain")) != marketplace:
            raise ValueError("result marketplace does not match request")
        for field in ("location_code", "language_code"):
            if context.get(field) != result.get(field):
                raise ValueError("result " + field + " does not match request")
        result_asin = asin(result.get("asin")) if family != "search" else None
        if requested_asin != result_asin:
            raise ValueError("result ASIN does not match request")
        validate_url_identity(result.get("check_url"), marketplace, result_asin)
        items = result.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError("empty/missing items are not an availability observation")
        if family != "search" and result.get("items_count") != len(items):
            raise ValueError("items_count mismatch: partial detail response")
        source_datetime = result.get("datetime")
        observed_at = utc(source_datetime) if source_datetime else collected_at
        groups = defaultdict(list)
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError("invalid item")
            if item.get("type") not in ROW_TYPES[family]:
                if family == "detail":
                    raise ValueError("unexpected non-product detail row type")
                continue
            if family == "search" and (item.get("data_asin"), marketplace) not in watched:
                continue
            item_asin = asin(item.get("data_asin"))
            if result_asin is not None and item_asin != result_asin:
                raise ValueError("detail item ASIN conflicts with result")
            domain = item.get("domain")
            if domain is not None and not amazon_host(domain, marketplace, family == "search"):
                raise ValueError("item marketplace conflicts with result")
            validate_url_identity(item.get("url"), marketplace, item_asin, family == "search")
            # Separate organic/paid rankings; multiple rows are retained.
            groups[item_asin].append(product(item, index))
        for item_asin, rows in groups.items():
            if (item_asin, marketplace) not in watched:
                continue
            scope = {key: context.get(key) for key in (
                "location_code", "language_code", "device", "os")}
            if family == "search":
                scope.update({key: context.get(key) for key in ("keyword", "depth", "max_crawl_pages")})
            series = family + ":" + digest(scope)[:20]
            observation = {
                "family": family, "asin": item_asin, "marketplace": marketplace,
                "series": series, "scope": scope, "observed_at": observed_at,
                "collected_at": collected_at, "time_basis": "provider_datetime" if source_datetime else "collection_time",
                "provenance": {"provider": "DataForSEO via AIsa", "tool": call.get("tool"),
                    "batch_id": batch.get("batch_id"), "call_id": call.get("call_id"),
                    "request_id": call["request_id"], "task_id": task["id"],
                    "path": path, "result_index": result_index, "check_url": result.get("check_url"),
                    "customer_cost_micros_usd": call.get("customer_cost_micros_usd")},
                "coverage": "observed rows only; marketplace completeness is unknown",
                "declared_items_count": result.get("items_count"),
                "returned_items_count": len(items), "title": result.get("title"),
                "rows": rows,
            }
            result_snapshots.append(observation)
    return result_snapshots


def ingest(connection, raw, collected_at):
    parsed_batches = list(batches(raw))
    watched = {(r["asin"], r["marketplace"]) for r in connection.execute("SELECT * FROM watch")}
    if not watched:
        raise ValueError("watchlist is empty; add exact ASIN/marketplace before ingest")
    input_id = digest(raw)
    stats = {"input_id": input_id, "inserted_snapshots": 0, "duplicate_snapshots": 0,
             "ignored_calls": 0, "rejected_calls": []}
    with connection:
        connection.execute("INSERT OR IGNORE INTO inputs VALUES (?, ?, ?)", (input_id, collected_at, dumps(raw)))
        for batch in parsed_batches:
            for call in batch["results"]:
                try:
                    tasks = validate_call(call)
                    # Validate the complete call before committing any of its snapshots.
                    observations = [observation for task in tasks for observation in
                                    normalize_task(task, call, batch, watched, collected_at)]
                    # A replay may change wrapper IDs/times, never business observations.
                    for observation in observations:
                        provenance = observation["provenance"]
                        prior = connection.execute("""SELECT normalized_json FROM snapshots
                            WHERE (task_id=? OR request_id=?) AND asin=? AND marketplace=?
                            AND series=? AND result_index=?""", (provenance["task_id"], provenance["request_id"],
                            observation["asin"], observation["marketplace"], observation["series"],
                            provenance["result_index"])).fetchall()
                        def comparable(obs):
                            obs = project_observation(obs)
                            excluded = {"provenance", "collected_at"}
                            if obs.get("time_basis") == "collection_time":
                                excluded.add("observed_at")
                            return {key: value for key, value in obs.items() if key not in excluded}
                        if any(comparable(json.loads(row[0])) != comparable(observation) for row in prior):
                            raise ValueError("conflicting replay for an existing request/task snapshot")
                except (ValueError, TypeError) as error:
                    stats["rejected_calls"].append({"call_id": call.get("call_id") if isinstance(call, dict) else None,
                                                    "reason": str(error)})
                    continue
                if not observations:
                    stats["ignored_calls"] += 1
                for observation in observations:
                    provenance = observation["provenance"]
                    observation["provenance"]["input_id"] = input_id
                    cursor = connection.execute("""INSERT OR IGNORE INTO snapshots
                        (input_id, asin, marketplace, family, series, observed_at, collected_at,
                         request_id, task_id, result_index, normalized_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (input_id, observation["asin"], observation["marketplace"], observation["family"],
                         observation["series"], observation["observed_at"], collected_at,
                         provenance["request_id"], provenance["task_id"], provenance["result_index"], dumps(observation)))
                    stats["inserted_snapshots" if cursor.rowcount else "duplicate_snapshots"] += 1
    return stats


def price_bounds(rows):
    return sorted(({"price_from": row.get("price_from"), "price_to": row.get("price_to"),
                    "currency": row.get("currency")} for row in rows), key=dumps)


def point_price(row):
    lower, upper = number(row.get("price_from")), number(row.get("price_to"))
    if lower is not None and lower >= 0 and (upper is None or upper == lower):
        return lower
    return None


def compare_product(latest, previous):
    current, before = defaultdict(list), defaultdict(list)
    for row in latest["rows"]:
        current[row["row_type"]].append(row)
    if previous:
        for row in previous["rows"]:
            before[row["row_type"]].append(row)
    comparisons = []
    for row_type in sorted(current.keys() | before.keys()):
        now, old = current[row_type], before[row_type]
        comparison = {
            "row_type": row_type, "current_row_count": len(now), "previous_row_count": len(old),
            "current_price_ranges": price_bounds(now), "previous_price_ranges": price_bounds(old),
            "price_delta": None, "rating_count_delta": None, "rating_value_delta": None,
            "availability_changed": None,
        }
        if previous is None:
            comparison["status"] = comparison["price_status"] = "baseline"
        elif not now:
            comparison["status"] = comparison["price_status"] = "not_observed_now"
        elif not old:
            comparison["status"] = comparison["price_status"] = "newly_observed"
        elif len(now) != 1 or len(old) != 1:
            comparison["status"] = "not_comparable"
            comparison["price_status"] = "ambiguous_rows"
        else:
            new, prior = now[0], old[0]
            # Row indices describe response ordering, not stable product identity.
            signal_fields = ("price_from", "price_to", "currency", "rating", "rank_group", "rank_absolute",
                             "is_available", "is_amazon_choice", "is_best_seller", "demand_signal")
            comparison["status"] = "unchanged" if all(new.get(k) == prior.get(k) for k in signal_fields) else "observed_product_changed"
            currency, previous_currency = new.get("currency"), prior.get("currency")
            valid_currency = lambda value: isinstance(value, str) and re.fullmatch(r"[A-Z]{3}", value)
            if not valid_currency(currency) or not valid_currency(previous_currency):
                comparison["price_status"] = "unknown_currency"
            elif currency != previous_currency:
                comparison["price_status"] = "currency_changed"
            elif number(new.get("price_from")) is None or number(prior.get("price_from")) is None:
                comparison["price_status"] = "unknown_price"
            elif point_price(new) is None or point_price(prior) is None:
                comparison["price_status"] = "range_observed"
            else:
                comparison["price_delta"] = round(point_price(new) - point_price(prior), 8)
                comparison["price_status"] = "unchanged" if comparison["price_delta"] == 0 else "changed"
            new_rating, old_rating = new.get("rating") or {}, prior.get("rating") or {}
            votes_now, votes_old = number(new_rating.get("votes_count")), number(old_rating.get("votes_count"))
            if votes_now is not None and votes_old is not None:
                comparison["rating_count_delta"] = votes_now - votes_old
            value_now, value_old = number(new_rating.get("value")), number(old_rating.get("value"))
            scale_now, scale_old = number(new_rating.get("rating_max")), number(old_rating.get("rating_max"))
            if value_now is not None and value_old is not None and scale_now is not None and scale_now > 0 and scale_now == scale_old and new_rating.get("rating_type") == old_rating.get("rating_type"):
                comparison["rating_value_delta"] = round(value_now - value_old, 8)
            if type(new.get("is_available")) is bool and type(prior.get("is_available")) is bool:
                comparison["availability_changed"] = new["is_available"] != prior["is_available"]
        comparisons.append(comparison)
    return {
        "previous_observed_at": previous["observed_at"] if previous else None,
        "rows": comparisons,
        "notes": [
            "Compare only the same endpoint, query, location, language, device, operating system and row type.",
            "A price_from with no price_to is a single displayed price; distinct bounds remain a range without a scalar delta.",
            "Multiple rows of one type are not paired; unknown currency or changed currency prevents a numeric price delta.",
            "Rating counts may be rounded or variant-aggregated. Missing rows do not establish stockouts.",
            "No sales or revenue are inferred from changes in rolling-month purchase signals.",
        ],
    }


def report(connection, target_asin, marketplace):
    watch = connection.execute("SELECT * FROM watch WHERE asin=? AND marketplace=?", (target_asin, marketplace)).fetchone()
    if watch is None:
        raise ValueError("product is not on the watchlist")
    series = defaultdict(list)
    for row in connection.execute("""SELECT * FROM snapshots WHERE asin=? AND marketplace=?
            AND family IN ('search', 'detail') ORDER BY observed_at DESC, id DESC""", (target_asin, marketplace)):
        if len(series[row["series"]]) < 2:
            projected = project_observation(json.loads(row["normalized_json"]))
            if projected is not None and projected["family"] == row["family"]:
                series[row["series"]].append(projected)
    observations = []
    for snapshots in series.values():
        if not snapshots:
            continue
        latest, previous = snapshots[0], snapshots[1] if len(snapshots) > 1 else None
        observations.append({"latest": latest, "comparison": compare_product(latest, previous)})
    return {"product": dict(watch), "generated_at": utc(), "series": observations,
            "limitations": [
                "No exact competitor units, revenue or market share are available.",
                "Past-month purchase signals are approximate product signals, not transaction records.",
                "Prices are displayed product prices; shipping, tax and checkout totals are not collected.",
                "Search and detail ratings remain separate series; source counts may aggregate variants.",
                "Every source has its own observation time; missing rows do not establish stockouts.",
            ]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "add", "list", "ingest", "report"):
        sub = commands.add_parser(command)
        sub.add_argument("--db", required=True, help="local SQLite path; parent directory must exist")
        if command in {"add", "report"}:
            sub.add_argument("--asin", required=True)
            sub.add_argument("--marketplace", default="amazon.com")
        if command == "add":
            sub.add_argument("--label")
        if command == "ingest":
            sub.add_argument("--input", required=True, help="saved AIsa batch_use JSON file")
            sub.add_argument("--collected-at", help="ISO timestamp with timezone; defaults to current UTC")
    args = parser.parse_args(argv)
    try:
        if args.command in {"add", "report"}:
            args.asin, args.marketplace = asin(args.asin), market(args.marketplace)
        with db_open(args.db) as connection:
            if args.command == "init":
                output = {"database": str(Path(args.db).resolve()), "initialized": True}
            elif args.command == "add":
                connection.execute("INSERT OR IGNORE INTO watch VALUES (?, ?, ?, ?)",
                                   (args.asin, args.marketplace, args.label, utc()))
                output = dict(connection.execute("SELECT * FROM watch WHERE asin=? AND marketplace=?",
                                                 (args.asin, args.marketplace)).fetchone())
            elif args.command == "list":
                output = [dict(row) for row in connection.execute("SELECT * FROM watch ORDER BY marketplace, asin")]
            elif args.command == "ingest":
                raw = json.loads(Path(args.input).read_text(encoding="utf-8"),
                                 parse_constant=lambda value: (_ for _ in ()).throw(ValueError("invalid JSON number " + value)))
                output = ingest(connection, raw, utc(args.collected_at))
            else:
                output = report(connection, args.asin, args.marketplace)
        print(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))
        return 2 if isinstance(output, dict) and output.get("rejected_calls") else 0
    except (ValueError, OSError, sqlite3.Error) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
