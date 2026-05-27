#!/usr/bin/env python3
"""Small AIsa API helper for SEO keyword research skills."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path


API_BASE = "https://api.aisa.one"
CHAT_ENDPOINT = "https://api.aisa.one/v1/chat/completions"


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def load_text(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")


def load_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_output(path: str | None, content: str) -> None:
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
    else:
        print(content)


def api_key() -> str:
    key = os.getenv("AISA_API_KEY", "").strip()
    if not key:
        raise SystemExit("AISA_API_KEY is not set.")
    return key


def resolve_url(path_or_url: str) -> str:
    if path_or_url.startswith("https://"):
        return path_or_url
    if not path_or_url.startswith("/"):
        path_or_url = "/" + path_or_url
    return API_BASE + path_or_url


def post_json(url: str, payload: object) -> object:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120, context=ssl_context()) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} from {url}\n{detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Request failed for {url}: {exc}") from exc


def command_data(args: argparse.Namespace) -> None:
    payload = load_json(args.payload)
    result = post_json(resolve_url(args.path), payload)
    write_output(args.out, json.dumps(result, ensure_ascii=False, indent=2))


def command_chat(args: argparse.Namespace) -> None:
    system_prompt = load_text(args.system) or (
        "You are an SEO strategist. Use only provided metrics as facts. "
        "Mark unverified ideas clearly."
    )
    user_prompt = load_text(args.prompt)
    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    result = post_json(CHAT_ENDPOINT, payload)
    content = (
        result.get("choices", [{}])[0]
        .get("message", {})
        .get("content", json.dumps(result, ensure_ascii=False, indent=2))
    )
    write_output(args.out, content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call AIsa data APIs or LLM gateway.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    data = subparsers.add_parser("data", help="POST a JSON payload to an AIsa data API path.")
    data.add_argument("path", help="AIsa API path, for example /apis/v1/dataforseo/...")
    data.add_argument("payload", help="Path to a JSON request payload file.")
    data.add_argument("--out", help="Optional output file.")
    data.set_defaults(func=command_data)

    chat = subparsers.add_parser("chat", help="Send a prompt to the AIsa LLM gateway.")
    chat.add_argument("--model", default="gpt-5-mini", help="AIsa model name.")
    chat.add_argument("--system", help="Optional system prompt file.")
    chat.add_argument("--prompt", required=True, help="User prompt file.")
    chat.add_argument("--out", help="Optional output file.")
    chat.set_defaults(func=command_chat)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
