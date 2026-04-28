# AIsa Twitter Post Engage

Post-launch Twitter/X follow-through variant for publishing, replies, and early engagement through the AIsa relay.

## What it does

- Search Twitter/X context before posting
- Publish posts after OAuth authorization
- Handle early likes, follows, and other follow-through actions through the bundled engagement client

## Best fit

- Use this when the user already has a tweet, launch, or campaign in motion and needs post-and-follow-through support.
- Use `aisa-twitter-api` for the flagship all-purpose Twitter lane.
- Use `aisa-twitter-engagement-suite` for ongoing engagement-heavy workflows.

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
python3 scripts/twitter_engagement_client.py like-latest --user "@elonmusk"
```

## Security & Trust

- Requires only `AISA_API_KEY`.
- All posting, OAuth approvals, and approved uploads are relayed through `api.aisa.one`.
- Do not claim a write action succeeded until the relay confirms it.
