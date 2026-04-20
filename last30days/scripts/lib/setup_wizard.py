"""First-run setup helpers for the AISA-only last30days skill."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# AIsa publishes its model catalog in the public docs. There is no
# /v1/models endpoint on api.aisa.one — the markdown version of the guide
# is the authoritative source and is stable/parseable.
# Human-facing version: https://aisa.one/docs/guides/models
AISA_MODELS_DOC_URL = "https://aisa.one/docs/guides/models.md"

# Per-role shortlists. Each role intersects against the live catalog at
# install time and falls back to the first few catalog entries if nothing
# matches. Order = recommendation order.
#
#   planner: needs reliable structured JSON; fast + cheap wins
#   rerank:  quality reasoning matters most (orders the candidate pool)
#   fun:     cosmetic vibes score; cheapest/fastest model is fine
_ROLE_SHORTLISTS: dict[str, tuple[str, ...]] = {
    "planner": (
        # Qwen, Kimi, and small ByteDance Seed models lead — fast, cheap,
        # and reliable at emitting the structured JSON query plan.
        # qwen-flash comes first for battle-tested reliability across
        # prompt shapes; kimi-k2.5 is even faster (~1.5s vs 3-4s) but
        # can return terse/single-object responses on weakly-constrained
        # prompts, so it's slot #2.
        # NOTE: seed-2-0-pro and qwen3.6-plus excluded — see comments in
        # the rerank shortlist.
        # Patterns are scoped to avoid matching qwen-mt-* (translation)
        # or qwen3-vl-* (vision) models.
        "qwen-flash",
        "kimi-k2.5",
        "seed-2-0-mini",       # ByteDance small, JSON-capable
        "qwen3-coder-flash",
        "qwen-plus",
        "qwen3-max",
        # Non-Chinese fallbacks, ordered by measured planner-prompt
        # latency on the AISA gateway (fast → slow). gpt-5-mini is
        # deliberately excluded: clocked at ~30s on the planner prompt
        # despite the "mini" label (GPT-5 generation has heavy reasoning
        # overhead that dominates planner latency).
        "claude-haiku",            # ~10s
        "gpt-4o-mini",             # ~9s
        "gemini-2.5-flash-lite",   # ~13s
        "gemini-2.5-flash",        # ~14s
        "gpt-4.1-mini",            # ~15s
    ),
    "rerank": (
        # Reranker orders the candidate pool. qwen-plus leads — it's
        # ~12s on the 40-candidate default-depth rerank prompt vs
        # qwen3-max at ~24s (which frequently hits the 60s pipeline
        # chat timeout after accounting for gateway overhead).
        # claude-sonnet-4-6 is the quality fallback at comparable
        # in-pipeline latency.
        # NOTES on excluded / deprioritized models:
        #   - qwen3-max: great on --quick, but ~24s × pipeline overhead
        #     pushes default-depth runs past 60s. Kept as slot #2 for
        #     users who want it on shorter runs.
        #   - kimi-k2.5: 2-15s variance on realistic rerank prompts —
        #     fast when it works, malformed JSON or timeouts otherwise.
        #     Available as slot #3 but not default.
        #   - qwen3.6-plus and MiniMax-M2.5: deep-reasoning variants
        #     that emit long chain-of-thought; exceed 60s at default
        #     depth. Fully excluded.
        #   - seed-2-0-pro (ByteDance): rejects response_format
        #     json_object on the gateway. Smaller Seed variants aren't
        #     strong enough for ranking.
        "qwen-plus",
        "qwen3-max",
        "kimi-k2.5",
        "claude-sonnet-4-6",
        "claude-sonnet-4-5",
        "gpt-5",
        "gpt-4o",
        "gemini-2.5-pro",
        "claude-haiku",
        "gpt-4o-mini",
    ),
    "fun": (
        # Fun-scoring is cosmetic — "is this item quirky or meme-worthy?"
        # A wrong answer just affects the optional "Best Takes" section,
        # never the core research. So lead with the cheapest small models
        # across providers; premium tiers are a waste of cents per run.
        "qwen-flash",
        "seed-2-0-lite",       # ByteDance lite — cheapest Seed variant
        "seed-1-6-flash",      # older/fast ByteDance Seed
        "qwen3-coder-flash",
        "deepseek-v3.2",
        "deepseek-v3.1",
        "gemini-2.5-flash-lite",
        "gpt-4o-mini",
        # Haiku is a reasonable fallback but already pricier per token
        # than the flash/lite tiers above — kept last in the shortlist.
        "claude-haiku",
    ),
}

_ROLE_DESCRIPTIONS: dict[str, str] = {
    "planner": "composes the structured JSON query plan (fast + reliable JSON)",
    "rerank":  "orders the candidate pool by relevance (quality matters most)",
    "fun":     "scores quirky/meme-worthy items for the 'Best Takes' section (cheap)",
}

# Matches a markdown table row whose first cell is a backtick-wrapped model id.
# Example row: | `gpt-4o-mini` | OpenAI | Text, Vision | 128,000 |
_MODEL_ROW_RE = re.compile(r"^\|\s*`([A-Za-z0-9][A-Za-z0-9._-]{2,})`\s*\|(.+)\|")


def fetch_available_models(api_key: str | None = None) -> list[str]:
    """Scrape the AIsa model catalog from the public docs.

    Returns a list of text-capable model IDs (planner / reranker need text).
    Empty list on any failure. The api_key parameter is accepted for
    backwards compatibility but is not used — the docs page is public.
    """
    del api_key
    from . import http
    try:
        raw = http.request(
            "GET",
            AISA_MODELS_DOC_URL,
            headers={"Accept": "text/plain,text/markdown"},
            timeout=15,
            retries=1,
            raw=True,
        )
    except Exception as exc:
        logger.warning("Could not fetch AIsa model catalog: %s", exc)
        return []

    if not isinstance(raw, str):
        return []

    ids: list[str] = []
    seen: set[str] = set()
    for line in raw.splitlines():
        match = _MODEL_ROW_RE.match(line)
        if not match:
            continue
        model_id, rest = match.group(1), match.group(2).lower()
        # Skip table header/separator lines that happen to start with ` (none in practice)
        if model_id.startswith("-") or "developer" in rest.lower():
            continue
        # Keep only models with text capability — planner/reranker can't use image-only.
        if "text" not in rest and "vision" not in rest:
            continue
        if model_id in seen:
            continue
        seen.add(model_id)
        ids.append(model_id)
    return ids


def _shortlist_for_role(role: str, models: list[str]) -> list[str]:
    """Intersect the role's preferred patterns with the live catalog."""
    patterns = _ROLE_SHORTLISTS.get(role, ())
    seen: set[str] = set()
    picked: list[str] = []
    for pattern in patterns:
        for mid in models:
            if pattern in mid.lower() and mid not in seen:
                seen.add(mid)
                picked.append(mid)
    return picked


