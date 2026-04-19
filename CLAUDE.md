# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A catalog of **agent skills** for the AIsa platform (https://aisa.one). Each top-level directory (`marketpulse/`, `media-gen/`, `multi-source-search/`, `perplexity-search/`, `prediction-market-arbitrage/`, `prediction-market-data/`, `twitter-autopilot/`, `youtube-serp/`) is one self-contained skill. These are consumed by agent harnesses (OpenClaw, Claude Code, Hermes) — this repo is *not* an application, so there is no build system, dependency manifest, or test suite.

## Skill anatomy (every skill follows this)

- `SKILL.md` — the contract. Starts with YAML frontmatter (`name`, `description`, `homepage`, `metadata.aisa.{emoji,requires,primaryEnv,compatibility}`) that the harness parses. The body is the authoritative prose the agent reads at runtime: capabilities, `curl` recipes, Python client usage, endpoint reference.
- `README.md` — human-facing overview (optional in some skills, e.g. `perplexity-search/` has none).
- `scripts/*.py` — a CLI entry point the agent invokes (e.g. `market_client.py`, `media_gen_client.py`). All clients are **zero-dependency Python stdlib** (`urllib.request`, `argparse`, `json`). Do not introduce `requests`, `httpx`, or other third-party libs — the skill must run with only `python3` and `curl` on the host.
- `references/` — extra prose files linked from `SKILL.md` when a workflow is too large to inline (currently only `twitter-autopilot/` uses this for OAuth-gated post/engage flows).

When `SKILL.md` references scripts, it uses the literal token `{baseDir}` (e.g. `python3 {baseDir}/scripts/market_client.py ...`). The harness substitutes this at load time — leave it as-is when editing.

## API surface

All clients hit `https://api.aisa.one` and authenticate with `Authorization: Bearer $AISA_API_KEY`. Two base paths coexist:
- `/apis/v1/...` — the main AIsa REST surface (financial, twitter, polymarket, kalshi, youtube, search, etc.)
- `/v1/models/{model}:generateContent` — the Gemini-compatible passthrough used by `media-gen` for images.

Responses include `usage.cost` / `usage.credits_remaining` — surface these when relevant.

## Conventions to preserve when editing

- Keep `SKILL.md` frontmatter valid YAML with the inline JSON `metadata` object intact — the harness depends on this shape.
- Keep CLI subcommand surfaces stable (e.g. `market_client.py stock prices ...`); `SKILL.md` examples are the spec and must stay in sync with `scripts/*.py`.
- When an endpoint has narrower coverage than siblings (e.g. `/financial/earnings/press-releases`), document the gotcha inline in `SKILL.md` and, if there's a supported-tickers list, keep it in a sibling `.md` file (see `marketpulse/earnings-press-releases-tickers.md`).
- Async task endpoints (video generation, OAuth) poll via a task-id GET — follow the pattern already in `media-gen/scripts/media_gen_client.py` rather than reinventing.

## Running a skill locally

```bash
export AISA_API_KEY="..."
python3 <skill>/scripts/<client>.py <subcommand> [--flags]
```

There is no test harness. Verify changes by running the client against the live API with a real key.
