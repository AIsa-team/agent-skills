---
name: aisa-twitter-api
description: 'Twitter/X command center for research, monitoring, watchlists, and approved posting through AIsa. Use when: the user needs one flagship skill for trend tracking, competitor monitoring, or publish-ready Twitter workflows without sharing passwords. Supports search, watchlists, and OAuth-gated posting.'
version: 1.0.5
license: Apache-2.0
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: 🐦
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# AIsa Twitter API Command Center

Run Twitter/X research, monitoring, trend discovery, and approved posting from one AIsa-backed command center.

## When to use

- The user wants one Twitter/X skill for research, monitoring, or content discovery.
- The user wants to inspect profiles, timelines, mentions, trends, replies, quotes, lists, communities, or Spaces.
- The user wants to draft or publish posts after explicit OAuth approval without sharing passwords.

## When NOT to use

- The user needs password-based login, cookie extraction, or browser credential scraping.
- The workflow must avoid relay-based calls to `api.aisa.one`.
- The request centers on likes, follows, replies, or growth actions better handled by `aisa-twitter-engagement-suite`.

## Quick Reference

- Required environment variable: `AISA_API_KEY`
- Read client: `scripts/twitter_client.py`
- OAuth and posting client: `scripts/twitter_oauth_client.py`
- Posting guide: `references/post_twitter.md`

## Setup

```bash
export AISA_API_KEY="your-key"
```

## Capabilities

- Read user data, timelines, mentions, followers, followings, and related profile information.
- Search tweets and users, inspect replies, quotes, retweeters, thread context, trends, lists, communities, and Spaces.
- Publish text, image, and video posts after explicit OAuth approval.

## High-Intent Workflows

- Research a creator, competitor, or narrative before writing.
- Monitor a keyword, launch, or watchlist and pull supporting tweets fast.
- Draft and publish a post only after the user explicitly approves OAuth.

## Common Commands

```bash
python3 scripts/twitter_client.py search --query "AI agents" --type Latest
python3 scripts/twitter_oauth_client.py authorize
python3 scripts/twitter_oauth_client.py post --text "Hello from AIsa"
```

## Guardrails

- Do not ask for Twitter passwords or browser cookies.
- Do not invent captions, tweet URLs, or attachment files.
- Do not claim external posting succeeded until the API confirms success.

## Example Requests

- Research what builders on X are saying about AI agents this week.
- Track reactions to our product launch and pull representative tweets.
- Build a small watchlist of competitor accounts and summarize what changed today.
- Authorize and publish a short Twitter post with an attached image.

## Security Notes

- The workflow is relay-based and sends API requests, OAuth requests, and approved media uploads to `api.aisa.one`.
- Required secret: `AISA_API_KEY`.
- This workflow does not require passwords or browser cookie extraction.
