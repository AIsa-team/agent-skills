---
name: web-search
description: 'Search the web using AIsa Scholar Web endpoint. Returns structured web results with titles, URLs, and snippets. Use when: the user needs web search, research, source discovery, or content extraction.'
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

# AIsa Web Search

Search the web using the AIsa Scholar Web Search endpoint. Returns structured results with titles, URLs, and content snippets.

## Setup

This skill requires the `AISA_API_KEY` environment variable. When installed as a Claude plugin, the key is configured via the plugin's `userConfig`.

## Usage

Run the search client with the `web` subcommand:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/web-search/scripts/search_client.py web --query "<search query>" --count <max_results>
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--query` / `-q` | Yes | — | The search query string |
| `--count` / `-c` | No | 10 | Maximum number of results (1–100) |

### Example

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/web-search/scripts/search_client.py web --query "latest AI agent frameworks 2026" --count 5
```

## Output

The script prints structured results including:
- **Title** — Page title
- **URL** — Direct link to the source
- **Snippet** — Content excerpt relevant to the query

## When to Use

Use this skill when the user asks to search the web, find information online, look up recent events, or needs general web results. This is the most versatile search tool for broad queries.
