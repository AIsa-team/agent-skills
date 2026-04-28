---
name: aisa-youtube-serp-scout
description: 'Search YouTube videos, channels, and trends through the AIsa YouTube SERP client. Use when the user asks for content research, competitor tracking, or trend discovery without managing Google credentials. Use when: the user needs YouTube search, trend discovery, channel research, or SERP analysis.'
version: 1.0.2
license: MIT-0
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: 📺
    requires:
      bins:
      - curl
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# AIsa YouTube SERP Scout

Search YouTube videos, channels, and trends through the AIsa relay for content research, competitor tracking, and trend discovery.

## When to use

- The user wants YouTube content research, channel discovery, or trend monitoring.
- The workflow benefits from a bundled Python client for repeated searches.
- The task can use `AISA_API_KEY` instead of direct Google API credentials.

## When NOT to use

- The user needs browser automation, local scraping, or account-level YouTube actions.
- The workflow must avoid sending search requests to `api.aisa.one`.
- The request depends on files outside this package.

## Quick Reference

- Required environment variable: `AISA_API_KEY`
- Endpoint: `https://api.aisa.one/apis/v1/youtube/search`
- Python client: `scripts/youtube_client.py`

## Setup

```bash
export AISA_API_KEY="your-key"
```

## Common Commands

```bash
curl "https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=AI+agents+tutorial" \
  -H "Authorization: Bearer $AISA_API_KEY"

python3 scripts/youtube_client.py search --query "AI agents tutorial"
python3 scripts/youtube_client.py search --query "machine learning" --country us
python3 scripts/youtube_client.py competitor --name "OpenAI" --topic "GPT tutorial"
```

## Capabilities

- Search videos, channels, and playlists with `q`
- Filter by country with `gl` and language with `hl`
- Reuse `sp` tokens for pagination or SERP narrowing
- Run competitor and top-video research from the bundled Python client

## Guardrails

- Do not ask for Google credentials or browser cookies.
- Do not claim competitor analysis succeeded before the client returns data.
- Do not assume missing locale values when the user needs a specific market.

## Security Notes

- All search requests go to `api.aisa.one`.
- Required secret: `AISA_API_KEY`.
- This package does not include browser automation, local scraping, or account actions.
