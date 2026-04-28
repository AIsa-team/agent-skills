# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## What this repo is

A catalog of **agent skills** for the AIsa platform (https://aisa.one).
Each top-level directory is one self-contained skill:

- `last30days/` — 30-day multi-source research brief
- `marketpulse/` — equity market data
- `media-gen/` — image + video generation
- `multi-source-search/` — web, scholar, Tavily, Perplexity Sonar
- `perplexity-search/` — Perplexity Sonar family
- `prediction-market-arbitrage/` — cross-platform arbitrage
- `prediction-market-data/` — Polymarket + Kalshi data
- `twitter-autopilot/` — X/Twitter read + authenticated write
- `youtube-serp/` — YouTube search

Skills are consumed by any [agentskills.io](https://agentskills.io)-
compatible harness (Claude Code, Claude, OpenCode, Cursor, Codex,
Gemini CLI, OpenClaw, Hermes, Goose, and others). This repo is *not*
an application — there is no build system, dependency manifest, or
test suite.

## Authoring reference

`SKILL_AUTHORING.md` at the repo root is the **authoritative SOP** for
composing and maintaining skills. When making any change to a skill's
`SKILL.md`, `README.md`, or frontmatter, read that first. This file
(CLAUDE.md) only covers the runtime and editing invariants Claude Code
needs to know; `SKILL_AUTHORING.md` covers the format, validation, and
conventions.

## Skill anatomy

Every skill directory contains:

- **`SKILL.md`** — the agent-facing contract. YAML frontmatter with
  `name`, `description`, `license`, `compatibility`, and a `metadata`
  map that includes `metadata.aisa.{emoji, homepage, requires,
  primaryEnv, harnesses}`. Body is prose the agent reads at runtime:
  compatibility block, capabilities, quick start, usage examples,
  per-endpoint API reference.
- **`README.md`** — human-facing overview. Every skill has one.
  Mandatory sections: `## Compatibility` (harness list) and
  `## API Reference` (short pointer to `aisa.one/docs/api-reference`).
  See `SKILL_AUTHORING.md` for the verbatim block.
- **`scripts/*.py`, `scripts/*.sh`** — CLI entry points the agent
  invokes. **Zero runtime dependencies**: Python stdlib only
  (`urllib.request`, `argparse`, `json`, `sqlite3`, `email.utils`).
  Do not introduce `requests`, `httpx`, or other third-party libs —
  every skill must run with only `python3` and `curl` on the host.
- **`references/`** — extra prose files linked from `SKILL.md` when a
  workflow is too large to inline (e.g. `twitter-autopilot/references/`
  for OAuth-gated post/engage flows).

When `SKILL.md` references script paths, it uses the literal token
`{baseDir}` — e.g. `python3 {baseDir}/scripts/market_client.py ...` or
`bash {baseDir}/scripts/run-last30days.sh ...`. The harness substitutes
it at load time. Do **not** use `${SKILL_ROOT}`, `./scripts/...`, or
absolute paths.

## API surface

All clients hit `https://api.aisa.one` and authenticate with
`Authorization: Bearer $AISA_API_KEY`. Two base paths coexist:

- `/apis/v1/...` — the main AIsa REST surface (financial, twitter,
  polymarket, kalshi, youtube, search, perplexity, etc.)
- `/v1/...` — OpenAI-compatible surface (chat completions, models) used
  by `last30days` for planner/reranker/fun-scorer LLM calls, and
  `/v1/models/{model}:generateContent` for the Gemini passthrough used
  by `media-gen`.

## Documentation

All doc links use **`aisa.one/docs/...`** (never `docs.aisa.one` or
`aisa.mintlify.app`, which are legacy hosts). Canonical targets:

- `https://aisa.one/docs` — landing
- `https://aisa.one/docs/api-reference` — endpoint catalog
- `https://aisa.one/docs/api-reference/<category>/<slug>` — specific endpoint
- `https://aisa.one/docs/guides/models` — model catalog (read by
  `last30days`' interactive setup)
- `https://aisa.one/docs/llms.txt` — docs index for LLMs

## Conventions to preserve when editing

- Keep `SKILL.md` frontmatter spec-compliant. Required fields: `name`
  (matches directory, lowercase+hyphens), `description`, `license`,
  `compatibility`. See `SKILL_AUTHORING.md` for the full schema.
- Keep the `metadata.aisa.{emoji, homepage, requires, primaryEnv,
  harnesses}` shape intact — harnesses that read it rely on it.
- Keep CLI subcommand surfaces stable (e.g.
  `market_client.py stock prices ...`); `SKILL.md` examples are the
  spec and must stay in sync with `scripts/*.py`.
- When an endpoint has narrower coverage than siblings (e.g.
  `/financial/earnings/press-releases`), document the gotcha inline
  in `SKILL.md` and, if there's a supported-tickers list, keep it in a
  sibling `.md` file (see `marketpulse/earnings-press-releases-tickers.md`).
- Async task endpoints (video generation, OAuth) poll via a task-id GET —
  follow the pattern in `media-gen/scripts/media_gen_client.py` rather
  than reinventing.
- If adding a new harness that supports the agent-skills spec, update
  the canonical list in every skill's `metadata.aisa.harnesses`, its
  `compatibility:` sentence, and the `## Compatibility` body section —
  and update `SKILL_AUTHORING.md` so future skills inherit it.

## Running a skill locally

```bash
export AISA_API_KEY="..."
python3 <skill>/scripts/<client>.py <subcommand> [--flags]
```

`last30days` is the exception — it's a bash-wrapped Python skill:

```bash
export AISA_API_KEY="..."
bash last30days/scripts/run-last30days.sh setup      # first-run
bash last30days/scripts/run-last30days.sh "<topic>"
```

There is no test harness. Verify changes by running the client against
the live API with a real key.
