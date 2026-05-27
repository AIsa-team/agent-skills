#!/usr/bin/env python3
"""Lightweight website crawler for SEO keyword research."""

from __future__ import annotations

import argparse
import html
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_USER_AGENT = "AIsa SEO Keyword Research Skill/1.0"


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta_description = ""
        self.canonical = ""
        self.headings: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.schema_types: list[str] = []
        self._current_tag: str | None = None
        self._current_attrs: dict[str, str] = {}
        self._buffer: list[str] = []
        self._text_chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k.lower(): v or "" for k, v in attrs}
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "meta":
            name = (attr.get("name") or attr.get("property") or "").lower()
            if name in {"description", "og:description"} and not self.meta_description:
                self.meta_description = clean_text(attr.get("content", ""))
        if tag == "link" and attr.get("rel", "").lower() == "canonical":
            self.canonical = attr.get("href", "")
        if tag == "a" and attr.get("href"):
            self.links.append({"href": attr["href"], "text": ""})
        if tag in {"title", "h1", "h2", "h3", "p", "li", "a"}:
            self._current_tag = tag
            self._current_attrs = attr
            self._buffer = []
        if tag == "script" and attr.get("type", "").lower() == "application/ld+json":
            self._current_tag = "jsonld"
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if self._current_tag == tag or (tag == "script" and self._current_tag == "jsonld"):
            text = clean_text(" ".join(self._buffer))
            if tag == "title" and text and not self.title:
                self.title = text
            elif tag in {"h1", "h2", "h3"} and text:
                self.headings.append({"level": tag, "text": text})
            elif tag in {"p", "li"} and text:
                self._text_chunks.append(text)
            elif tag == "a" and text and self.links:
                self.links[-1]["text"] = text
                self._text_chunks.append(text)
            elif self._current_tag == "jsonld" and text:
                self.schema_types.extend(extract_schema_types(text))
            self._current_tag = None
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth and self._current_tag != "jsonld":
            return
        if self._current_tag:
            self._buffer.append(data)

    @property
    def visible_text(self) -> str:
        return clean_text(" ".join(self._text_chunks))


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    return re.sub(r"\s+", " ", value).strip()


def extract_schema_types(raw_json: str) -> list[str]:
    types: list[str] = []
    try:
        data = json.loads(raw_json)
    except Exception:
        return types

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            t = obj.get("@type")
            if isinstance(t, str):
                types.append(t)
            elif isinstance(t, list):
                types.extend(str(x) for x in t)
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    return sorted(set(types))


def normalize_url(url: str, base_url: str) -> str:
    url = urllib.parse.urljoin(base_url, url)
    parsed = urllib.parse.urlsplit(url)
    parsed = parsed._replace(fragment="")
    return urllib.parse.urlunsplit(parsed)


def same_site(url: str, root_netloc: str) -> bool:
    netloc = urllib.parse.urlsplit(url).netloc.lower()
    return netloc == root_netloc or netloc.endswith("." + root_netloc)


def likely_content_url(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    path = parsed.path.lower()
    if re.search(r"\.(jpg|jpeg|png|gif|webp|svg|pdf|zip|mp4|mp3|css|js|ico)$", path):
        return False
    if any(x in path for x in ["/login", "/signup", "/cart", "/checkout"]):
        return False
    return True


def fetch(url: str, timeout: int) -> tuple[int | None, str, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl_context()) as response:
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return response.status, "", content_type, "non-html response"
            raw = response.read(1_500_000)
            charset = response.headers.get_content_charset() or "utf-8"
            return response.status, raw.decode(charset, errors="replace"), content_type, ""
    except urllib.error.HTTPError as exc:
        return exc.code, "", "", str(exc)
    except urllib.error.URLError as exc:
        return None, "", "", str(exc.reason)


def parse_page(url: str, body: str, root_netloc: str) -> dict[str, object]:
    parser = PageParser()
    parser.feed(body)
    internal_links: list[dict[str, str]] = []
    seen: set[str] = set()
    for link in parser.links:
        href = normalize_url(link["href"], url)
        if href in seen or not likely_content_url(href) or not same_site(href, root_netloc):
            continue
        seen.add(href)
        internal_links.append({"url": href, "text": clean_text(link.get("text", ""))})
    text = parser.visible_text
    return {
        "url": url,
        "title": parser.title,
        "meta_description": parser.meta_description,
        "canonical": parser.canonical,
        "headings": parser.headings[:40],
        "schema_types": parser.schema_types,
        "text_sample": text[:5000],
        "word_count_estimate": len(text.split()),
        "internal_links": internal_links[:80],
    }


def crawl(start_url: str, max_pages: int, timeout: int, delay: float) -> dict[str, object]:
    if not urllib.parse.urlsplit(start_url).scheme:
        start_url = "https://" + start_url
    start_url = normalize_url(start_url, start_url)
    root_netloc = urllib.parse.urlsplit(start_url).netloc.lower()
    queue = [start_url]
    visited: set[str] = set()
    pages: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []

    while queue and len(pages) < max_pages:
        url = queue.pop(0)
        if url in visited or not likely_content_url(url) or not same_site(url, root_netloc):
            continue
        visited.add(url)
        status, body, content_type, error = fetch(url, timeout)
        if not body:
            errors.append({"url": url, "status": status, "content_type": content_type, "error": error})
            continue
        page = parse_page(url, body, root_netloc)
        pages.append(page)
        for link in page["internal_links"]:
            href = link["url"]
            if href not in visited and href not in queue:
                queue.append(href)
        time.sleep(delay)

    return {
        "start_url": start_url,
        "root_netloc": root_netloc,
        "pages_crawled": len(pages),
        "pages": pages,
        "errors": errors[:20],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl a website and extract SEO research context.")
    parser.add_argument("url", help="Starting URL or domain.")
    parser.add_argument("--max-pages", type=int, default=12, help="Maximum HTML pages to crawl.")
    parser.add_argument("--timeout", type=int, default=20, help="Request timeout in seconds.")
    parser.add_argument("--delay", type=float, default=0.25, help="Delay between requests in seconds.")
    parser.add_argument("--out", help="Optional JSON output path.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = crawl(args.url, args.max_pages, args.timeout, args.delay)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
