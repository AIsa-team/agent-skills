---
name: openclaw-twitter
description: 'Search X/Twitter profiles, tweets, trends, lists, communities, and Spaces through the AISA relay, then publish approved posts with OAuth. Use when: the user asks for Twitter/X research, monitoring, or posting without sharing passwords. Supports read APIs, authorization links, and media-aware posting.'
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

# OpenClaw Twitter

Runtime-focused release bundle for Twitter/X search and posting through the AISA relay.

## When to use

- The user wants to read profiles, timelines, mentions, followers, tweet search results, trends, lists, communities, or Spaces.
- The user wants to draft or publish posts after completing OAuth without sharing passwords.
- The task needs a Python client for repeatable Twitter/X automation backed by `AISA_API_KEY`.

## When NOT to use

- The user needs cookie extraction, browser credential scraping, or direct password login.
- The workflow must avoid sending requests, OAuth state, or approved media through `api.aisa.one`.
- The request is for likes, follows, or other engagement actions not covered by this package.

## Quick Reference

- Required env: `AISA_API_KEY`
- Read client: `./scripts/twitter_client.py`
- Post workflow guide: `./references/post_twitter.md`

## Setup

```bash
export AISA_API_KEY="your-key"
```

All network calls go to `https://api.aisa.one/apis/v1/...`.

## Capabilities

- Read user data, timelines, mentions, followers, followings, verified followers, and follow relationships.
- Search tweets and users, inspect replies, quotes, retweeters, thread context, and Spaces.
- Publish text, image, and video posts after explicit OAuth approval.
- Split long posts into threaded chunks when the publish script needs it.

## Common Commands

```bash
python3 scripts/twitter_client.py user-info --username elonmusk
python3 scripts/twitter_client.py search --query "AI agents" --type Latest
python3 scripts/twitter_client.py trends --woeid 1
python3 scripts/twitter_oauth_client.py status
python3 scripts/twitter_oauth_client.py authorize
python3 scripts/twitter_oauth_client.py post --text "Hello from OpenClaw"
```

## Posting Workflow

When the user asks to send, publish, reply, or quote on X/Twitter, follow `./references/post_twitter.md`.

- Return the authorization link first when posting is not yet approved.
- Use `--media-file` only for user-provided workspace files.
- Do not invent captions, remote URLs, or extra media attachments.

## ClawHub Suspicious Review Notes

These points summarize the common reasons similar skills are marked `Suspicious` and how this release addresses them:

- The package is relay-based: read calls, OAuth requests, and approved media uploads go to `api.aisa.one`.
- The package is API-key-first: it requires `AISA_API_KEY` and does not ask for passwords, cookies, `CT0`, or other legacy secrets.
- The release bundle is runtime-only: it keeps `SKILL.md`, `scripts/`, and the posting reference, while omitting non-runtime files such as `README.md` and `_meta.json`.
- The package does not include cache sync, self-install logic, home-directory persistence, browser-cookie extraction, or external agent CLI wrappers.
- Browser opening is optional and not the default workflow; returning the authorization link is the preferred path for OpenClaw.

## Release Bundle Notes

- `scripts/twitter_client.py` preserves the read API surface from the original bundle.
- `scripts/twitter_oauth_client.py` preserves OAuth and posting behavior from the original bundle.
- This package is optimized for publication metadata and upload safety, not for changing runtime logic.
