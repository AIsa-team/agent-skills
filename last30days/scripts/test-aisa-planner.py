#!/usr/bin/env python3
"""End-to-end AISA planner request probe for last30days v1.0.2.

This script mirrors the current planner -> provider -> AISA Chat path:
pipeline -> planner.plan_query() -> providers.AIsaClient -> aisa.chat_completion()

Usage:
    AISA_API_KEY=... /usr/local/python3.12/bin/python3.12 scripts/test-aisa-planner.py \
      --topic "OpenAI Agents SDK" \
      --depth quick \
      --available x,youtube,grounding,reddit,hackernews,polymarket \
      --requested x,youtube,grounding
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from lib import aisa, http, planner, providers  # noqa: E402


def _csv_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe the live AISA planner request used by last30days.")
    parser.add_argument("--topic", required=True, help="Research topic passed to the planner.")
    parser.add_argument("--depth", default="quick", choices=["quick", "default", "deep"])
    parser.add_argument(
        "--available",
        default="reddit,x,youtube,hackernews,polymarket,grounding",
        help="Comma-separated available sources as seen by planner.",
    )
    parser.add_argument(
        "--requested",
        default="",
        help="Comma-separated requested sources. Leave empty for auto.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("LAST30DAYS_PLANNER_MODEL") or providers.AISA_DEFAULT,
        help="AISA chat model to test.",
    )
    parser.add_argument(
        "--context",
        default="",
        help="Optional web-resolved context appended to the planner prompt.",
    )
    parser.add_argument(
        "--print-prompt",
        action="store_true",
        help="Print the full planner prompt before sending.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    api_key = os.environ.get("AISA_API_KEY", "").strip()
    if not api_key:
        sys.stderr.write("AISA_API_KEY is required.\n")
        return 2

    available_sources = _csv_list(args.available)
    requested_sources = _csv_list(args.requested) or None

    prompt = planner._build_prompt(
        args.topic,
        available_sources,
        requested_sources,
        args.depth,
    )
    if args.context:
        prompt += f"\n\nCurrent context (from web search): {args.context}"

    payload: dict[str, object] = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    print("[Planner Probe] endpoint=", aisa.AISA_CHAT_COMPLETIONS_URL, sep="")
    print("[Planner Probe] timeout=", f"{aisa.AISA_CHAT_TIMEOUT}s", sep="")
    print("[Planner Probe] retries=", aisa.AISA_CHAT_RETRIES, sep="")
    print("[Planner Probe] model=", args.model, sep="")
    print("[Planner Probe] topic=", args.topic, sep="")
    print("[Planner Probe] depth=", args.depth, sep="")
    print("[Planner Probe] available_sources=", json.dumps(available_sources, ensure_ascii=False), sep="")
    print(
        "[Planner Probe] requested_sources=",
        json.dumps(requested_sources, ensure_ascii=False),
        sep="",
    )
    print("[Planner Probe] prompt_chars=", len(prompt), sep="")
    print("[Planner Probe] request_payload=")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    if args.print_prompt:
        print("[Planner Probe] full_prompt=")
        print(prompt)

    start = time.time()
    try:
        response = aisa.chat_completion(
            api_key,
            args.model,
            prompt,
            response_mime_type="application/json",
        )
        elapsed = time.time() - start
        text = providers.extract_openai_text(response)
        parsed = providers.extract_json(text) if text else {}
        print(f"[Planner Probe] elapsed={elapsed:.2f}s")
        print("[Planner Probe] response_text=")
        print(text)
        print("[Planner Probe] parsed_json=")
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:  # pragma: no cover - runtime probe
        elapsed = time.time() - start
        error_class = http.classify_error(exc)
        print(f"[Planner Probe] elapsed={elapsed:.2f}s", file=sys.stderr)
        print(
            f"[Planner Probe] failed class={error_class} type={type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
