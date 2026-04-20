# last30days

Multi-source research skill for the last 30 days. One command pulls a
ranked, clustered brief on any topic across eight sources: Reddit, X,
YouTube, TikTok, Instagram, Hacker News, Polymarket, and grounded web
search — in ~40 seconds.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: **Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**,
**Gemini CLI**, **OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and
others that implement the
[Agent Skills specification](https://agentskills.io/specification).

Requires Python 3, a POSIX shell, and `AISA_API_KEY`.

## Quick start

```bash
# 1. Set your AIsa key
export AISA_API_KEY=sk-...

# 2. First-run setup (interactive model picker)
bash scripts/run-last30days.sh setup

# 3. Research a topic
bash scripts/run-last30days.sh "OpenAI Agents SDK"
```

## Examples

```bash
last30days "OpenAI Agents SDK"
last30days "Claude Code vs Codex"
last30days "Peter Steinberger"
last30days "bitcoin price" --quick
last30days "Perplexity" --emit=json
```

## What it returns

A single markdown (or JSON) brief:

- **Ranked evidence clusters** — top findings grouped by theme, each with
  a URL, date, engagement stats, and a one-line "why relevant" rationale
- **Stats** — items per source, top communities/domains/channels
- **Best Takes** — quirky or meme-worthy items (cosmetic)
- **Source coverage** — how many items each source contributed

Pass `--emit=json` for a machine-readable version with the full
`query_plan`, `ranked_candidates`, `clusters`, and `items_by_source`
fields — suitable for feeding into another agent.

## Requirements

- **Python 3.12+**
- **`AISA_API_KEY`** — powers the planner, reranker, fun-scorer, and
  hosted retrieval for X, YouTube, TikTok, Instagram, Polymarket, and
  grounded web search. Get one at [aisa.one](https://aisa.one).
- **`GH_TOKEN` or `GITHUB_TOKEN`** *(optional)* — enables the GitHub
  source. Without it the other seven sources still work.

Reddit and Hacker News use public endpoints and need no credentials.

## Per-role model configuration

The skill makes three LLM calls per run: planner (query structure),
reranker (relevance ranking), fun-scorer (quirkiness). Each can be pinned
independently:

```bash
# ~/.config/last30days/.env
LAST30DAYS_PLANNER_MODEL=qwen-flash           # fast + reliable JSON
LAST30DAYS_RERANK_MODEL=qwen-plus-2025-12-01  # quality ranking
LAST30DAYS_FUN_MODEL=qwen-flash               # cheap vibes
```

Or set `AISA_MODEL=...` for a single model across all three. The
interactive `setup` flow walks you through picking from the live
[AIsa model catalog](https://aisa.one/docs/guides/models).

## Flags

| Flag | Meaning |
|---|---|
| `--quick` | Lower-latency retrieval profile (fewer candidates) |
| `--deep` | Higher-recall retrieval profile |
| `--emit=json` | Machine-readable output (default: markdown) |
| `--search=reddit,x,hackernews` | Restrict to specific sources |
| `--diagnose` | Print provider / source availability |
| `--save-dir=out/` | Persist the rendered brief to disk |
| `--store` | Persist findings to the local SQLite research store |

Run `last30days --help` for the full list.

## API Reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for the
complete catalog of endpoints this skill can call.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
