#!/usr/bin/env python3
"""
OpenClaw Search - AIsa API Client.

Usage:
    python search_client.py web --query <query> [--count <n>]
    python search_client.py scholar --query <query> [--count <n>] [--year-from <y>] [--year-to <y>]
    python search_client.py smart --query <query> [--count <n>]
    python search_client.py sonar --query <query> [--system <instruction>]
    python search_client.py sonar-pro --query <query> [--system <instruction>]
    python search_client.py sonar-reasoning-pro --query <query> [--system <instruction>]
    python search_client.py sonar-deep-research --query <query> [--system <instruction>]
    python search_client.py tavily-search --query <query>
    python search_client.py tavily-extract --urls <url1,url2,...>
    python search_client.py verity --query <query> [--count <n>]
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional


class SearchClient:
    """OpenClaw Search API client."""

    BASE_URL = "https://api.aisa.one/apis/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("AISA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "AISA_API_KEY is required. Set it via environment variable or pass to constructor."
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 120,
        retries: int = 0,
        retry_delay_seconds: int = 5,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the AIsa API."""
        url = f"{self.BASE_URL}{endpoint}"

        if params:
            query_string = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None}
            )
            url = f"{url}?{query_string}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenClaw-Search/2.0",
        }

        request_data = None
        if data is not None:
            request_data = json.dumps(data).encode("utf-8")

        if method == "POST" and request_data is None:
            request_data = b"{}"

        req = urllib.request.Request(url, data=request_data, headers=headers, method=method)

        attempts = retries + 1
        for attempt in range(1, attempts + 1):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8")
                if e.code in {502, 503, 504} and attempt < attempts:
                    time.sleep(retry_delay_seconds)
                    continue
                try:
                    error_data = json.loads(error_body)
                except json.JSONDecodeError:
                    error_data = {
                        "success": False,
                        "error": {"code": str(e.code), "message": error_body},
                    }

                if e.code == 504 and endpoint == "/perplexity/sonar-deep-research":
                    error_data = self._friendly_deep_research_timeout(
                        attempts=attempt, timeout=timeout, error_data=error_data
                    )
                return error_data
            except urllib.error.URLError as e:
                if attempt < attempts:
                    time.sleep(retry_delay_seconds)
                    continue
                error_data = {
                    "success": False,
                    "error": {"code": "NETWORK_ERROR", "message": str(e.reason)},
                }
                if endpoint == "/perplexity/sonar-deep-research":
                    error_data = self._friendly_deep_research_timeout(
                        attempts=attempt, timeout=timeout, error_data=error_data
                    )
                return error_data

        return {
            "success": False,
            "error": {"code": "UNKNOWN_ERROR", "message": "Request failed unexpectedly."},
        }

    @staticmethod
    def _friendly_deep_research_timeout(
        attempts: int, timeout: int, error_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rewrite deep-research timeout errors into a more actionable message."""
        base_error = error_data.get("error", {})
        code = str(base_error.get("code", "TIMEOUT"))
        original_message = base_error.get("message", "Timed out")
        return {
            "success": False,
            "error": {
                "code": code,
                "message": (
                    "Sonar Deep Research timed out after "
                    f"{attempts} attempt(s) with a {timeout}s timeout per attempt. "
                    "The endpoint appears reachable, but the research job did not finish in time. "
                    "Try a narrower prompt, retry later, or switch to sonar-pro / sonar-reasoning-pro "
                    "for a faster response."
                ),
                "details": original_message,
            },
        }

    def _perplexity_request(
        self,
        endpoint: str,
        model: str,
        query: str,
        system: Optional[str] = None,
        timeout: int = 120,
        retries: int = 0,
        retry_delay_seconds: int = 5,
    ) -> Dict[str, Any]:
        """Send a minimal OpenAI-style messages payload to a Perplexity endpoint."""
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": query})
        return self._request(
            "POST",
            endpoint,
            data={"model": model, "messages": messages},
            timeout=timeout,
            retries=retries,
            retry_delay_seconds=retry_delay_seconds,
        )

    # Search APIs

    def web_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/scholar/search/web",
            params={"query": query, "max_num_results": max_results},
        )

    def scholar_search(
        self,
        query: str,
        max_results: int = 10,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> Dict[str, Any]:
        params = {"query": query, "max_num_results": max_results}
        if year_from:
            params["as_ylo"] = year_from
        if year_to:
            params["as_yhi"] = year_to
        return self._request("POST", "/scholar/search/scholar", params=params)

    def smart_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/scholar/search/smart",
            params={"query": query, "max_num_results": max_results},
        )

    def sonar(self, query: str, system: Optional[str] = None) -> Dict[str, Any]:
        return self._perplexity_request("/perplexity/sonar", "sonar", query, system)

    def sonar_pro(self, query: str, system: Optional[str] = None) -> Dict[str, Any]:
        return self._perplexity_request("/perplexity/sonar-pro", "sonar-pro", query, system)

    def sonar_reasoning_pro(self, query: str, system: Optional[str] = None) -> Dict[str, Any]:
        return self._perplexity_request(
            "/perplexity/sonar-reasoning-pro", "sonar-reasoning-pro", query, system
        )

    def sonar_deep_research(self, query: str, system: Optional[str] = None) -> Dict[str, Any]:
        return self._perplexity_request(
            "/perplexity/sonar-deep-research",
            "sonar-deep-research",
            query,
            system,
            timeout=180,
            retries=2,
            retry_delay_seconds=6,
        )

    def explain_results(
        self, results: List[Dict[str, Any]], language: str = "en", output_format: str = "summary"
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/scholar/explain",
            data={"results": results, "language": language, "format": output_format},
        )

    # Tavily APIs

    def tavily_search(self, query: str) -> Dict[str, Any]:
        return self._request("POST", "/tavily/search", data={"query": query})

    def tavily_extract(self, urls: List[str]) -> Dict[str, Any]:
        return self._request("POST", "/tavily/extract", data={"urls": urls})

    def tavily_crawl(self, url: str, max_depth: int = 2) -> Dict[str, Any]:
        return self._request("POST", "/tavily/crawl", data={"url": url, "max_depth": max_depth})

    def tavily_map(self, url: str) -> Dict[str, Any]:
        return self._request("POST", "/tavily/map", data={"url": url})

    # Verity-style search

    def verity_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Multi-source retrieval with a simple confidence score.

        This mode intentionally stays retrieval-focused and does not depend on the
        newer Perplexity endpoints so downstream consumers can still inspect raw
        source sets from scholar, web, hybrid scholar, and Tavily.
        """
        sources: Dict[str, Any] = {}
        errors: List[str] = []

        def fetch_scholar():
            return ("scholar", self.scholar_search(query, max_results))

        def fetch_web():
            return ("web", self.web_search(query, max_results))

        def fetch_smart():
            return ("smart", self.smart_search(query, max_results))

        def fetch_tavily():
            return ("tavily", self.tavily_search(query))

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(fetch_scholar),
                executor.submit(fetch_web),
                executor.submit(fetch_smart),
                executor.submit(fetch_tavily),
            ]

            for future in as_completed(futures):
                try:
                    source_name, result = future.result()
                    sources[source_name] = result
                except Exception as exc:
                    errors.append(str(exc))

        confidence = self._calculate_confidence(sources)

        return {
            "query": query,
            "confidence": confidence,
            "confidence_level": self._confidence_level(confidence["score"]),
            "sources": sources,
            "result_count": {
                source: len(data.get("results", data.get("data", [])))
                if isinstance(data, dict)
                else 0
                for source, data in sources.items()
            },
            "errors": errors if errors else None,
        }

    def _calculate_confidence(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        score = 0.0
        breakdown: Dict[str, Any] = {}

        source_quality = 0.0

        scholar_data = sources.get("scholar", {})
        if isinstance(scholar_data, dict) and scholar_data.get("results"):
            scholar_count = len(scholar_data.get("results", []))
            source_quality += min(40, scholar_count * 8)
            breakdown["scholar_results"] = scholar_count

        web_data = sources.get("web", {})
        if isinstance(web_data, dict) and web_data.get("results"):
            web_count = len(web_data.get("results", []))
            source_quality += min(20, web_count * 2)
            breakdown["web_results"] = web_count

        smart_data = sources.get("smart", {})
        if isinstance(smart_data, dict) and smart_data.get("results"):
            smart_count = len(smart_data.get("results", []))
            source_quality += min(20, smart_count * 2)
            breakdown["smart_results"] = smart_count

        tavily_data = sources.get("tavily", {})
        if isinstance(tavily_data, dict) and tavily_data.get("results"):
            tavily_count = len(tavily_data.get("results", []))
            source_quality += min(10, tavily_count)
            breakdown["tavily_results"] = tavily_count

        source_quality_score = min(40, source_quality * 0.4)
        breakdown["source_quality"] = round(source_quality_score, 2)
        score += source_quality_score

        sources_with_data = sum(
            1
            for source in sources.values()
            if isinstance(source, dict) and (source.get("results") or source.get("data"))
        )
        agreement_score = (sources_with_data / 4) * 35
        breakdown["agreement"] = round(agreement_score, 2)
        breakdown["sources_responding"] = sources_with_data
        score += agreement_score

        total_results = sum(
            len(source.get("results", source.get("data", [])))
            for source in sources.values()
            if isinstance(source, dict)
        )
        data_score = min(15, total_results * 0.5)
        breakdown["data_availability"] = round(data_score, 2)
        breakdown["total_results"] = total_results
        score += data_score

        no_errors = all(
            isinstance(source, dict) and source.get("success", True) is not False
            for source in sources.values()
        )
        error_score = 10 if no_errors else 0
        breakdown["no_errors"] = error_score
        score += error_score

        return {"score": round(min(100, score), 1), "breakdown": breakdown}

    @staticmethod
    def _confidence_level(score: float) -> str:
        if score >= 90:
            return "Very High"
        if score >= 70:
            return "High"
        if score >= 50:
            return "Medium"
        if score >= 30:
            return "Low"
        return "Very Low"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenClaw Search - structured search plus Perplexity Sonar endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s web --query "AI frameworks"
    %(prog)s scholar --query "transformer models" --year-from 2024
    %(prog)s sonar-pro --query "Compare coding agents with citations"
    %(prog)s verity --query "Is quantum computing enterprise-ready?"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Search type")

    web = subparsers.add_parser("web", help="Web search")
    web.add_argument("--query", "-q", required=True, help="Search query")
    web.add_argument("--count", "-c", type=int, default=10, help="Max results")

    scholar = subparsers.add_parser("scholar", help="Academic paper search")
    scholar.add_argument("--query", "-q", required=True, help="Search query")
    scholar.add_argument("--count", "-c", type=int, default=10, help="Max results")
    scholar.add_argument("--year-from", type=int, help="Year lower bound")
    scholar.add_argument("--year-to", type=int, help="Year upper bound")

    smart = subparsers.add_parser("smart", help="Hybrid scholar search")
    smart.add_argument("--query", "-q", required=True, help="Search query")
    smart.add_argument("--count", "-c", type=int, default=10, help="Max results")

    for command_name, help_text in [
        ("sonar", "Perplexity Sonar"),
        ("sonar-pro", "Perplexity Sonar Pro"),
        ("sonar-reasoning-pro", "Perplexity Sonar Reasoning Pro"),
        ("sonar-deep-research", "Perplexity Sonar Deep Research"),
    ]:
        subparser = subparsers.add_parser(command_name, help=help_text)
        subparser.add_argument("--query", "-q", required=True, help="User query")
        subparser.add_argument("--system", help="Optional system instruction")

    tavily_search = subparsers.add_parser("tavily-search", help="Tavily search")
    tavily_search.add_argument("--query", "-q", required=True, help="Search query")

    tavily_extract = subparsers.add_parser("tavily-extract", help="Extract content from URLs")
    tavily_extract.add_argument("--urls", "-u", required=True, help="URLs (comma-separated)")

    tavily_crawl = subparsers.add_parser("tavily-crawl", help="Crawl web pages")
    tavily_crawl.add_argument("--url", "-u", required=True, help="URL to crawl")
    tavily_crawl.add_argument("--depth", "-d", type=int, default=2, help="Max crawl depth")

    tavily_map = subparsers.add_parser("tavily-map", help="Generate site map")
    tavily_map.add_argument("--url", "-u", required=True, help="URL to map")

    verity = subparsers.add_parser("verity", help="Multi-source retrieval with confidence scoring")
    verity.add_argument("--query", "-q", required=True, help="Search query")
    verity.add_argument("--count", "-c", type=int, default=10, help="Max results per source")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        client = SearchClient()
    except ValueError as exc:
        print(json.dumps({"success": False, "error": {"code": "AUTH_ERROR", "message": str(exc)}}))
        sys.exit(1)

    result: Optional[Dict[str, Any]] = None

    if args.command == "web":
        result = client.web_search(args.query, args.count)
    elif args.command == "scholar":
        result = client.scholar_search(args.query, args.count, args.year_from, args.year_to)
    elif args.command == "smart":
        result = client.smart_search(args.query, args.count)
    elif args.command == "sonar":
        result = client.sonar(args.query, args.system)
    elif args.command == "sonar-pro":
        result = client.sonar_pro(args.query, args.system)
    elif args.command == "sonar-reasoning-pro":
        result = client.sonar_reasoning_pro(args.query, args.system)
    elif args.command == "sonar-deep-research":
        result = client.sonar_deep_research(args.query, args.system)
    elif args.command == "tavily-search":
        result = client.tavily_search(args.query)
    elif args.command == "tavily-extract":
        urls = [url.strip() for url in args.urls.split(",") if url.strip()]
        result = client.tavily_extract(urls)
    elif args.command == "tavily-crawl":
        result = client.tavily_crawl(args.url, args.depth)
    elif args.command == "tavily-map":
        result = client.tavily_map(args.url)
    elif args.command == "verity":
        result = client.verity_search(args.query, args.count)

    if result is None:
        parser.print_help()
        sys.exit(1)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    try:
        print(output)
    except UnicodeEncodeError:
        print(json.dumps(result, indent=2, ensure_ascii=True))

    sys.exit(0 if result.get("success", True) else 1)


if __name__ == "__main__":
    main()
