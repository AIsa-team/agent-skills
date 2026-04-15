---
name: aisa-twitter-engagement-suite
description: Search X/Twitter profiles, tweets, trends, and approved engagement actions through the AIsa relay. Use when the user asks for Twitter/X research, posting, likes, follows, or related workflows without sharing passwords.
license: MIT-0
compatibility: Requires python3, AISA_API_KEY, and internet access to api.aisa.one. Uses relative paths for scripts and references to maximize compatibility across AgentSkills-compatible clients, including OpenClaw, Hermes, and Claude Code.
metadata:
  author: AIsa
  version: "1.0.6"
  homepage: https://aisa.one
  tags: twitter,x,engagement,automation,social-media
  openclaw:
    emoji: "🐦"
    primaryEnv: AISA_API_KEY
    requires:
      bins:
        - python3
      env:
        - AISA_API_KEY
  hermes:
    tags:
      - twitter
      - automation
      - engagement
allowed-tools: Read Grep Bash
---

# AIsa Twitter Engagement Suite

Search X/Twitter profiles, tweets, trends, and approved engagement actions through the AIsa relay.

## When to use

- The user wants Twitter/X research plus posting, liking, unliking, following, or unfollowing workflows.
- The task can use a Python client with `AISA_API_KEY` and explicit OAuth approval.
- The workflow needs a single package that covers read, post, and engagement actions.

## When NOT to use

- The user needs cookie extraction, password login, or a fully local Twitter client.
- The workflow must avoid relay-based network calls or media upload through `api.aisa.one`.
- The task needs undocumented secrets or browser-derived auth values.

## Quick Reference

- Required environment variable: `AISA_API_KEY`
- Read client: `scripts/twitter_client.py`
- Post client: `scripts/twitter_oauth_client.py`
- Engage client: `scripts/twitter_engagement_client.py`
- References: `references/post_twitter.md`, `references/engage_twitter.md`

## Setup

```bash
export AISA_API_KEY="your-key"
```

## Common Commands

```bash
python3 scripts/twitter_client.py search --query "AI agents" --type Latest
python3 scripts/twitter_oauth_client.py authorize
python3 scripts/twitter_engagement_client.py like-latest --user "@elonmusk"
```

## Capabilities

- Research Twitter/X accounts, tweets, trends, lists, communities, and Spaces.
- Publish text, image, and video posts after explicit OAuth approval.
- Like, unlike, follow, and unfollow after authorization exists.
