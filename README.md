# OpenClaw Skills Collection 🦞

> **Official skill library for OpenClaw autonomous agents.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![OpenClaw Compatible](https://img.shields.io/badge/OpenClaw-Compatible-brightgreen.svg)](https://openclaw.ai)

---

## What is This?

This repository contains **production-ready skills** for [OpenClaw](https://openclaw.ai) autonomous agents. Each skill provides a specific capability that your agent can use.

---

### Available Skills

| Skill | Description | Status |
|-------|-------------|--------|
| [**Market**](./market/) | Query real-time and historical financial data across equities and crypto. | ✅ Ready |
| [**Media Gen**](./media-gen/) | Generate images & videos with AIsa. | ✅ Ready |
| [**Perplexity Search**](./perplexity-search/) | Perplexity Sonar search and answer generation through AIsa. | ✅ Ready |
| [**Prediction Market**](./prediction-market/) | Prediction markets data - Polymarket, Kalshi markets, prices, positions, and trades. | ✅ Ready |
| [**Prediction Market Arbitrage**](./prediction-market-arbitrage/) | Find and analyze arbitrage opportunities across prediction markets. | ✅ Ready |
| [**Search**](./search/) | Intelligent search for agents. Multi-source retrieval across web, scholar, Tavily, and Perplexity Sonar models. | ✅ Ready |
| [**Twitter**](./twitter/) | Searches and reads X (Twitter): profiles, timelines, mentions, followers, tweet search, trends, lists, communities, and Spaces. | ✅ Ready |
| [**YouTube**](./youtube/) | Search YouTube videos, channels, and trends. | ✅ Ready |

---

## Quick Start

### 1. Choose a Skill

Browse the skills above and pick what your agent needs.

### 2. Follow the Skill Guide

Each skill folder contains:
- `README.md` - Human-readable documentation
- `SKILL.md` - OpenClaw skill specification
- Supporting scripts and references

### 3. Configure Your Agent

```bash
# Example: Using the OpenClaw Starter Kit
export AISA_API_KEY="your-api-key"
```

---

## Adding New Skills

Want to contribute a skill? Each skill should include:

1. **SKILL.md** - OpenClaw skill specification with metadata
2. **README.md** - Human-readable documentation
3. **Scripts/Tools** - Any supporting code
4. **References** - API docs, examples

See existing skills in the `openclaw-skills/` directory for reference.

---

## Links

- 🦞 [OpenClaw](https://openclaw.ai) - The autonomous agent framework
- ⚡ [AIsa](https://aisa.one) - Unified API backend
- 📖 [Documentation](https://docs.aisa.one) - API reference

---

## License

Apache 2.0 License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>OpenClaw Skills</b> - Extend your agent's capabilities.
</p>
