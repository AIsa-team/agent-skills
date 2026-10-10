---
name: aisa-twitter-api
description: 'Twitter/X research, monitoring, watchlists, and OAuth-approved posting through AIsa. Use when: the user needs one flagship Twitter skill for trend tracking, competitor monitoring, timeline analysis, or approved posting without sharing passwords. Supports search, watchlists, relay-based reads, and OAuth-gated text or media posting.'
license: Apache-2.0
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  version: "1.0.5"
  aisa:
    emoji: 🐦
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
    version: 1.0.5
---

# AIsa Twitter API Command Center

Flagship Twitter/X skill for research, monitoring, watchlists, and OAuth-approved posting through the AIsa relay.

## When to use

- When the user wants one primary Twitter/X skill for research, monitoring, trend discovery, timeline review, or content discovery.
- When the user needs to inspect profiles, timelines, mentions, trends, replies, quotes, lists, communities, or Spaces.
- When the user wants to draft or publish posts after explicit OAuth approval without sharing passwords or browser cookies.
- When the workflow should use `AISA_API_KEY` and relay-based access to `https://api.aisa.one` instead of local credential extraction.

## When NOT to use

- Do NOT use this for password-based login, cookie extraction, or browser credential scraping.
- Do NOT use this when the workflow must avoid relay-based requests to `https://api.aisa.one`.
- Do NOT use this as the primary skill for like, follow, reply, or growth-action workflows better handled by `aisa-twitter-engagement-suite`.

## Quick Reference

- Required environment variable: `AISA_API_KEY`
- Required binary: `python3`
- Read client: `scripts/twitter_client.py`
- OAuth and posting client: `scripts/twitter_oauth_client.py`
- Posting guide: `references/post_twitter.md`
- Relay target: `https://api.aisa.one`
- External writes: posting happens only after explicit OAuth approval
- Upload behavior: image and video posting sends user-selected media through the relay

## Setup

```bash
export AISA_API_KEY="your-key"
```

Requirements:

- `python3`
- `AISA_API_KEY`
- Internet access to `https://api.aisa.one`
- Explicit OAuth approval before posting
- User-provided media files when posting images or videos

## Capabilities

- Read user data, timelines, mentions, followers, followings, and related profile information.
- Search tweets and users, inspect replies, quotes, retweeters, thread context, trends, lists, communities, and Spaces.
- Run watchlist-style research and monitoring workflows from one Twitter/X command surface.
- Publish text, image, and video posts after explicit OAuth approval.

## High-Intent Workflows

- Research a creator, competitor, brand, or narrative before writing.
- Monitor a keyword, launch, or watchlist and pull representative tweets quickly.
- Review timelines, mentions, replies, and trend movement from one command surface.
- Draft and publish a post only after the user explicitly approves OAuth.

## Common Commands

```bash
python3 scripts/twitter_client.py search --query "AI agents" --type Latest
python3 scripts/twitter_oauth_client.py authorize
python3 scripts/twitter_oauth_client.py post --text "Hello from AIsa"
```

## Guardrails

- Do not ask for Twitter/X passwords or browser cookies.
- Do not invent captions, tweet URLs, or attachment files.
- Do not claim external posting succeeded until the API confirms success.
- Do not imply OAuth is optional for posting.

## Example Requests

- Research what builders on X are saying about AI agents this week.
- Track reactions to our product launch and pull representative tweets.
- Build a small watchlist of competitor accounts and summarize what changed today.
- Authorize and publish a short Twitter post with an attached image.

## Security Notes

- This is a relay-based workflow that sends Twitter/X API requests to `https://api.aisa.one`.
- Posting requires explicit OAuth approval through the relay before external writes occur.
- Approved image and video posting sends user-selected media through the relay for upload.
- Required secret: `AISA_API_KEY`.
- This workflow does not require passwords or browser cookie extraction.
