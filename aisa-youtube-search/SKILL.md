---
name: aisa-youtube-search
description: Search YouTube videos, channels, and playlists through the AIsa YouTube relay with one API key. Use when the user asks for YouTube discovery, query expansion, or pagination without managing Google credentials.
license: MIT-0
compatibility: Requires curl, AISA_API_KEY, and internet access to api.aisa.one. Uses a lightweight curl-first workflow for broad compatibility across AgentSkills-compatible clients, including OpenClaw, Hermes, and Claude Code.
metadata:
  author: AIsa
  version: "1.0.3"
  homepage: https://aisa.one
  tags: youtube,search,serp,discovery,media
  openclaw:
    emoji: "🎬"
    primaryEnv: AISA_API_KEY
    requires:
      bins:
        - curl
      env:
        - AISA_API_KEY
  hermes:
    tags:
      - youtube
      - search
      - media
allowed-tools: Read Grep Bash
---

# AIsa YouTube Search

Search YouTube videos, channels, and playlists through the AIsa YouTube relay with one API key.

## When to use

- The user wants to search YouTube videos, channels, or playlists.
- The task needs region or language filters without direct Google API setup.
- The workflow can call the AIsa YouTube search endpoint with `AISA_API_KEY`.

## When NOT to use

- The user needs browser automation, local scraping, or direct YouTube account actions.
- The workflow must avoid sending search requests to `api.aisa.one`.
- The request depends on a local helper script that is not part of this package.

## Quick Reference

- Required environment variable: `AISA_API_KEY`
- Endpoint: `https://api.aisa.one/apis/v1/youtube/search`
- This package is curl-first and does not ship a local Python client.

## Setup

```bash
export AISA_API_KEY="your-key"
```

## Common Commands

```bash
curl -s "https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=machine+learning+tutorial" \
  -H "Authorization: Bearer $AISA_API_KEY"

curl -s "https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=AI+news&gl=us&hl=en" \
  -H "Authorization: Bearer $AISA_API_KEY"

curl -s "https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=python+tutorial&sp=EgIQAQ%3D%3D" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

## Capabilities

- Search YouTube SERP results with `q`
- Filter by locale with `gl` and `hl`
- Apply pagination or narrowing via `sp`
- Return structured results that may include `videos` or grouped `sections`

## Guardrails

- Do not ask for Google credentials or browser cookies.
- Do not claim a result is local-only when it depends on relay requests.
- Do not fabricate missing filters or parameters.

## Security Notes

- All search requests go to `api.aisa.one`.
- Required secret: `AISA_API_KEY`.
- This workflow does not require passwords, browser automation, or local scraping.
