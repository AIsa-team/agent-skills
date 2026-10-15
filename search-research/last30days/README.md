# last30days

Multi-source research skill for the last 30 days. One command pulls a
ranked, clustered brief on any topic across public and hosted sources: Reddit, X,
YouTube, TikTok, Instagram, Hacker News, Polymarket, and grounded web
search. Runtime depends on source coverage and provider latency.

## Quick start

```bash
# 1. Set your AIsa key
export AISA_API_KEY=sk-...

# 2. First-run setup (interactive model picker)
bash scripts/run-last30days.sh setup

# 3. Research a topic
bash scripts/run-last30days.sh "OpenAI Agents SDK" \
  --budget-usd "$APPROVED_BUDGET_USD" --cost-ledger research-costs.json
```

## Examples

```bash
bash scripts/run-last30days.sh --cost-ledger research-costs.json "OpenAI Agents SDK"
bash scripts/run-last30days.sh --cost-ledger research-costs.json "Claude Code vs Codex"
bash scripts/run-last30days.sh --cost-ledger research-costs.json "Peter Steinberger"
bash scripts/run-last30days.sh --cost-ledger research-costs.json "bitcoin price" --quick
bash scripts/run-last30days.sh --cost-ledger research-costs.json "Perplexity" --emit=json
```

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: **Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**,
**Gemini CLI**, **OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and
others that implement the
[Agent Skills specification](https://agentskills.io/specification).

Requires Python 3.11+ and a POSIX shell. Hosted retrieval needs `AISA_API_KEY` and an authorized budget.

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

- **Python 3.11+**
- **`AISA_API_KEY`** — enables hosted retrieval. TikTok and Instagram use indexed web discovery, not native engagement APIs. Get a key at [aisa.one](https://aisa.one).
- **`GH_TOKEN` or `GITHUB_TOKEN`** *(optional)* — enables the GitHub
  source. Without it the GitHub source is unavailable.

Reddit and Hacker News use public endpoints and need no credentials.

## Costs and reasoning

Use one durable ledger for each authorized task. Exact quotes are compared with
remaining budget, and actual charges are recorded separately. Unknown charges
block further paid work; paid requests are never automatically retried.
Variable estimates need `--allow-variable-cost` only when the user accepted that
final charges may exceed estimates. See [cost controls and recovery](references/cost-control.md).

Public-source/local runs and `--mock` need no paid authorization. Planning and
ranking have local fallbacks. Hosted chat calls are currently blocked because
the chat contract does not declare the quote/admission support required by this
release; retained model pins do not imply execution.

## Flags

| Flag | Meaning |
|---|---|
| `--quick` | Lower-latency retrieval profile (fewer candidates) |
| `--deep` | Higher-recall retrieval profile |
| `--emit=json` | Machine-readable output (default: markdown) |
| `--search=reddit,x,hackernews` | Restrict to specific sources |
| `--diagnose` | Inspect configured providers/sources; no live availability guarantee |
| `--budget-usd` | Authorize an exact estimate budget for a new ledger |
| `--cost-ledger` | Share/reuse a durable task budget and request records |
| `--allow-variable-cost` | Accept quotes whose final charge may exceed the estimate |
| `--save-dir=out/` | Persist the rendered brief to disk |
| `--store` | Persist findings to the local SQLite research store |

Run `bash scripts/run-last30days.sh --help` for the full list.

## API Reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for the
complete catalog of endpoints this skill can call.

## License

MIT — see [LICENSE](../LICENSE) at the category root.

## Tests

Run `bash scripts/run-tests.sh` for the offline regression suite. No pytest or live API key is required.
