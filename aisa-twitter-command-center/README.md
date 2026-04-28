# AIsa Twitter Command Center

Watchlist and trend-desk variant for Twitter/X monitoring through the AIsa relay.

## What it does

- Track competitor accounts, recurring watchlists, timelines, trends, lists, communities, and Spaces
- Inspect mentions, replies, quotes, and thread context during monitoring work
- Support approved posting workflows through OAuth when monitoring turns into action
- Reuse the same skill package across OpenClaw, Hermes, Claude Code, and other compatible runtimes

## Best fit

- Use this when the user primarily wants monitoring, watchlists, or trend scanning.
- Use `aisa-twitter-api` for the flagship all-purpose Twitter lane.
- Use `aisa-twitter-engagement-suite` for likes, follows, replies, and heavier engagement flows.

## Directory Layout

```text
aisa-twitter-command-center/
├── SKILL.md
├── README.md
├── scripts/
│   ├── twitter_client.py
│   └── twitter_oauth_client.py
└── references/
    └── post_twitter.md
```

## Setup

```bash
export AISA_API_KEY="your-key"
```

Requires:

- `python3`
- network access to `https://api.aisa.one/apis/v1/...`

## Common Commands

```bash
python3 scripts/twitter_client.py user-info --username elonmusk
python3 scripts/twitter_client.py search --query "AI agents" --type Latest
python3 scripts/twitter_oauth_client.py status
python3 scripts/twitter_oauth_client.py authorize
python3 scripts/twitter_oauth_client.py post --text "Hello from AIsa"
```

## Platform Notes

- AgentSkills: the package follows the standard `SKILL.md + scripts + references` structure.
- OpenClaw: `metadata.openclaw` is included for environment and runtime hints.
- Hermes: the skill can be used as-is, with optional categorization in a Hermes skill tree.
- Claude Code: the skill can run standalone, or be wrapped into a plugin marketplace package for distribution.

## Security Notes

- Requests, OAuth operations, and approved media uploads go to `api.aisa.one`.
- The skill requires `AISA_API_KEY`.
- The workflow is designed to avoid direct password sharing and browser-cookie extraction.
