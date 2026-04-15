# AIsa Twitter API

Cross-platform Twitter/X research and posting skill for AgentSkills-compatible clients.

## What it does

- Search Twitter/X profiles, tweets, trends, lists, communities, and Spaces
- Inspect timelines, mentions, replies, quotes, and thread context
- Support approved posting workflows through OAuth

## Setup

```bash
export AISA_API_KEY="your-key"
```

Requires:

- `python3`
- network access to `https://api.aisa.one/apis/v1/...`

## Common Commands

```bash
python3 scripts/twitter_client.py search --query "AI agents" --type Latest
python3 scripts/twitter_oauth_client.py authorize
python3 scripts/twitter_oauth_client.py post --text "Hello from AIsa"
```
