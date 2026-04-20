---
name: last30days
description: "Research the last 30 days across Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, GitHub, and grounded web search. Returns a ranked, clustered brief with citations. Use when the task needs recent social evidence, competitor comparisons, launch reactions, trend scans, or person/company profiles."
license: MIT
compatibility: "Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3, a POSIX shell, and AISA_API_KEY."
metadata: {"aisa": {"emoji": "📰", "homepage": "https://aisa.one", "requires": {"bins": ["python3", "bash"], "env": ["AISA_API_KEY"]}, "primaryEnv": "AISA_API_KEY", "harnesses": ["claude-code", "claude", "opencode", "cursor", "codex", "gemini-cli", "openclaw", "hermes", "goose"]}}
---
# last30days 📰

**30-day multi-source research brief for autonomous agents. Powered by AIsa.**

One API key. Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, GitHub, and grounded web — merged into a single ranked brief.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness, including:

- **Claude Code** and **Claude** (Anthropic)
- **OpenAI Codex**
- **Cursor**
- **Gemini CLI** (Google)
- **OpenCode**, **Goose**, **OpenClaw**, **Hermes**
- and any other harness that implements the [Agent Skills
  specification](https://agentskills.io/specification)

Requires Python 3, a POSIX shell, and `AISA_API_KEY` (get one at
[aisa.one](https://aisa.one)).

## What Can You Do?

### Trend scan
```text
"last30days OpenAI Agents SDK"
```

### Competitor comparison
```text
"last30days Claude Code vs Codex"
```

### Person / company profile
```text
"last30days Peter Steinberger"
```

### Launch reaction
```text
"last30days GPT-5 launch --deep"
```

### Prediction-market angle
```text
"last30days bitcoin price"
```

## Quick Start

```bash
# 1. Export your AIsa key
export AISA_API_KEY=sk-...

# 2. First-run setup (interactive — picks planner / rerank / fun-scorer models)
bash "${SKILL_ROOT}/scripts/run-last30days.sh" setup

# 3. Research a topic
bash "${SKILL_ROOT}/scripts/run-last30days.sh" "OpenAI Agents SDK"
```

## Common Flags

```bash
# Low-latency profile (fewer candidates per source)
bash "${SKILL_ROOT}/scripts/run-last30days.sh" "$ARGUMENTS" --quick

# Higher-recall profile
bash "${SKILL_ROOT}/scripts/run-last30days.sh" "$ARGUMENTS" --deep

# Machine-readable output (full plan + candidates + clusters)
bash "${SKILL_ROOT}/scripts/run-last30days.sh" "$ARGUMENTS" --emit=json

# Restrict to specific sources
bash "${SKILL_ROOT}/scripts/run-last30days.sh" "$ARGUMENTS" --search=reddit,x,grounding

# Check provider / source availability
bash "${SKILL_ROOT}/scripts/run-last30days.sh" --diagnose
```

## Inputs and Outputs

**Input.** A topic, person, company, product, or comparison — e.g.
`OpenAI Agents SDK`, `OpenClaw vs Codex`, `Peter Steinberger`.

**Output.** A markdown brief (default) or JSON with:

- `query_plan` — planner-generated subqueries and source weights
- `ranked_candidates` — reranked candidate pool with scores
- `clusters` — semantically grouped findings
- `items_by_source` — per-source item lists with dates, engagement, URLs
- `provider_runtime` — which models + retrieval backends ran
- `errors_by_source` — any source-level failures (fail-soft)

## When to use

- You need last-30-days evidence on a person, company, product, market, tool, or trend.
- You want a ranked competitor comparison, launch-reaction summary, creator/community sentiment scan, or shipping update.
- You want a structured JSON brief to feed into another agent.

## When NOT to use

- Timeless reference questions with no recent-evidence requirement.
- When you only want one official source and don't want social/community signals.

## Capabilities

- **AISA-powered**: planner (structured JSON query plan), reranker
  (relevance ordering), fun-scorer (meme/quirk signal), and hosted
  retrieval for X, YouTube, TikTok, Instagram, Polymarket, and grounded
  Tavily web search.
- **Public paths (no extra credentials)**: Reddit, Hacker News.
- **GitHub** via the official API when `GH_TOKEN` or `GITHUB_TOKEN` is
  set — optional.
- **Fail-soft**: if one source errors or times out, the brief still
  renders with the others and notes the gap.

## Model Configuration

The skill makes three LLM calls per run. Each role is independently
pinnable via `~/.config/last30days/.env`:

```bash
LAST30DAYS_PLANNER_MODEL=qwen-flash           # fast + reliable JSON
LAST30DAYS_RERANK_MODEL=qwen-plus-2025-12-01  # quality ranking
LAST30DAYS_FUN_MODEL=qwen-flash               # cheap vibes
```

Or set `AISA_MODEL=...` for a single model across all three roles. Run
`last30days setup` to pick interactively — the picker fetches the live
catalog from [aisa.one/docs/guides/models](https://aisa.one/docs/guides/models).

## API Reference

last30days calls the following AIsa endpoints directly. See the
[full API Reference](https://aisa.one/docs/api-reference) for the
complete catalog.

- [OpenAI Chat / `createChatCompletion`](https://aisa.one/docs/api-reference/chat/createchatcompletion) — planner, reranker, fun-scorer
- [Twitter Advanced Search](https://aisa.one/docs/api-reference/twitter/get_twitter-tweet-advanced-search) — X retrieval
- [YouTube Search](https://aisa.one/docs/api-reference/search/get_youtube-search) — YouTube retrieval
- [Tavily Search](https://aisa.one/docs/api-reference/search/post_tavily-search) — grounded web
- [Polymarket Markets](https://aisa.one/docs/api-reference/prediction-market/get_polymarket-markets) — prediction-market retrieval

Reddit and Hacker News use their respective public APIs directly (no
AISA proxy required).

## Requirements

- **Python 3.12+**
- **`AISA_API_KEY`** — required. Get one at [aisa.one](https://aisa.one).
- **`GH_TOKEN` / `GITHUB_TOKEN`** — optional, enables the GitHub source.

```bash
# Pin an interpreter ≥ 3.12
for py in /usr/local/python3.12/bin/python3.12 python3.14 python3.13 python3.12 python3; do
  command -v "$py" >/dev/null 2>&1 || continue
  "$py" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' || continue
  LAST30DAYS_PYTHON="$py"
  break
done
```
