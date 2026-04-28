# AIsa Twitter Engagement Suite

Engagement-focused Twitter/X variant for likes, follows, replies, and approved posting through the AIsa relay.

## What it does

- Search Twitter/X profiles, tweets, and trends
- Publish through OAuth after explicit approval
- Like, unlike, follow, and unfollow through a bundled Python client

## Best fit

- Use this when the user already knows what to engage with and needs action-oriented Twitter/X follow-through.
- Use `aisa-twitter-api` for the flagship all-purpose Twitter lane.
- Use `aisa-twitter-command-center` for watchlists, trend scanning, and recurring monitoring.

## Setup

```bash
export AISA_API_KEY="your-key"
```

Requires:

- `python3`
- network access to `https://api.aisa.one/apis/v1/...`

## Security & Trust

- Requires only `AISA_API_KEY`.
- All write actions and approved uploads are relayed through `api.aisa.one`.
- Do not claim a write action succeeded until the API confirms it.
