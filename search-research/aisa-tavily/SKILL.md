---
name: aisa-tavily
description: 'Search the web and extract public page content through AIsa''s Tavily-backed API relay. Use when: the user needs web search, source discovery, current news lookup, or URL content extraction. Supports concise result sets, deeper research, and news-focused queries.'
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries node, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  version: "1.0.0"
  aisa:
    emoji: 🔎
    requires:
      bins:
      - node
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries node, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# AIsa Tavily Search

Search the web and extract public page content through AIsa's Tavily-backed API relay. Use this skill when the user needs open-web research, source discovery, current-news lookup, or readable extraction from a specific public URL.

## When to use

- When the user needs web search results for a topic, question, company, product, or event
- When the user wants source discovery before summarizing, comparing, or validating information
- When the user needs current-news lookup with recent-day filtering
- When the user provides a public URL and wants the page content extracted for downstream analysis

## When NOT to use

- Do not use this skill for sites that require login, browser interaction, cookies, or private account access
- Do not use this skill for posting, social engagement, media upload, or OAuth-based workflows; it performs search and public-URL extraction only
- Do not use this skill when there is no network access to `https://aisa.one` or `https://api.aisa.one`

## Quick Reference

| Task | Command |
| --- | --- |
| Search the web | `node scripts/search.mjs "query"` |
| Search with more results | `node scripts/search.mjs "query" -n 10` |
| Run deeper research | `node scripts/search.mjs "query" --deep` |
| Search news | `node scripts/search.mjs "query" --topic news` |
| Search recent news only | `node scripts/search.mjs "query" --topic news --days 7` |
| Extract content from a URL | `node scripts/extract.mjs "https://example.com/article"` |

## Capabilities

- Search the web through AIsa's Tavily-backed relay
- Return concise, relevant result sets for research and agent workflows
- Run deeper research with `--deep` for broader coverage
- Focus on news search with `--topic news`
- Limit news lookback windows with `--days <n>`
- Extract readable content from a public URL

## Search

```bash
node scripts/search.mjs "query"
node scripts/search.mjs "query" -n 10
node scripts/search.mjs "query" --deep
node scripts/search.mjs "query" --topic news
```

## Options

- `-n <count>`: Number of results (default: 5, max: 20)
- `--deep`: Use advanced search for deeper research (slower, more comprehensive)
- `--topic <topic>`: Search topic - `general` (default) or `news`
- `--days <n>`: For news topic, limit to last n days

## Extract content from URL

```bash
node scripts/extract.mjs "https://example.com/article"
```

## Setup

Requirements:
- `node`
- `AISA_API_KEY`
- Internet access with outbound requests to `https://aisa.one` and `https://api.aisa.one`

Auth, relay, and side-effect notes:
- This skill requires `AISA_API_KEY` from https://marketplace.aisa.one
- Requests are sent through AIsa's remote relay at `https://aisa.one` and `https://api.aisa.one`
- This skill does not use OAuth
- This skill does not upload media or files
- This skill may send user search queries and public target URLs to the remote AIsa relay in order to return search results or extracted content

## Example Requests

- "Search for recent coverage of OpenAI enterprise pricing"
- "Find sources comparing vector databases for production RAG"
- "Look up this week's news about NVIDIA export controls"
- "Extract the main content from this article URL"

## Notes

- Needs `AISA_API_KEY` from https://marketplace.aisa.one
- Powered by AIsa's unified API gateway (`https://aisa.one` / `https://api.aisa.one`)
- Use `--deep` for complex research questions
- Use `--topic news` for current events
- Search and extraction operate through remote relay requests, not local browser automation
