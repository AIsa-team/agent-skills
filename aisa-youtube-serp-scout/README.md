# AIsa YouTube SERP Scout

Cross-platform YouTube research skill for AgentSkills-compatible clients.

## What it does

- Search YouTube videos, channels, and trends through the AIsa relay
- Use the bundled Python client for repeatable research workflows
- Support content research, competitor tracking, and trend discovery

## Setup

```bash
export AISA_API_KEY="your-key"
```

Requires:

- `python3`
- `curl`
- network access to `https://api.aisa.one/apis/v1/youtube/search`

## Common Commands

```bash
python3 scripts/youtube_client.py search --query "AI agents tutorial"
python3 scripts/youtube_client.py competitor --name "OpenAI" --topic "GPT tutorial"
```

## Platform Notes

- AgentSkills: standard `SKILL.md + scripts/` structure.
- OpenClaw: keeps OpenClaw metadata hints without changing the cross-platform body.
- Hermes: fits naturally into a research category.
- Claude Code: can use the same package as a standalone skill.
