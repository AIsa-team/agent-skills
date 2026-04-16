---
name: scholar-search
description: Search academic papers and scholarly articles via AIsa Scholar endpoint. Supports year range filtering for targeted research.
---

# AIsa Scholar Search

Search academic papers and scholarly articles using the AIsa Scholar Search endpoint. Ideal for finding peer-reviewed research, conference papers, and citations. Supports year range filtering.

## Setup

This skill requires the `AISA_API_KEY` environment variable. When installed as a Claude plugin, the key is configured via the plugin's `userConfig`.

## Usage

Run the search client with the `scholar` subcommand:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/scholar-search/scripts/search_client.py scholar --query "<academic query>" --count <max_results> [--year-from YYYY] [--year-to YYYY]
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--query` / `-q` | Yes | — | Academic search query |
| `--count` / `-c` | No | 10 | Maximum number of results (1–100) |
| `--year-from` | No | — | Year lower bound (e.g., 2023) |
| `--year-to` | No | — | Year upper bound (e.g., 2026) |

### Examples

```bash
# Search for recent transformer papers
python3 ${CLAUDE_PLUGIN_ROOT}/skills/scholar-search/scripts/search_client.py scholar --query "transformer architecture attention mechanism" --count 10 --year-from 2024

# Search papers in a specific year range
python3 ${CLAUDE_PLUGIN_ROOT}/skills/scholar-search/scripts/search_client.py scholar --query "reinforcement learning from human feedback" --year-from 2022 --year-to 2025
```

## Output

The script prints structured academic results including:
- **Title** — Paper title
- **URL** — Link to the paper or abstract
- **Publication info** — Journal, conference, or preprint source
- **Snippet** — Abstract excerpt

## When to Use

Use this skill when the user needs academic papers, scholarly articles, research citations, or peer-reviewed sources. Best for literature reviews, citation lookups, and academic research tasks.
