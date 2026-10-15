#!/usr/bin/env python3
"""Topic watchlist management for last30days.

Preferred entrypoint:
    bash scripts/run-watchlist.sh ...
"""

from __future__ import annotations

import argparse
import json
import os
import uuid
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

import store
from lib import costs, http, schema


# --- Webhook Delivery Functions ---

def _deliver_findings(topic_name: str, counts: dict) -> None:
    """Send webhook notification if delivery is configured and there are new findings."""
    channel = store.get_setting("delivery_channel", "")
    if not channel or counts.get("new", 0) == 0:
        return
    
    mode = store.get_setting("delivery_mode", "announce")
    message = _format_delivery_message(topic_name, counts, mode)
    
    try:
        if "hooks.slack.com" in channel:
            _send_slack_webhook(channel, message)
        elif channel.startswith("https://"):
            _send_generic_webhook(channel, message)
    except Exception as e:
        # Don't fail the research run if delivery fails
        print(f"Delivery failed: {e}", file=sys.stderr)


def _format_delivery_message(topic: str, counts: dict, mode: str) -> str:
    """Format notification message based on delivery mode."""
    new = counts.get("new", 0)
    updated = counts.get("updated", 0)
    
    if mode == "announce":
        return f"📰 *last30days update: {topic}*\n{new} new, {updated} updated"
    elif mode == "silent":
        return f"last30days: {new} new findings for '{topic}'"
    else:
        return f"last30days: Research complete for '{topic}'"


def _send_slack_webhook(url: str, text: str) -> None:
    """POST to Slack incoming webhook."""
    # http.post raises http.HTTPError on non-2xx — same fail-loud contract
    # as requests' raise_for_status(). _deliver_findings swallows it.
    http.post(
        url,
        {"text": text},
        headers={"Content-Type": "application/json"},
        timeout=10,
        retries=1,
    )


def _send_generic_webhook(url: str, text: str) -> None:
    """POST JSON payload to generic webhook."""
    http.post(
        url,
        {
            "message": text,
            "source": "last30days",
            "timestamp": time.time(),
        },
        headers={"Content-Type": "application/json"},
        timeout=10,
        retries=1,
    )


# --- Command Handlers ---

def cmd_add(args):
    schedule = "0 8 * * 1" if args.weekly else (args.schedule or "0 8 * * *")
    queries = [query.strip() for query in (args.queries or "").split(",") if query.strip()] or None
    topic = store.add_topic(args.topic, search_queries=queries, schedule=schedule)
    sched_desc = "weekly (Mondays 8am)" if args.weekly else f"daily ({schedule})"
    print(json.dumps({
        "action": "added",
        "topic": topic["name"],
        "schedule": sched_desc,
        "message": f'Added "{topic["name"]}" to watchlist. Schedule: {sched_desc}.',
    }, default=str))


def cmd_remove(args):
    removed = store.remove_topic(args.topic)
    if not removed:
        print(json.dumps({"action": "not_found", "topic": args.topic, "message": f'Topic not found: "{args.topic}"'}))
        return
    remaining = store.list_topics()
    print(json.dumps({
        "action": "removed",
        "topic": args.topic,
        "message": f'Removed "{args.topic}" from watchlist.',
        "remaining": len(remaining),
    }))


def _ledger_dir() -> Path:
    return store._get_db_path().parent / "cost-ledgers" / "watchlist"


def _configured_budget() -> int | None:
    # Old databases contained an automatic $5 default; that is not consent.
    if store.get_setting("daily_budget_authorized") != "true":
        return None
    value = store.get_setting("daily_budget")
    if value is None:
        return None
    return costs.parse_usd(value)


def _daily_state() -> dict:
    today = costs.utc_day()
    current = None
    unresolved = []
    for path in sorted(_ledger_dir().glob("*.json")):
        summary = costs.ledger_summary(path)
        if summary.get("period") == today:
            current = summary
        if summary["unknown_requests"]:
            unresolved.append({"ledger_path": str(path), "request_ids": summary["unknown_requests"]})
    return {
        "utc_day": today,
        "budget_micros_usd": current["budget_micros_usd"] if current else _configured_budget(),
        "known_cost_micros_usd": current["known_cost_micros_usd"] if current else 0,
        "spent_micros_usd": current["spent_micros_usd"] if current else 0,
        "unresolved_ledgers": unresolved,
        "accounting_scope": "watchlist request ledgers; unknown charges from earlier days block new spending",
    }


def _daily_budget(args) -> costs.RunBudget:
    amount = args.budget_usd if args.budget_usd is not None else _configured_budget()
    if amount is None:
        raise costs.CostControlError("Watchlist spending requires --budget-usd or an explicit 'config budget USD'")
    state = _daily_state()
    if state["unresolved_ledgers"]:
        raise costs.CostControlError("Unresolved watchlist charges must be reconciled before another run: "
                                    + ", ".join(row["ledger_path"] for row in state["unresolved_ledgers"]))
    return costs.RunBudget(_ledger_dir() / f"{state['utc_day']}.json", amount,
                           period=state["utc_day"], allow_variable_cost=args.allow_variable_cost)


def cmd_list(args):
    del args
    print(json.dumps({"topics": store.list_topics(), "costs": _daily_state()}, default=str))


