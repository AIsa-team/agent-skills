"""Static provider catalog and runtime client implementations."""

from __future__ import annotations

import json
import re
import sys
from typing import Any

from . import aisa, env, schema

AISA_DEFAULT = "gpt-4.1-mini"


class ReasoningClient:
    """Shared interface for planner and rerank providers."""

    name: str

    def generate_text(
        self,
        model: str,
        prompt: str,
        *,
        tools: list[dict[str, Any]] | None = None,
        response_mime_type: str | None = None,
    ) -> str:
        raise NotImplementedError

    def generate_json(
        self,
        model: str,
        prompt: str,
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        text = self.generate_text(model, prompt, tools=tools, response_mime_type="application/json")
        return extract_json(text)


class AIsaClient(ReasoningClient):
    name = "aisa"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_text(
        self,
        model: str,
        prompt: str,
        *,
        tools: list[dict[str, Any]] | None = None,
        response_mime_type: str | None = None,
    ) -> str:
        del tools
        response = aisa.chat_completion(
            self.api_key,
            model,
            prompt,
            response_mime_type=response_mime_type,
        )
        return extract_openai_text(response)


_MODEL_DEFAULTS: dict[str, tuple[str, str]] = {
    "aisa": (AISA_DEFAULT, AISA_DEFAULT),
}

def _normalize_provider_name(provider_name: str) -> str:
    return provider_name


def display_provider_name(provider_name: str) -> str:
    """Normalize user-facing provider labels to the effective runtime provider."""
    return _normalize_provider_name((provider_name or "auto").lower())


def warn_if_legacy_provider_alias(provider_name: str) -> None:
    normalized = (provider_name or "").lower()
    if normalized not in {"", "auto", "aisa"}:
        raise RuntimeError(
            "Unsupported LAST30DAYS_REASONING_PROVIDER. The AISA-only runtime accepts only 'auto' or 'aisa'."
        )


def _resolve_model_pins(config: dict[str, Any], depth: str, provider_name: str) -> tuple[str, str]:
    """Resolve planner and rerank model pins for a provider."""
    del depth
    default_planner, default_rerank = _MODEL_DEFAULTS.get(provider_name, (AISA_DEFAULT, AISA_DEFAULT))
    planner_model = config.get("LAST30DAYS_PLANNER_MODEL") or default_planner
    rerank_model = config.get("LAST30DAYS_RERANK_MODEL") or default_rerank
    return planner_model, rerank_model


def mock_runtime(config: dict[str, Any], depth: str) -> schema.ProviderRuntime:
    """Resolve model pins for mock mode without requiring live credentials."""
    provider_name = (config.get("LAST30DAYS_REASONING_PROVIDER") or "aisa").lower()
    warn_if_legacy_provider_alias(provider_name)
    if provider_name == "auto":
        provider_name = "aisa"
    provider_name = _normalize_provider_name(provider_name)
    if provider_name not in _MODEL_DEFAULTS:
        raise RuntimeError(f"Unsupported reasoning provider: {provider_name}")
    planner_model, rerank_model = _resolve_model_pins(config, depth, provider_name)
    return schema.ProviderRuntime(
        reasoning_provider=provider_name,
        planner_model=planner_model,
        rerank_model=rerank_model,
        x_search_backend=_resolve_x_backend(config),
    )


def resolve_runtime(config: dict[str, Any], depth: str) -> tuple[schema.ProviderRuntime, ReasoningClient | None]:
    """Resolve the reasoning provider and pinned models."""
    provider_name = (config.get("LAST30DAYS_REASONING_PROVIDER") or "auto").lower()
    warn_if_legacy_provider_alias(provider_name)
    aisa_key = config.get("AISA_API_KEY")

    if provider_name == "auto":
        if aisa_key:
            provider_name = "aisa"
        else:
            return schema.ProviderRuntime(
                reasoning_provider="local",
                planner_model="deterministic",
                rerank_model="local-score",
                x_search_backend=_resolve_x_backend(config),
            ), None

    provider_name = _normalize_provider_name(provider_name)
    planner_model, rerank_model = _resolve_model_pins(config, depth, provider_name)

    if provider_name == "aisa":
        if not aisa_key:
            raise RuntimeError("AIsa selected but no AISA_API_KEY is configured.")
        runtime = schema.ProviderRuntime(
            reasoning_provider="aisa",
            planner_model=planner_model,
            rerank_model=rerank_model,
            x_search_backend=_resolve_x_backend(config),
        )
        return runtime, AIsaClient(aisa_key)

    raise RuntimeError(f"Unsupported reasoning provider: {provider_name}")


def _resolve_x_backend(config: dict[str, Any]) -> str | None:
    preferred = (config.get("LAST30DAYS_X_BACKEND") or "").lower()
    if preferred == "aisa":
        return preferred
    return env.get_x_source(config)


def extract_json(text: str) -> dict[str, Any]:
    """Extract the first JSON object from a model response."""
    text = text.strip()
    if not text:
        raise ValueError("Expected JSON response, got empty text")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        return json.loads(match.group(0))


def extract_gemini_text(payload: dict[str, Any]) -> str:
    del payload
    return ""


def extract_openai_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    output = payload.get("output") or payload.get("choices") or []
    for item in output:
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            if isinstance(item.get("text"), str):
                return item["text"]
            content = item.get("content") or []
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        return part["text"]
                    if isinstance(part, dict) and part.get("type") == "output_text" and isinstance(part.get("text"), str):
                        return part["text"]
            message = item.get("message") or {}
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
    if payload:
        print(f"[Providers] extract_openai_text: no text in payload keys: {list(payload.keys())}", file=sys.stderr)
    return ""


def _parse_sse_chunk(chunk: str) -> dict[str, Any] | None:
    data_lines = [
        line[5:].strip()
        for line in chunk.split("\n")
        if line.startswith("data:")
    ]
    if not data_lines:
        return None
    data = "\n".join(data_lines).strip()
    if not data or data == "[DONE]":
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def _parse_codex_stream(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    events = [chunk for chunk in raw.split("\n\n") if chunk.strip()]
    text_parts: list[str] = []
    completed: dict[str, Any] | None = None
    for chunk in events:
        payload = _parse_sse_chunk(chunk)
        if not payload:
            continue
        if payload.get("type") == "response.completed" and isinstance(payload.get("response"), dict):
            completed = payload["response"]
        delta = payload.get("delta")
        if isinstance(delta, str):
            text_parts.append(delta)
    if completed is not None:
        return completed
    if text_parts:
        return {"output_text": "".join(text_parts)}
    return {}