def select_model_interactive(
    api_key: str,
    *,
    role: str = "planner",
    models: list[str] | None = None,
    reuse_option: tuple[str, str] | None = None,
) -> str | None:
    """Prompt the installer to pick a model for a specific role.

    Args:
        api_key: used only if ``models`` isn't pre-fetched.
        role: one of "planner", "rerank", "fun" — controls the shortlist and label.
        models: pre-fetched catalog to avoid repeated HTTP calls per role.
        reuse_option: optional (label, value) shown as an extra menu entry —
            lets later roles reuse an earlier role's choice in one keystroke.

    Returns the chosen model id, or None on skip / EOF / parse failure.
    """
    if models is None:
        models = fetch_available_models(api_key)
    if not models:
        sys.stderr.write(
            "[last30days] Could not fetch the AISA model catalog; skipping model picker.\n"
            "             Set model env vars manually in ~/.config/last30days/.env.\n"
        )
        return None

    recommended = _shortlist_for_role(role, models) or models[:8]
    description = _ROLE_DESCRIPTIONS.get(role, "")
    header = f"\nPick model for {role.upper()}"
    if description:
        header += f" — {description}"
    sys.stderr.write(header + ":\n")
    for idx, mid in enumerate(recommended, 1):
        sys.stderr.write(f"  [{idx}] {mid}\n")
    next_idx = len(recommended) + 1
    reuse_idx = None
    if reuse_option is not None:
        reuse_idx = next_idx
        sys.stderr.write(f"  [{reuse_idx}] {reuse_option[0]}  ({reuse_option[1]})\n")
        next_idx += 1
    show_all_idx = next_idx
    skip_idx = next_idx + 1
    sys.stderr.write(f"  [{show_all_idx}] ...show full list ({len(models)} models)\n")
    sys.stderr.write(f"  [{skip_idx}] skip\n")
    sys.stderr.write("Choice [1]: ")
    sys.stderr.flush()

    try:
        raw = input().strip()
    except (EOFError, KeyboardInterrupt):
        sys.stderr.write("\n")
        return None
    if not raw:
        return recommended[0]

    try:
        idx = int(raw)
    except ValueError:
        if raw in models:
            return raw
        sys.stderr.write(f"[last30days] {raw!r} is not a known model id.\n")
        return None

    if 1 <= idx <= len(recommended):
        return recommended[idx - 1]
    if reuse_idx is not None and idx == reuse_idx:
        return reuse_option[1]
    if idx == show_all_idx:
        sys.stderr.write("\nFull model list:\n")
        for i, mid in enumerate(models, 1):
            sys.stderr.write(f"  [{i}] {mid}\n")
        sys.stderr.write("Enter model id or number: ")
        sys.stderr.flush()
        try:
            raw2 = input().strip()
        except (EOFError, KeyboardInterrupt):
            sys.stderr.write("\n")
            return None
        try:
            j = int(raw2)
            if 1 <= j <= len(models):
                return models[j - 1]
        except ValueError:
            if raw2 in models:
                return raw2
        sys.stderr.write("[last30days] Invalid choice.\n")
        return None
    return None