def cmd_run_one(args):
    topic = store.get_topic(args.topic)
    if not topic:
        raise SystemExit(f'Topic not found: "{args.topic}"')
    # This directory-level lock also prevents concurrent watchlist runs crossing
    # a UTC day boundary from ignoring an earlier run's unresolved outcome.
    with costs._locked(_ledger_dir() / "watchlist"):
        budget = _daily_budget(args)
        result = _run_topic(topic, budget)
    print(json.dumps(result, default=str))


def cmd_run_all(args):
    topics = [topic for topic in store.list_topics() if topic["enabled"]]
    if not topics:
        print(json.dumps({"message": "No enabled topics to research."}))
        return
    results = []
    with costs._locked(_ledger_dir() / "watchlist"):
        for topic in topics:
            try:
                budget = _daily_budget(args)
                state = budget.summary()
                if state["budget_exceeded"] or state["remaining_micros_usd"] == 0:
                    raise costs.CostControlError("The daily admission budget is exhausted")
            except costs.CostControlError as exc:
                results.append({"topic": topic["name"], "status": "skipped", "reason": str(exc)})
                continue
            results.append(_run_topic(topic, budget))
        state = _daily_state()
    print(json.dumps({"action": "run_all", "results": results, "costs": state}, default=str))


def _run_topic(topic: dict, budget: costs.RunBudget) -> dict:
    start_time = time.time()
    topic_id = topic["id"]
    run_id = store.record_run(topic_id, source_mode="v3", status="running", cost_ledger=str(budget.path))
    child_run_id = uuid.uuid4().hex
    child_env = {**os.environ, "LAST30DAYS_COST_RUN_ID": child_run_id}

    def finish_cost() -> dict:
        summary = costs.run_summary(budget.path, child_run_id)
        amount = summary["run_cost_micros_usd"]
        store.update_run(run_id, cost_micros_usd=amount,
                         cost_status="reported" if amount is not None else "unknown",
                         cost_ledger=str(budget.path))
        return summary

    try:
        search_queries = json.loads(topic["search_queries"]) if topic.get("search_queries") else None
        search_term = search_queries[0] if search_queries else topic["name"]
        command = [sys.executable, str(SCRIPT_DIR / "last30days.py"), search_term,
                   "--emit=json", "--quick", "--lookback-days", "90",
                   "--budget-usd", costs.usd_text(budget.summary()["budget_micros_usd"]),
                   "--cost-ledger", str(budget.path)]
        if budget.allow_variable_cost:
            command.append("--allow-variable-cost")
        result = subprocess.run(command, capture_output=True, text=True, timeout=300, env=child_env)
        duration = time.time() - start_time
        if result.returncode != 0:
            store.update_run(run_id, status="failed", error_message=result.stderr[:500], duration_seconds=duration)
            return {"topic": topic["name"], "status": "failed", "error": result.stderr[:200],
                    "duration": duration, "costs": finish_cost()}
        report = schema.report_from_dict(json.loads(result.stdout))
        findings = store.findings_from_report(report, limit=25)
        counts = store.store_findings(run_id, topic_id, findings)
        store.update_run(run_id, status="completed", duration_seconds=duration,
                         findings_new=counts["new"], findings_updated=counts["updated"])
        summary = finish_cost()
        _deliver_findings(topic["name"], counts)
        return {"topic": topic["name"], "status": "completed", "new": counts["new"],
                "updated": counts["updated"], "duration": duration, "costs": summary}
    except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
        duration = time.time() - start_time
        error = "Research timed out after 300s" if isinstance(exc, subprocess.TimeoutExpired) else str(exc)
        store.update_run(run_id, status="failed", error_message=error[:500], duration_seconds=duration)
        return {"topic": topic["name"], "status": "failed", "error": error, "costs": finish_cost()}


def cmd_config(args):
    if args.key == "budget":
        value = costs.usd_text(costs.parse_usd(args.value))
        store.set_setting("daily_budget", value)
        store.set_setting("daily_budget_authorized", "true")
        print(json.dumps({"action": "config", "key": "daily_budget", "value": value,
                          "limit_semantics": "admission estimate limit; final charges may exceed estimates"}))
        return
    if args.key == "delivery":
        store.set_setting("delivery_channel", str(args.value))
        print(json.dumps({"action": "config", "key": "delivery_channel", "value": str(args.value)}))
        return
    raise SystemExit(f"Unknown config key: {args.key}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the last30days watchlist")
    sub = parser.add_subparsers(dest="command")

    add = sub.add_parser("add")
    add.add_argument("topic")
    add.add_argument("--schedule")
    add.add_argument("--weekly", action="store_true")
    add.add_argument("--queries")
    add.set_defaults(func=cmd_add)

    remove = sub.add_parser("remove")
    remove.add_argument("topic")
    remove.set_defaults(func=cmd_remove)

    list_parser = sub.add_parser("list")
    list_parser.set_defaults(func=cmd_list)

    run_one = sub.add_parser("run-one")
    run_one.add_argument("topic")
    run_one.set_defaults(func=cmd_run_one)

    run_all = sub.add_parser("run-all")
    run_all.set_defaults(func=cmd_run_all)
    for runner in (run_one, run_all):
        runner.add_argument("--budget-usd", type=costs.parse_usd,
                            help="Explicit daily admission budget; final charges may exceed estimates")
        runner.add_argument("--allow-variable-cost", action="store_true",
                            help="Allow provider quotes whose final charge may exceed the estimate")

    config = sub.add_parser("config")
    config.add_argument("key", choices=["delivery", "budget"])
    config.add_argument("value")
    config.set_defaults(func=cmd_config)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    try:
        args.func(args)
    except (costs.CostControlError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
