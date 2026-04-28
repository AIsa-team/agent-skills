# AIsa YouTube Search

Cross-platform YouTube discovery skill for AgentSkills-compatible clients.

## What it does

- Search YouTube videos, channels, and playlists through the AIsa relay
- Apply locale and filter parameters without managing Google credentials
- Use simple `curl` requests for lightweight research workflows

## Setup

```bash
export AISA_API_KEY="your-key"
```

Requires:

- `curl`
- network access to `https://api.aisa.one/apis/v1/youtube/search`

## Common Commands

```bash
curl -s "https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=machine+learning+tutorial" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

## Platform Notes

- AgentSkills: lightweight `SKILL.md`-only package with curl-based examples.
- OpenClaw: `metadata.openclaw` includes environment and binary hints.
- Hermes: can be categorized under research or media skills.
- Claude Code: works as a standalone skill, or can be wrapped in a plugin later.