def select_models_interactive(api_key: str) -> dict[str, str | None]:
    """Prompt for planner + reranker + fun-scorer in turn.

    Later roles get a 'use same as <earlier>' menu entry so installers who
    want a single-model setup only have to pick once.
    """
    models = fetch_available_models(api_key)
    if not models:
        sys.stderr.write(
            "[last30days] Could not fetch the AISA model catalog; skipping model picker.\n"
        )
        return {"planner": None, "rerank": None, "fun": None}

    sys.stderr.write(
        "\nlast30days makes three LLM calls per research run. You can specialize\n"
        "each model (faster planner, stronger reranker, cheapest fun-scorer), or\n"
        "reuse the same choice for all three.\n"
    )

    planner = select_model_interactive(api_key, role="planner", models=models)
    rerank = select_model_interactive(
        api_key,
        role="rerank",
        models=models,
        reuse_option=("use same as planner", planner) if planner else None,
    )
    fun = select_model_interactive(
        api_key,
        role="fun",
        models=models,
        reuse_option=("use same as reranker", rerank) if rerank else
                     (("use same as planner", planner) if planner else None),
    )
    return {"planner": planner, "rerank": rerank, "fun": fun}


def is_first_run(config: dict[str, Any]) -> bool:
    """Return True when setup has not been completed."""
    return not config.get("SETUP_COMPLETE")


def run_auto_setup(config: dict[str, Any]) -> dict[str, Any]:
    """Return the current AISA setup state."""
    return {
        "aisa_configured": bool(config.get("AISA_API_KEY")),
        "env_written": False,
    }


