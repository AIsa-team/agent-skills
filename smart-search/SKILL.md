---
name: smart-search
description: Intelligent hybrid search combining web and academic sources via AIsa Smart Search endpoint. Best when you need both web and scholarly results.
---

# AIsa Smart Search

Intelligent hybrid search that combines web and academic sources using the AIsa Smart Search endpoint. Automatically blends general web results with scholarly articles for comprehensive coverage.

## Setup

This skill requires the `AISA_API_KEY` environment variable. When installed as a Claude plugin, the key is configured via the plugin's `userConfig`.

## Usage

Run the search client with the `smart` subcommand:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/smart-search/scripts/search_client.py smart --query "<search query>" --count <max_results>
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--query` / `-q` | Yes | — | Search query |
| `--count` / `-c` | No | 10 | Maximum number of results (1–100) |

### Example

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/smart-search/scripts/search_client.py smart --query "impact of large language models on software engineering" --count 10
```

## Output

The script prints a mixed set of results from both web and academic sources, including titles, URLs, and content snippets.

## When to Use

Use this skill when the user's query spans both general knowledge and academic research. For example, questions about emerging technologies, scientific topics with practical applications, or any query where both web articles and papers would be valuable.
