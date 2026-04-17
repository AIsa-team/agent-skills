#!/usr/bin/env python3
"""Minimal AISA provider connectivity check for last30days v1.0.2."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from lib import aisa, http, providers  # noqa: E402


def main() -> int:
    api_key = os.environ.get("AISA_API_KEY", "").strip()
    if not api_key:
        sys.stderr.write("AISA_API_KEY is required.\n")
        return 2

    model = os.environ.get("LAST30DAYS_PLANNER_MODEL") or providers.AISA_DEFAULT
    prompt = os.environ.get(
        "AISA_TEST_PROMPT",
        "Reply with JSON only: {\"ok\": true, \"provider\": \"aisa\"}",
    )

    print(f"[AISA Test] model={model}")
    print(f"[AISA Test] url={aisa.AISA_CHAT_COMPLETIONS_URL}")
    print(
        "[AISA Test] timeout="
        f"{aisa.AISA_CHAT_TIMEOUT}s retries={aisa.AISA_CHAT_RETRIES} "
        f"prompt_chars={len(prompt)}"
    )
    try:
        payload = aisa.chat_completion(
            api_key,
            model,
            prompt,
            response_mime_type="application/json",
        )
        text = providers.extract_openai_text(payload)
        parsed = providers.extract_json(text) if text else {}
        print("[AISA Test] request=ok")
        print(json.dumps({"text": text, "parsed": parsed}, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:  # pragma: no cover - runtime utility
        error_class = http.classify_error(exc)
        print(
            f"[AISA Test] request=failed class={error_class} "
            f"type={type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
