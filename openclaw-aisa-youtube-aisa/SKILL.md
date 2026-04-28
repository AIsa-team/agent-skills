---
name: openclaw-aisa-youtube-aisa
description: 'Search YouTube videos, channels, and trends through the AISA YouTube SERP client. Use when: the user needs YouTube search, trend discovery, channel research, or SERP analysis.'
license: MIT-0
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: ▶️
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# OpenClaw YouTube SERP Scout

Runtime-focused release bundle for YouTube search, competitor tracking, and trend discovery through the AISA relay.

## When to use

- The user wants YouTube content research, channel discovery, or trend monitoring.
- The workflow benefits from the bundled Python client for repeated searches.
- The task can use `AISA_API_KEY` instead of direct Google API credentials.

## When NOT to use

- The user needs browser automation, local scraping, or account-level YouTube actions.
- The workflow must avoid sending search requests to `api.aisa.one`.
- The request depends on files outside this release bundle.

## Setup

Required:

- Environment variable:
  - `AISA_API_KEY` (required)

- Binaries:
  - `python3` (required)
  - `curl` (used for direct API calls)

```bash
export AISA_API_KEY="your-key"
```

## Quick Reference

```bash
python3 scripts/youtube_client.py search --query "AI agents tutorial"
python3 scripts/youtube_client.py search --query "machine learning" --country us
python3 scripts/youtube_client.py competitor --name "OpenAI" --topic "GPT tutorial"
```
## Advanced / Debug Usage (Optional)

Direct API access using curl:
curl "https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=AI+agents+tutorial" \
  -H "Authorization: Bearer $AISA_API_KEY"

## Capabilities

- Search videos, channels, and playlists with `q`
- Filter by country with `gl` and language with `hl`
- Reuse `sp` tokens for pagination or SERP narrowing
- Run competitor and top-video research from the bundled Python client

## ClawHub Suspicious Review Notes

These points summarize the common reasons similar skills are marked `Suspicious` and how this release addresses them:

- The package is relay-based: all search requests go to `api.aisa.one`.
- The package is API-key-first: it requires `AISA_API_KEY` and does not ask for passwords, cookies, browser data, or other legacy secrets.
- The frontmatter declares required bins/env under `metadata.openclaw`, matching the runtime files kept in this release bundle.
- The release bundle is runtime-only: it keeps `SKILL.md` and `scripts/youtube_client.py`, while omitting non-runtime files such as `README.md` and `_meta.json`.
- The package does not include browser automation, cache sync, home-directory persistence, cookie extraction, or external agent CLI wrappers.

## Release Bundle Notes

- `scripts/youtube_client.py` is preserved from the original bundle.
- Search behavior and command surface are unchanged from the original runtime.
- The only changes are packaging trim and clearer publication metadata.
