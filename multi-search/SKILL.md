---
name: multi-search
description: 'Parallel multi-source search combining Web, Scholar, Smart, and Tavily results with confidence scoring and AI synthesis. Best for comprehensive research requiring cross-source validation. Use when: the user needs web search, research, source discovery, or content extraction.'
license: MIT
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: 🔎
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# AIsa Multi-Source Search

The most comprehensive search tool in this plugin. Queries Web, Scholar, Smart, and Tavily sources in parallel, then computes a confidence score based on source availability, result quality, and diversity. Optionally generates an AI synthesis of all results.

## Setup

This skill requires the `AISA_API_KEY` environment variable. When installed as a Claude plugin, the key is configured via the plugin's `userConfig`.

## Usage

Run the search client with the `verity` subcommand:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/multi-search/scripts/search_client.py verity --query "<search query>" --count <results_per_source>
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--query` / `-q` | Yes | — | Search query |
| `--count` / `-c` | No | 5 | Maximum results per source (1–20) |

### Example

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/multi-search/scripts/search_client.py verity --query "impact of AI on healthcare diagnostics" --count 5
```

## Output

The script prints:

1. **Individual results** from each source (Web, Smart, Scholar, Tavily)
2. **Confidence Assessment** with:
   - **Score** (0–100) — Overall confidence in the search results
   - **Level** — Very High / High / Medium / Low / Very Low
   - **Sources queried** and **Sources OK** — How many sources responded
   - **Total results** — Combined result count across all sources
3. **AI Synthesis** — A coherent summary combining insights from all sources, with citations

### Confidence Scoring Breakdown

| Factor | Weight | Description |
|--------|--------|-------------|
| Source availability | 40% | How many of the 4 sources returned results |
| Result quality | 35% | Ratio of actual results to expected results |
| Source diversity | 15% | Whether both academic and web sources are present |
| Recency bonus | 10% | Bonus for having at least one successful source |

## When to Use

Use this skill when the user needs the most thorough and reliable search results possible. Best for fact-checking, comprehensive research, verifying claims across multiple sources, or any query where cross-source validation adds significant value. This tool is slower but more reliable than individual search tools.
