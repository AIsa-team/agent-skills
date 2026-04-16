#!/usr/bin/env python3
"""
AIsa Multi Search Engine — Python CLI Client
=============================================

A command-line search client that calls AIsa API endpoints for multi-source
search.  Requires the AISA_API_KEY environment variable.

Usage:
    python3 search_client.py web      --query "latest AI news" --count 10
    python3 search_client.py scholar  --query "transformer architecture" --year-from 2024
    python3 search_client.py smart    --query "autonomous agents" --count 10
    python3 search_client.py tavily   --query "AI developments" --depth advanced
    python3 search_client.py extract  --urls "https://example.com/article"
    python3 search_client.py sonar    --query "quantum computing" --model sonar-pro
    python3 search_client.py verity   --query "Is quantum computing ready?"
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

AISA_BASE = "https://api.aisa.one/apis/v1"


def get_api_key() -> str:
    key = os.environ.get("AISA_API_KEY", "")
    if not key:
        print("Error: AISA_API_KEY environment variable is not set.", file=sys.stderr)
        print("Get your key at https://aisa.one", file=sys.stderr)
        sys.exit(1)
    return key


def aisa_post(api_key: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    url = f"{AISA_BASE}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        print(f"API error {e.code} on {path}: {body_text}", file=sys.stderr)
        return {"error": str(e), "status": e.code}


def print_results(data: dict[str, Any], source: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {source} Results")
    print(f"{'='*60}\n")

    if "results" in data and isinstance(data["results"], list):
        for i, r in enumerate(data["results"], 1):
            print(f"  [{i}] {r.get('title', 'Untitled')}")
            if r.get("url"):
                print(f"      URL: {r['url']}")
            if r.get("published_date"):
                print(f"      Date: {r['published_date']}")
            snippet = r.get("content") or r.get("snippet") or ""
            if snippet:
                print(f"      {snippet[:200]}")
            print()

    if "organic_results" in data and isinstance(data["organic_results"], list):
        for i, r in enumerate(data["organic_results"], 1):
            print(f"  [{i}] {r.get('title', 'Untitled')}")
            if r.get("link"):
                print(f"      URL: {r['link']}")
            if r.get("snippet"):
                print(f"      {r['snippet'][:200]}")
            print()

    if "answer" in data:
        print(f"  Answer: {data['answer']}\n")

    if "choices" in data and isinstance(data["choices"], list):
        for c in data["choices"]:
            msg = c.get("message", {})
            if msg.get("content"):
                print(f"  {msg['content'][:1000]}\n")

    if "citations" in data and isinstance(data["citations"], list):
        print("  Citations:")
        for cite in data["citations"]:
            print(f"    - {cite}")
        print()

    if "usage" in data:
        usage = data["usage"]
        if "cost" in usage:
            print(f"  Cost: ${usage['cost']}")
        if "credits_remaining" in usage:
            print(f"  Credits remaining: {usage['credits_remaining']}")
        print()


def cmd_web(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    data = aisa_post(api_key, "/scholar/search/web", {
        "query": args.query,
        "max_num_results": args.count,
    })
    print_results(data, "Web Search")


def cmd_scholar(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    body: dict[str, Any] = {
        "query": args.query,
        "max_num_results": args.count,
    }
    if args.year_from:
        body["as_ylo"] = args.year_from
    if args.year_to:
        body["as_yhi"] = args.year_to
    data = aisa_post(api_key, "/scholar/search/scholar", body)
    print_results(data, "Scholar Search")


def cmd_smart(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    data = aisa_post(api_key, "/scholar/search/smart", {
        "query": args.query,
        "max_num_results": args.count,
    })
    print_results(data, "Smart Search")


def cmd_tavily(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    body: dict[str, Any] = {
        "query": args.query,
        "max_results": args.count,
        "search_depth": args.depth,
    }
    if args.topic:
        body["topic"] = args.topic
    if args.time_range:
        body["time_range"] = args.time_range
    if args.include_answer:
        body["include_answer"] = True
    data = aisa_post(api_key, "/tavily/search", body)
    print_results(data, "Tavily Search")


def cmd_extract(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    urls = [u.strip() for u in args.urls.split(",")]
    data = aisa_post(api_key, "/tavily/extract", {"urls": urls})
    if "results" in data and isinstance(data["results"], list):
        for r in data["results"]:
            print(f"\n{'='*60}")
            print(f"  URL: {r.get('url', 'Unknown')}")
            print(f"{'='*60}")
            content = r.get("raw_content", "")
            print(content[:3000] if content else "(no content)")
    else:
        print(json.dumps(data, indent=2))


def cmd_sonar(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    endpoint_map = {
        "sonar": "/sonar",
        "sonar-pro": "/sonar-pro",
        "sonar-reasoning-pro": "/sonar-reasoning-pro",
        "sonar-deep-research": "/sonar-deep-research",
    }
    endpoint = endpoint_map.get(args.model, "/sonar")
    data = aisa_post(api_key, endpoint, {
        "model": args.model,
        "messages": [{"role": "user", "content": args.query}],
    })
    print_results(data, f"Perplexity ({args.model})")


def cmd_verity(args: argparse.Namespace) -> None:
    """Multi-source search with confidence scoring."""
    api_key = get_api_key()
    count = args.count

    print(f"\nSearching across multiple sources for: \"{args.query}\"\n")

    # Phase 1: Parallel retrieval
    sources: dict[str, dict[str, Any]] = {}
    tasks = {
        "Web": ("/scholar/search/web", {"query": args.query, "max_num_results": count}),
        "Smart": ("/scholar/search/smart", {"query": args.query, "max_num_results": count}),
        "Scholar": ("/scholar/search/scholar", {"query": args.query, "max_num_results": count}),
        "Tavily": ("/tavily/search", {"query": args.query, "max_results": count, "include_answer": True}),
    }

    def fetch(name: str, endpoint: str, body: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        return name, aisa_post(api_key, endpoint, body)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(fetch, name, ep, body): name
            for name, (ep, body) in tasks.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                _, data = future.result()
                sources[name] = data
                print(f"  [OK] {name}")
            except Exception as e:
                print(f"  [FAIL] {name}: {e}")

    # Print individual results
    for name, data in sources.items():
        print_results(data, name)

    # Phase 2: Confidence scoring
    total_sources = len(sources)
    total_results = 0
    for d in sources.values():
        if isinstance(d.get("results"), list):
            total_results += len(d["results"])
        if isinstance(d.get("organic_results"), list):
            total_results += len(d["organic_results"])

    score = 0.0
    score += (total_sources / len(tasks)) * 40
    expected = count * len(tasks)
    score += min(total_results / expected, 1.0) * 35
    has_scholar = any(isinstance(d.get("organic_results"), list) for d in sources.values())
    has_web = any(
        isinstance(d.get("results"), list) and not isinstance(d.get("organic_results"), list)
        for d in sources.values()
    )
    score += ((0.5 if has_scholar else 0) + (0.5 if has_web else 0)) * 15
    score += 10 if total_sources > 0 else 0
    score = min(round(score), 100)

    levels = {90: "Very High", 70: "High", 50: "Medium", 30: "Low", 0: "Very Low"}
    level = "Very Low"
    for threshold in sorted(levels.keys(), reverse=True):
        if score >= threshold:
            level = levels[threshold]
            break

    print(f"\n{'='*60}")
    print(f"  Confidence Assessment")
    print(f"{'='*60}")
    print(f"  Score:            {score}/100")
    print(f"  Level:            {level}")
    print(f"  Sources queried:  {len(tasks)}")
    print(f"  Sources OK:       {total_sources}")
    print(f"  Total results:    {total_results}")

    # Phase 3: Explanation
    if sources:
        print(f"\n  Generating synthesis...")
        explain_data = aisa_post(api_key, "/scholar/explain", {
            "results": list(sources.values()),
            "language": "en",
            "format": "summary",
        })
        if "summary" in explain_data:
            print(f"\n  AI Synthesis:")
            print(f"  {explain_data['summary']}")
        if isinstance(explain_data.get("citations"), list):
            print(f"\n  Citations:")
            for c in explain_data["citations"]:
                print(f"    - {c}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AIsa Multi Search Engine CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # web
    p_web = sub.add_parser("web", help="Web search")
    p_web.add_argument("--query", "-q", required=True)
    p_web.add_argument("--count", "-c", type=int, default=10)
    p_web.set_defaults(func=cmd_web)

    # scholar
    p_scholar = sub.add_parser("scholar", help="Academic paper search")
    p_scholar.add_argument("--query", "-q", required=True)
    p_scholar.add_argument("--count", "-c", type=int, default=10)
    p_scholar.add_argument("--year-from", type=int, default=None)
    p_scholar.add_argument("--year-to", type=int, default=None)
    p_scholar.set_defaults(func=cmd_scholar)

    # smart
    p_smart = sub.add_parser("smart", help="Smart hybrid search")
    p_smart.add_argument("--query", "-q", required=True)
    p_smart.add_argument("--count", "-c", type=int, default=10)
    p_smart.set_defaults(func=cmd_smart)

    # tavily
    p_tavily = sub.add_parser("tavily", help="Tavily web search")
    p_tavily.add_argument("--query", "-q", required=True)
    p_tavily.add_argument("--count", "-c", type=int, default=5)
    p_tavily.add_argument("--depth", default="basic", choices=["basic", "advanced", "fast", "ultra-fast"])
    p_tavily.add_argument("--topic", default=None, choices=["general", "news", "finance"])
    p_tavily.add_argument("--time-range", default=None)
    p_tavily.add_argument("--include-answer", action="store_true")
    p_tavily.set_defaults(func=cmd_tavily)

    # extract
    p_extract = sub.add_parser("extract", help="Extract content from URLs")
    p_extract.add_argument("--urls", "-u", required=True, help="Comma-separated URLs")
    p_extract.set_defaults(func=cmd_extract)

    # sonar (perplexity)
    p_sonar = sub.add_parser("sonar", help="Perplexity deep research")
    p_sonar.add_argument("--query", "-q", required=True)
    p_sonar.add_argument(
        "--model", "-m", default="sonar",
        choices=["sonar", "sonar-pro", "sonar-reasoning-pro", "sonar-deep-research"],
    )
    p_sonar.set_defaults(func=cmd_sonar)

    # verity (multi-source)
    p_verity = sub.add_parser("verity", help="Multi-source search with confidence scoring")
    p_verity.add_argument("--query", "-q", required=True)
    p_verity.add_argument("--count", "-c", type=int, default=5)
    p_verity.set_defaults(func=cmd_verity)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
