#!/usr/bin/env python3
# ruff: noqa: E402
"""last30days CLI. Version lives in lib/__init__.py (__version__)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from contextlib import nullcontext
from pathlib import Path

MIN_PYTHON = (3, 11)


def ensure_supported_python(version_info: tuple[int, int, int] | object | None = None) -> None:
    if version_info is None:
        version_info = sys.version_info
    major, minor, micro = tuple(version_info[:3])
    if (major, minor) >= MIN_PYTHON:
        return
    sys.stderr.write(
        "last30days v1 requires Python 3.11+.\n"
        f"Detected Python {major}.{minor}.{micro}.\n"
        "Set LAST30DAYS_PYTHON to a Python 3.11+ interpreter and rerun the shell entrypoint.\n"
    )
    raise SystemExit(1)


ensure_supported_python()

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from lib import costs, env, pipeline, planner, providers, render, schema, ui


def parse_search_flag(raw: str) -> list[str]:
    sources = []
    for source in raw.split(","):
        source = source.strip().lower()
        if not source:
            continue
        normalized = pipeline.SEARCH_ALIAS.get(source, source)
        if normalized not in getattr(pipeline, "SUPPORTED_SOURCES", pipeline.MOCK_AVAILABLE_SOURCES):
            raise SystemExit(f"Unknown search source: {source}")
        if normalized not in sources:
            sources.append(normalized)
    if not sources:
        raise SystemExit("--search requires at least one source.")
    return sources


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "last30days"


def save_output(report: schema.Report, emit: str, save_dir: str, suffix: str = "") -> Path:
    from datetime import datetime
    path = Path(save_dir).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    slug = slugify(report.topic)
    extension = "json" if emit == "json" else "md"
    suffix_part = f"-{suffix}" if suffix else ""
    out_path = path / f"{slug}-raw{suffix_part}.{extension}"
    if out_path.exists():
        out_path = path / f"{slug}-raw{suffix_part}-{datetime.now().strftime('%Y-%m-%d')}.{extension}"
    # Save a user-requested debug artifact only when --save-dir is provided.
    if emit == "json":
        content = emit_output(report, emit)
    else:
        content = render.render_full(report)
    out_path.write_text(content)
    return out_path


def emit_output(report: schema.Report, emit: str, fun_level: str = "medium") -> str:
    if emit == "json":
        return json.dumps(schema.to_dict(report), indent=2, sort_keys=True)
    if emit in {"compact", "md"}:
        return render.render_compact(report, fun_level=fun_level)
    if emit == "context":
        return render.render_context(report)
    raise SystemExit(f"Unsupported emit mode: {emit}")


def persist_report(report: schema.Report) -> dict[str, int]:
    import store

    store.init_db()
    topic_row = store.add_topic(report.topic)
    topic_id = topic_row["id"]
    source_mode = ",".join(sorted(report.items_by_source)) or "v3"
    run_costs = report.artifacts.get("costs", {})
    charged = run_costs.get("run_cost_micros_usd")
    cost_fields = {
        "cost_micros_usd": charged,
        "cost_status": "reported" if charged is not None else "unknown",
        "cost_ledger": run_costs.get("ledger_path"),
    }
    run_id = store.record_run(topic_id, source_mode=source_mode, status="running", **cost_fields)
    try:
        findings = store.findings_from_report(report)
        counts = store.store_findings(run_id, topic_id, findings)
        store.update_run(
            run_id,
            status="completed",
            findings_new=counts["new"],
            findings_updated=counts["updated"],
            **cost_fields,
        )
        return counts
    except Exception as exc:
        store.update_run(run_id, status="failed", error_message=str(exc)[:500], **cost_fields)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Research a topic across live social, market, and grounded web sources.", allow_abbrev=False)
    parser.add_argument("topic", nargs="*", help="Research topic")
    parser.add_argument("--emit", default="compact", choices=["compact", "json", "context", "md"])
    parser.add_argument("--search", help="Comma-separated source list")
    depth = parser.add_mutually_exclusive_group()
    depth.add_argument("--quick", action="store_true", help="Lower-latency retrieval profile")
    depth.add_argument("--deep", action="store_true", help="Higher-recall retrieval profile")
    parser.add_argument("--debug", action="store_true", help="Enable HTTP debug logging")
    parser.add_argument("--mock", action="store_true", help="Use mock retrieval fixtures")
    parser.add_argument("--diagnose", action="store_true", help="Print configured providers and sources without checking live availability")
    parser.add_argument("--budget-usd", dest="budget_micros", type=costs.parse_usd,
                        help="Required budget for hosted research; admission uses estimates, actual variable charges can exceed it")
    parser.add_argument("--cost-ledger", help="Durable JSON cost ledger; reuse to share a previously authorized budget")
    parser.add_argument("--allow-variable-cost", action="store_true",
                        help="Allow requests whose actual charge may exceed the admission estimate")
    parser.add_argument("--save-dir", help="Optional directory for saving the rendered output")
    parser.add_argument("--store", action="store_true", help="Persist ranked findings to the SQLite research store")
    parser.add_argument("--x-handle", help="X handle for targeted supplemental search")
    parser.add_argument("--x-related", help="Comma-separated related X handles (searched with lower weight)")
    parser.add_argument("--web-backend", default="auto",
                        choices=["auto", "aisa", "none"],
                        help="Web search backend (default: auto, prefers AISA)")
    parser.add_argument("--deep-research", action="store_true",
                        help="Use the AISA-hosted deep web research path for in-depth analysis.")
    parser.add_argument("--plan", help="JSON query plan (skips internal LLM planner). Can be a JSON string or a file path.")
    parser.add_argument("--save-suffix", help="Suffix for saved output filename (e.g., 'aisa' → kanye-west-raw-aisa.md)")
    parser.add_argument("--subreddits", help="Comma-separated subreddit names to search (e.g., SaaS,Entrepreneur)")
    parser.add_argument("--tiktok-hashtags", help="Comma-separated TikTok hashtags without # (e.g., tella,screenrecording)")
    parser.add_argument("--tiktok-creators", help="Comma-separated TikTok creator handles (e.g., TellaHQ,taborplace)")
    parser.add_argument("--ig-creators", help="Comma-separated Instagram creator handles (e.g., tella.tv,laborstories)")
    parser.add_argument("--lookback-days", type=int, default=30, help="Number of days to look back for research (default: 30, watchlist uses 90)")
    parser.add_argument("--auto-resolve", action="store_true",
                        help="Use web search to discover subreddits/handles before planning (for platforms without WebSearch)")
    parser.add_argument("--github-user", help="GitHub username for person-mode search (e.g., steipete)")
    parser.add_argument("--github-repo", help="Comma-separated owner/repo for project-mode search (e.g., openclaw/openclaw,paperclipai/paperclip)")
    return parser


def _missing_sources_for_promo(diag: dict[str, object]) -> str | None:
    available = set(diag.get("available_sources") or [])
    missing = []
    if "reddit" not in available:
        missing.append("reddit")
    if "x" not in available:
        missing.append("x")
    if "grounding" not in available:
        missing.append("web")
    if not missing:
        return None
    if "reddit" in missing and "x" in missing:
        return "both"
    return missing[0]


def _show_runtime_ui(report: schema.Report, progress: ui.ProgressDisplay, diag: dict[str, object]) -> None:
    counts = {source: len(items) for source, items in report.items_by_source.items()}
    display_sources = list(
        dict.fromkeys(
            [
                *report.query_plan.source_weights.keys(),
                *report.items_by_source.keys(),
                *report.errors_by_source.keys(),
            ]
        )
    )
    progress.end_processing()
    progress.show_complete(
        source_counts=counts,
        display_sources=display_sources,
    )
    promo = _missing_sources_for_promo(diag)
    if promo:
        progress.show_promo(promo, diag=diag)


def _validate_arguments(parser: argparse.ArgumentParser, args, extra_argv: list[str]):
    """Complete structural validation before config discovery or any I/O to providers."""
    topic = " ".join(args.topic).strip()
    is_setup = topic.lower() == "setup"
    if extra_argv and (not is_setup or any(flag not in {"--openclaw", "--github", "--device-auth"} for flag in extra_argv)):
        parser.error(f"unrecognized arguments: {' '.join(extra_argv)}")
    if is_setup and len(extra_argv) > 1:
        parser.error("setup accepts only one setup mode")
    if is_setup and args.mock:
        parser.error("--mock cannot be combined with setup")
    if not 1 <= args.lookback_days <= 365:
        parser.error("--lookback-days must be between 1 and 365")
    for name in ("deep_research", "tiktok_hashtags", "tiktok_creators", "ig_creators"):
        if getattr(args, name) is not None and getattr(args, name) is not False:
            parser.error(f"--{name.replace('_', '-')} is unsupported by the current retrieval backend")
    requested_sources = parse_search_flag(args.search) if args.search else None
    if args.mock and requested_sources:
        unsupported = set(requested_sources) - set(pipeline.MOCK_AVAILABLE_SOURCES)
        if unsupported:
            parser.error(f"--mock has no fixture for: {', '.join(sorted(unsupported))}")
    external_plan = None
    if args.plan is not None:
        try:
            plan_text = args.plan
            if not plan_text.lstrip().startswith(("{", "[")):
                plan_text = Path(plan_text).expanduser().read_text(encoding="utf-8")
            raw_plan = json.loads(plan_text)
            external_plan = planner.validate_external_plan(
                raw_plan, list(getattr(pipeline, "SUPPORTED_SOURCES", pipeline.MOCK_AVAILABLE_SOURCES)),
            )
        except (OSError, ValueError) as exc:
            parser.error(f"Invalid --plan: {exc}")
    if not topic and not args.diagnose:
        parser.error("a research topic is required")
    return topic, requested_sources, external_plan


def _run_setup(config: dict, extra_argv: list[str]) -> int:
    from lib import setup_wizard
    if "--openclaw" in extra_argv:
        print(json.dumps(setup_wizard.run_openclaw_setup(config)))
        return 0
    if "--github" in extra_argv:
        print(json.dumps(setup_wizard.run_github_auth()))
        return 0
    if "--device-auth" in extra_argv:
        print(json.dumps(setup_wizard.run_full_device_auth()))
        return 0
    sys.stderr.write("Running auto-setup...\n")
    results = setup_wizard.run_auto_setup(config)
    chosen_models = None
    already_configured = config.get("AISA_MODEL") or (
        config.get("LAST30DAYS_PLANNER_MODEL") and config.get("LAST30DAYS_RERANK_MODEL")
    )
    if results.get("aisa_configured") and not already_configured:
        chosen_models = setup_wizard.select_models_interactive(config["AISA_API_KEY"])
    if env.CONFIG_FILE is not None:
        results["env_written"] = setup_wizard.write_setup_config(env.CONFIG_FILE, models=chosen_models)
        results["env_path"] = str(env.CONFIG_FILE)
    if chosen_models:
        results["models"] = chosen_models
    sys.stderr.write(setup_wizard.get_setup_status_text(results) + "\n")
    return 0


def _run_research(args, config: dict, topic: str, requested_sources, external_plan, depth: str):
    x_related = [h.strip() for h in args.x_related.split(",") if h.strip()] if args.x_related else None
    subreddits = [s.strip().removeprefix("r/") for s in args.subreddits.split(",") if s.strip()] if args.subreddits else None
    # Mock execution never invokes discovery or any provider. Explicit plans already contain queries.
    if args.auto_resolve and not args.mock and external_plan is None:
        from lib import resolve
        resolution = resolve.auto_resolve(topic, config)
        subreddits = subreddits or resolution.get("subreddits")
        args.x_handle = args.x_handle or resolution.get("x_handle")
        args.github_user = args.github_user or resolution.get("github_user")
        args.github_repo = args.github_repo or ",".join(resolution.get("github_repos") or [])
        if resolution.get("context"):
            config["_auto_resolve_context"] = resolution["context"]
    github_user = args.github_user.lstrip("@").lower() if args.github_user else None
    github_repos = [r.strip() for r in args.github_repo.split(",") if r.strip()] if args.github_repo else None
    return pipeline.run(
        topic=topic, config=config, depth=depth, requested_sources=requested_sources,
        mock=args.mock, x_handle=args.x_handle, x_related=x_related,
        web_backend=args.web_backend, external_plan=external_plan, subreddits=subreddits,
        lookback_days=args.lookback_days, github_user=github_user, github_repos=github_repos,
    )


def main() -> int:
    parser = build_parser()
    args, extra_argv = parser.parse_known_args()
    topic, requested_sources, external_plan = _validate_arguments(parser, args, extra_argv)
    if args.debug:
        os.environ["LAST30DAYS_DEBUG"] = "1"
    config = env.get_config()
    if topic.lower() == "setup":
        return _run_setup(config, extra_argv)
    diag = pipeline.diagnose(config, requested_sources)
    if args.diagnose:
        print(json.dumps(diag, indent=2, sort_keys=True))
        return 0
    depth = "deep" if args.deep else "quick" if args.quick else "default"
    hosted_sources = {"x", "youtube", "tiktok", "instagram", "threads", "pinterest", "polymarket", "grounding"}
    uses_hosted_retrieval = (
        requested_sources is None or bool(hosted_sources.intersection(requested_sources))
        or args.auto_resolve or args.web_backend == "aisa"
    )
    hosted = bool(config.get("AISA_API_KEY")) and not args.mock and uses_hosted_retrieval
    if requested_sources and not uses_hosted_retrieval:
        # An ambient AIsa key/model pin must not turn explicit public-source research
        # into a hosted reasoning request. Preserve other credentials, including GitHub.
        config = {**config, "AISA_API_KEY": None}
    if hosted and args.budget_micros is None and not args.cost_ledger:
        parser.error("hosted research requires --budget-usd or an existing --cost-ledger with an authorized budget")
    if not args.mock:
        try:
            providers.resolve_runtime(config, depth)
        except (ValueError, RuntimeError) as exc:
            parser.error(str(exc))
    budget = None
    progress = ui.ProgressDisplay(topic, show_banner=True)
    progress.start_processing()
    try:
        if hosted or args.cost_ledger or args.budget_micros is not None:
            ledger_path = args.cost_ledger or str(
                Path.home() / ".local" / "state" / "last30days" / "costs" / f"{uuid.uuid4().hex}.json"
            )
            budget = costs.RunBudget(
                ledger_path, args.budget_micros, allow_variable_cost=args.allow_variable_cost,
                run_id=os.environ.get("LAST30DAYS_COST_RUN_ID"),
            )
        with costs.activate(budget) if budget is not None else nullcontext():
            started = time.monotonic()
            report = _run_research(args, config, topic, requested_sources, external_plan, depth)
            sys.stderr.write(f"[last30days] pipeline done in {time.monotonic() - started:.2f}s\n")
        report.artifacts["costs"] = budget.summary() if budget is not None else _no_cost_summary()
        if report.artifacts["costs"].get("last_refusal"):
            report.warnings.append(
                "Cost controls declined hosted operations; planning/ranking may use local fallbacks. "
                + report.artifacts["costs"]["last_refusal"]
            )
        if hosted and report.provider_runtime.reasoning_provider == "local":
            report.warnings.append("Reasoning model pins are incomplete; deterministic planning and local ranking were used.")
        _show_runtime_ui(report, progress, diag)
        if args.store:
            counts = persist_report(report)
            sys.stderr.write(f"[last30days] Stored {counts['new']} new, {counts['updated']} updated findings\n")
        rendered = emit_output(report, args.emit, fun_level=config.get("FUN_LEVEL", "medium").lower())
        if args.save_dir:
            save_path = save_output(report, args.emit, args.save_dir, suffix=args.save_suffix or "")
            sys.stderr.write(f"[last30days] Saved output to {save_path}\n")
        print(rendered)
        return 0
    except Exception as exc:
        progress.end_processing()
        progress.show_error(str(exc))
        return 1
    finally:
        summary = budget.summary() if budget is not None else _no_cost_summary()
        sys.stderr.write("[last30days] costs " + json.dumps(summary, sort_keys=True) + "\n")


def _no_cost_summary() -> dict:
    return {
        "spent_micros_usd": 0, "known_cost_micros_usd": 0,
        "remaining_micros_usd": None, "unknown_requests": [],
        "ledger_path": None, "budget_micros_usd": None,
        "run_cost_micros_usd": 0, "run_known_cost_micros_usd": 0,
        "run_request_count": 0, "run_unknown_requests": [],
        "request_count": 0, "budget_exceeded": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