def write_setup_config(
    env_path: Path,
    *,
    model: str | None = None,
    models: dict[str, str | None] | None = None,
) -> bool:
    """Write SETUP_COMPLETE and role-specific model pins to the .env file.

    Priority: ``models`` (per-role dict) > ``model`` (legacy single pin).
    Never overwrites existing keys — that's the installer's job to edit.
    """
    try:
        env_path = Path(env_path)
        env_path.parent.mkdir(parents=True, exist_ok=True)

        existing_keys: set[str] = set()
        existing_content = ""
        if env_path.exists():
            existing_content = env_path.read_text(encoding="utf-8")
            for line in existing_content.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    existing_keys.add(stripped.split("=", 1)[0].strip())

        lines_to_append: list[str] = []

        if models:
            # Write per-role pins. If every role resolved to the same model,
            # collapse to a single AISA_MODEL pin for a cleaner .env.
            picked = {role: value for role, value in models.items() if value}
            distinct = set(picked.values())
            if picked and len(distinct) == 1 and "AISA_MODEL" not in existing_keys:
                lines_to_append.append(f"AISA_MODEL={next(iter(distinct))}")
            else:
                role_to_key = {
                    "planner": "LAST30DAYS_PLANNER_MODEL",
                    "rerank":  "LAST30DAYS_RERANK_MODEL",
                    "fun":     "LAST30DAYS_FUN_MODEL",
                }
                for role, value in picked.items():
                    key = role_to_key.get(role)
                    if key and key not in existing_keys:
                        lines_to_append.append(f"{key}={value}")
        elif model and "AISA_MODEL" not in existing_keys:
            lines_to_append.append(f"AISA_MODEL={model}")

        if "SETUP_COMPLETE" not in existing_keys:
            lines_to_append.append("SETUP_COMPLETE=true")

        if not lines_to_append:
            return True

        with open(env_path, "a", encoding="utf-8") as handle:
            if existing_content and not existing_content.endswith("\n"):
                handle.write("\n")
            handle.write("\n".join(lines_to_append) + "\n")
        return True
    except OSError as exc:
        logger.error("Failed to write setup config to %s: %s", env_path, exc)
        return False


def get_setup_status_text(results: dict[str, Any]) -> str:
    """Return a human-readable summary of setup results."""
    lines = [
        "Setup complete! Here's what I found:",
        "",
        "  - AISA API key configured" if results.get("aisa_configured") else "  - AISA API key not configured",
    ]
    models = results.get("models") or {}
    chosen_model = results.get("model")
    if models and any(models.values()):
        lines.append("  - Reasoning models:")
        for role in ("planner", "rerank", "fun"):
            value = models.get(role)
            if value:
                lines.append(f"      {role:7s} → {value}")
    elif chosen_model:
        lines.append(f"  - Reasoning model: {chosen_model}")
    elif results.get("aisa_configured"):
        lines.append("  - Reasoning model: not set (run setup again or export AISA_MODEL)")
    if results.get("env_written"):
        lines.append("")
        lines.append(f"Configuration saved to {results.get('env_path') or '~/.config/last30days/.env'}.")
    return "\n".join(lines)


def _has_python312_plus() -> bool:
    candidates = [
        "/usr/local/python3.12/bin/python3.12",
        shutil.which("python3.14"),
        shutil.which("python3.13"),
        shutil.which("python3.12"),
        shutil.which("python3"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            proc = subprocess.run(
                [candidate, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"],
                capture_output=True,
                check=False,
                text=True,
            )
        except OSError:
            continue
        if proc.returncode == 0:
            return True
    return False


def run_openclaw_setup(config: dict[str, Any]) -> dict[str, Any]:
    """Server-side setup probe: no browser auth, just tool + key availability."""
    return {
        "node": shutil.which("node") is not None,
        "python3": _has_python312_plus(),
        "keys": {"aisa": bool(config.get("AISA_API_KEY"))},
        "aisa_configured": bool(config.get("AISA_API_KEY")),
        "x_method": "aisa" if config.get("AISA_API_KEY") else None,
    }


def run_github_auth() -> dict[str, Any]:
    """GitHub auth is no longer brokered by this skill."""
    return {"supported": False, "reason": "GitHub auth is handled by GH_TOKEN/GITHUB_TOKEN."}


def run_full_device_auth() -> dict[str, Any]:
    """Device auth is no longer exposed by the AISA-only runtime."""
    return {"supported": False, "reason": "Legacy device auth was removed from the AISA-only runtime."}
