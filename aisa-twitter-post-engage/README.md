# AIsa Twitter Post Engage

Cross-platform Twitter/X research, posting, and engagement skill for AgentSkills-compatible clients.

## What it does

- Search Twitter/X data and monitor accounts or trends
- Publish posts after OAuth authorization
- Like, unlike, follow, and unfollow through the bundled engagement client

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
