# AIsa Agent Skills ⚡

> **Production-ready skills for autonomous agents.** Compatible with any
> [agentskills.io](https://agentskills.io) harness — Claude Code, Claude,
> OpenAI Codex, Cursor, Gemini CLI, OpenCode, Goose, OpenClaw, Hermes,
> and others that implement the [Agent Skills specification](https://agentskills.io/specification).

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

---

## What is this?

A catalog of agent skills powered by the [AIsa](https://aisa.one) unified
API gateway. Each top-level directory is one self-contained skill — a
bundle of `SKILL.md`, `README.md`, and supporting scripts that any
skills-compatible harness can consume. One `AISA_API_KEY` covers them
all.

---

## Available skills

| Skill | What it does |
|---|---|
| [**last30days**](./last30days/) 📰 | 30-day multi-source research brief across Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, GitHub, and grounded web. Returns a ranked, clustered brief with citations. |
| [**MarketPulse**](./marketpulse/) 📊 | Real-time and historical equity data — prices, news, financial statements, analyst estimates, insider/institutional activity, SEC filings, earnings press releases, stock screening, macro interest rates. |
| [**Media Gen**](./media-gen/) 🎬 | Generate images and videos. 4 image models across 3 endpoints (Gemini, Wan 2.7 image/pro, Seedream) and 4 Wan video variants (wan2.6/2.7 × t2v/i2v). |
| [**Multi-source Search**](./multi-source-search/) 🔎 | Unified web + scholar + Tavily + Perplexity Sonar retrieval. Ranked results, content extraction, recursive crawling, site mapping. |
| [**Perplexity Search**](./perplexity-search/) 🔎 | Perplexity Sonar family — fast answers, pro synthesis, chain-of-thought reasoning, deep research reports — all through AIsa. |
| [**Prediction Market Arbitrage**](./prediction-market-arbitrage/) ⚖️ | Cross-platform arbitrage detection. Match events across Polymarket and Kalshi, compare implied probabilities, verify orderbook depth. |
| [**Prediction Market Data**](./prediction-market-data/) 📈 | Unified access to Polymarket and Kalshi — market discovery, pricing, orderbooks, trade history, wallet positions, P&L. |
| [**Twitter Autopilot**](./twitter-autopilot/) 🐦 | Full X/Twitter intelligence — profiles, timelines, mentions, search, trends, lists, communities, Spaces. OAuth-gated write for posting, liking, following. |
| [**YouTube SERP**](./youtube-serp/) 📺 | YouTube search with ranked results and rich metadata. Content-gap analysis, competitor tracking, keyword research. |

---

## Quick start

### 1. Get an AIsa API key

```bash
export AISA_API_KEY="sk-..."
```

Get one at [aisa.one](https://aisa.one).

### 2. Pick a skill and invoke it

Each skill lives in its own directory and carries a `SKILL.md`
(agent-facing spec) and a `README.md` (human-facing overview). The
harness auto-discovers `SKILL.md`; humans can skim the README.

For example, to run `last30days` directly from the command line:

```bash
bash last30days/scripts/run-last30days.sh "OpenAI Agents SDK"
```

See each skill's README for per-skill usage.

---

## Compatibility

Every skill in this repo works with any
[agentskills.io](https://agentskills.io)-compatible harness, including:

- **Claude Code** and **Claude** (Anthropic)
- **OpenAI Codex**
- **Cursor**
- **Gemini CLI** (Google)
- **OpenCode**, **Goose**, **OpenClaw**, **Hermes**
- and any other harness that implements the
  [Agent Skills specification](https://agentskills.io/specification)

Requires Python 3, a POSIX shell, and `AISA_API_KEY`. Individual skills
may require additional environment variables — check each skill's
`SKILL.md`.

---

## Contributing a skill

1. Read [`SKILL_AUTHORING.md`](./SKILL_AUTHORING.md) — the house SOP for
   composing skills in this repo. It covers directory layout, required
   frontmatter fields, body structure, canonical documentation links,
   and the pre-PR validation checklist.
2. Create a new top-level `<skill-name>/` directory following the SOP.
3. Open a PR. Every skill must include:
   - `SKILL.md` — agent-facing contract (frontmatter + instructions)
   - `README.md` — human-facing overview
   - A `## Compatibility` section listing supported harnesses
   - A `## API Reference` section pointing to `aisa.one/docs/api-reference`

See existing skills in this repo for reference. The
[agentskills.io specification](https://agentskills.io/specification) is
the authoritative source for the `SKILL.md` format.

---

## Links

- ⚡ [AIsa](https://aisa.one) — unified API gateway
- 📖 [Documentation](https://aisa.one/docs) — guides, models, API reference
- 🧭 [Agent Skills spec](https://agentskills.io/specification) — upstream format
- 📋 [`SKILL_AUTHORING.md`](./SKILL_AUTHORING.md) — house authoring SOP
- 🤖 [`CLAUDE.md`](./CLAUDE.md) — Claude Code's guide to this repo

---

## License

This repo uses a **dual-license arrangement**:

- **Source / contributions** — Apache-2.0 (see [LICENSE](LICENSE)). Governs
  this repo's contributor bargain: explicit patent grant, attribution,
  notice preservation.
- **Per-skill distribution** — MIT, declared in each skill's `SKILL.md`
  `license:` frontmatter. This is what the packaged skill ships under
  when it's redistributed via [clawhub.ai](https://clawhub.ai).

Both are intentional and mutually compatible. See
[`SKILL_AUTHORING.md`](./SKILL_AUTHORING.md#dual-license-arrangement)
for details.

---

<p align="center">
  <b>AIsa Agent Skills</b> — extend your agent's capabilities.
</p>
