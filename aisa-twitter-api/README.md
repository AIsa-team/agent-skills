# AIsa Twitter API

Flagship Twitter/X command center for research, monitoring, watchlists, and approved posting through the AIsa relay.

## What it does

- Search Twitter/X profiles, tweets, trends, lists, communities, and Spaces
- Inspect timelines, mentions, replies, quotes, and thread context
- Support watchlist-style monitoring and approved posting workflows through OAuth
- Relay API requests, OAuth approvals, and approved media uploads through `https://api.aisa.one`

## Best fit

- Use this as the primary Twitter/X skill when the user wants one general-purpose surface.
- Use `aisa-twitter-engagement-suite` when the task is mainly likes, follows, replies, or other engagement actions.
- Use `aisa-twitter-command-center` when the task is mainly watchlists, trend scanning, and monitoring.

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

## Security & Trust

- Requires only `AISA_API_KEY`.
- Does not require passwords or browser cookies.
- Do not claim posting succeeded until the relay returns success.
