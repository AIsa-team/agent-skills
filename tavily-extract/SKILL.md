---
name: tavily-extract
description: Extract clean, readable content from one or more URLs using Tavily Extract via AIsa API. Useful for reading full articles without visiting the page.
---

# AIsa Tavily Extract

Extract clean, readable content from one or more URLs using the Tavily Extract endpoint via AIsa API. Converts web pages into structured text, stripping ads, navigation, and other noise.

## Setup

This skill requires the `AISA_API_KEY` environment variable. When installed as a Claude plugin, the key is configured via the plugin's `userConfig`.

## Usage

Run the search client with the `extract` subcommand:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/tavily-extract/scripts/search_client.py extract --urls "<comma-separated URLs>"
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--urls` / `-u` | Yes | — | Comma-separated list of URLs to extract content from |

### Examples

```bash
# Extract a single article
python3 ${CLAUDE_PLUGIN_ROOT}/skills/tavily-extract/scripts/search_client.py extract --urls "https://example.com/article"

# Extract multiple pages
python3 ${CLAUDE_PLUGIN_ROOT}/skills/tavily-extract/scripts/search_client.py extract --urls "https://example.com/page1,https://example.com/page2"
```

## Output

For each URL, the script prints:
- **URL** — The source URL
- **Content** — Clean extracted text (up to 3000 characters per page)

## When to Use

Use this skill when the user provides a URL and wants to read or analyze its content, or when you need to fetch the full text of an article found via search. This is the best tool for "read this page" or "summarize this URL" requests.
