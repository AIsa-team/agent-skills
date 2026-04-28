# OpenClaw Search 🔍

Intelligent search for autonomous agents with confidence scoring.

Inspired by [AIsa Verity](https://github.com/AIsa-team/verity) - A next-generation search agent with trust-scored answers.

## Features

- **Web Search**: Structured web results
- **Scholar Search**: Academic paper retrieval
- **Smart Search**: Intelligent hybrid search
- **Tavily Integration**: External validation
- **Verity Mode**: Multi-source search with confidence scoring

## Quick Start

```bash
export AISA_API_KEY="your-key"

# Single source search
python scripts/search_client.py web --query "AI frameworks"
python scripts/search_client.py scholar --query "transformer models"

# Multi-source with confidence scoring
python scripts/search_client.py verity --query "Is quantum computing enterprise-ready?"
```

## Confidence Scoring

The Verity-style search returns a deterministic confidence score (0-100):

| Score | Level | Meaning |
|-------|-------|---------|
| 90-100 | Very High | Strong consensus |
| 70-89 | High | Good agreement |
| 50-69 | Medium | Mixed signals |
| 30-49 | Low | Conflicting sources |
| 0-29 | Very Low | Insufficient data |

## Documentation

See [SKILL.md](SKILL.md) for complete API documentation.
