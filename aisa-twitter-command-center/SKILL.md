---
name: aisa-twitter-command-center
description: Search X/Twitter profiles, tweets, trends, lists, communities, and Spaces through the AIsa relay, then support approved posting workflows with OAuth. Use when the user asks for Twitter research, monitoring, or posting without sharing passwords.
license: Apache-2.0
compatibility: Requires python3, AISA_API_KEY, and internet access to api.aisa.one. Uses relative paths for scripts and references to maximize compatibility across AgentSkills-compatible clients, including OpenClaw, Hermes, and Claude Code.
metadata:
  author: AIsa
  version: "1.0.0"
  homepage: https://aisa.one
  tags: twitter,x,social-media,research,posting
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
      - research
      - posting
allowed-tools: Read Grep Bash
---

# AIsa Twitter Command Center

Search X/Twitter profiles, tweets, trends, lists, communities, and Spaces through the AIsa relay, then support approved posting workflows with OAuth.

## When to use

- The user wants Twitter/X research, monitoring, or content discovery.
- The user wants to inspect profiles, timelines, mentions, trends, replies, quotes, lists, communities, or Spaces.
- The user wants to draft or publish posts after explicit OAuth approval without sharing passwords.

## When NOT to use

- The user needs password-based login, cookie extraction, or browser credential scraping.
- The workflow must avoid relay-based calls to `api.aisa.one`.
- The request is for unsupported engagement actions not covered by this package.

## Quick Reference

- Required environment variable: `AISA_API_KEY`
- Read client: `scripts/twitter_client.py`
- OAuth and posting client: `scripts/twitter_oauth_client.py`
- Posting guide: `references/post_twitter.md`

## Setup

```bash
export AISA_API_KEY="your-key"
```

All network calls go to `https://api.aisa.one/apis/v1/...`.

## Capabilities

- Read user data, timelines, mentions, followers, followings, and related profile information.
- Search tweets and users, inspect replies, quotes, retweeters, thread context, trends, lists, communities, and Spaces.
- Publish text, image, and video posts after explicit OAuth approval.
- Return an authorization link when posting access has not been approved yet.

## Common Commands

```bash
python3 scripts/twitter_client.py user-info --username elonmusk
python3 scripts/twitter_client.py search --query "AI agents" --type Latest
python3 scripts/twitter_client.py trends --woeid 1
python3 scripts/twitter_oauth_client.py status
python3 scripts/twitter_oauth_client.py authorize
python3 scripts/twitter_oauth_client.py post --text "Hello from AIsa"
```

## Posting Workflow

When the user asks to send, publish, reply, or quote on X/Twitter:

1. Check whether `AISA_API_KEY` is configured.
2. If the user intent is to publish, attempt the publish workflow.
3. If authorization has not been completed, return the OAuth authorization link first.
4. Use `--media-file` only for user-provided local workspace files.
5. Do not claim the post succeeded until the publish command actually succeeds.

## Guardrails

- Do not ask for Twitter passwords or browser cookies.
- Do not invent captions, tweet URLs, or attachment files.
- Do not default to browser opening unless the user explicitly wants local browser launch.
- Do not claim external posting succeeded until the API confirms success.

## Security Notes

- The workflow is relay-based and sends API requests, OAuth requests, and approved media uploads to `api.aisa.one`.
- Required secret: `AISA_API_KEY`.
- This workflow does not require passwords, browser cookie extraction, or direct account credential sharing.

## References

- See `references/post_twitter.md` for detailed posting examples and OAuth guidance.
