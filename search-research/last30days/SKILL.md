---
name: last30days
description: Research the last 30 days across Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, GitHub, and grounded web search. Returns a ranked, clustered brief with citations. Use when the task needs recent social evidence, competitor comparisons, launch reactions, trend scans, or person/company profiles.
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3.11+ and a POSIX shell; hosted retrieval requires AISA_API_KEY and an authorized budget.
metadata:
  version: "1.1.0"
  aisa:
    emoji: 📰
    homepage: https://aisa.one
    requires:
      bins:
      - python3
      - bash
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    harnesses:
    - claude-code
    - claude
    - opencode
    - cursor
    - codex
    - gemini-cli
    - openclaw
    - hermes
    - goose
---
# last30days 📰

**30-day multi-source research brief for autonomous agents. Powered by AIsa.**

Combine public Reddit and Hacker News, AIsa-hosted X/YouTube/Polymarket/web retrieval, optional GitHub, and indexed TikTok/Instagram web discoveries into one ranked evidence brief. Native social engagement is not available from web discovery.

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

Requires Python 3.11+, a POSIX shell, and `AISA_API_KEY` for hosted retrieval (get one at
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

# 2. Optional setup: inspect configuration and choose model pins
bash scripts/run-last30days.sh setup

# 3. Research within the user-authorized estimate budget
bash scripts/run-last30days.sh "OpenAI Agents SDK" \
  --budget-usd "$APPROVED_BUDGET_USD" --cost-ledger research-costs.json
```

Run paths relative to the installed skill directory, or resolve them to absolute paths.
The wrappers preserve the caller's working directory and project configuration.
Public-source/local and `--mock` runs do not need an AIsa key or budget.

For hosted work, honor the budget the user actually authorized. Read
[request costs and recovery](references/cost-control.md) before running paid retrieval.
Quotes marked `may_exceed_estimate` require explicit acceptance via
`--allow-variable-cost`; the final charge can exceed the admission estimate.

## Common Flags

```bash
# Low-latency profile (fewer candidates per source)
bash scripts/run-last30days.sh "$ARGUMENTS" --cost-ledger research-costs.json --quick

# Higher-recall profile
bash scripts/run-last30days.sh "$ARGUMENTS" --cost-ledger research-costs.json --deep

# Machine-readable output (full plan + candidates + clusters)
bash scripts/run-last30days.sh "$ARGUMENTS" --cost-ledger research-costs.json --emit=json

# Restrict to specific sources
bash scripts/run-last30days.sh "$ARGUMENTS" --cost-ledger research-costs.json --search=reddit,x,grounding

# Inspect configured providers/sources (does not verify live availability)
bash scripts/run-last30days.sh --diagnose
```

## Inputs and Outputs

**Input.** A topic, person, company, product, or comparison — e.g.
`OpenAI Agents SDK`, `OpenClaw vs Codex`, `Peter Steinberger`.

**Output.** A markdown brief (default) or JSON with:

- `query_plan` — planner-generated subqueries and source weights
- `ranked_candidates` — reranked candidate pool with scores
- `clusters` — semantically grouped findings
- `items_by_source` — per-source item lists with dates, engagement, URLs
- `provider_runtime` — configured reasoning models and retrieval backends; inspect plan notes/warnings for fallbacks
- `errors_by_source` — failures, including partial source failures
- `artifacts.source_coverage` — retained counts and unavailable/empty/partial/failed source status
- `artifacts.costs` — exact known charges, unresolved requests, and durable ledger location

## When to use

- You need last-30-days evidence on a person, company, product, market, tool, or trend.
- You want a ranked competitor comparison, launch-reaction summary, creator/community sentiment scan, or shipping update.
- You want a structured JSON brief to feed into another agent.

## When NOT to use

- Timeless reference questions with no recent-evidence requirement.
- When you only want one official source and don't want social/community signals.

## Capabilities

- **Hosted retrieval**: X, YouTube, Polymarket public search, and Tavily web search through AIsa. TikTok/Instagram are indexed web discoveries, with unknown native engagement preserved as missing.
- **Public paths**: Reddit and Hacker News; GitHub is optional with `GH_TOKEN` or `GITHUB_TOKEN`.
- **Freshness**: ranked posts/articles require valid publication dates inside the requested window. Undated, future, and older items are excluded. Polymarket entries are explicitly labeled current observations, with resolution dates kept separate; they do not establish historical price movement.
- **Partial failures** remain visible when a source also returns usable results.

## Reasoning configuration

Deterministic planning and local ranking work without model configuration.
The current chat endpoint does not declare quote/admission-limit support, so
this release blocks hosted reasoning calls before dispatch and uses those local
fallbacks. Retrieval APIs with verified cost capabilities remain available.
Model pins (`AISA_MODEL` or per-role `LAST30DAYS_*_MODEL`) are retained for
configuration compatibility; their presence does not prove a model was called.

Unknown flags, malformed external plans, invalid date windows, and unsupported
creator/hashtag or deep-research options fail before research. `--lookback-days`
accepts 1–365 days. Mock mode covers Reddit, X, and web fixtures and performs no
network calls. The historical revision evaluator is restricted to mock mode
because old revisions do not provide the current accounting guarantees.

## API Reference

last30days calls the following AIsa endpoints directly. See the
[full API Reference](https://aisa.one/docs/api-reference) for the
complete catalog.

- [OpenAI Chat / `createChatCompletion`](https://aisa.one/docs/api-reference/chat/createchatcompletion) — configured reasoning integration; dispatch blocked pending verified cost capabilities
- [Twitter Advanced Search](https://aisa.one/docs/api-reference/twitter/get_twitter-tweet-advanced-search) — X retrieval
- [YouTube Search](https://aisa.one/docs/api-reference/search/get_youtube-search) — YouTube retrieval
- [Tavily Search](https://aisa.one/docs/api-reference/search/post_tavily-search) — grounded web
- [Polymarket Public Search](https://aisa.one/docs/api-reference/polymarket-gamma/any_polymarket_data_apis_v1_polymarket_public_search) — prediction-market retrieval

Reddit and Hacker News use their respective public APIs directly (no
AISA proxy required).

## Requirements

- **Python 3.11+**
- **`AISA_API_KEY`** — required for hosted retrieval. Get one at [aisa.one](https://aisa.one).
- **`GH_TOKEN` / `GITHUB_TOKEN`** — optional, enables the GitHub source.

```bash
# Optionally select a supported interpreter
for py in python3.14 python3.13 python3.12 python3.11 python3; do
  command -v "$py" >/dev/null 2>&1 || continue
  "$py" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || continue
  export LAST30DAYS_PYTHON="$py"
  break
done
```
