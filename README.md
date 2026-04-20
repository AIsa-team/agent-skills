# AIsa Agent Skills ⚡

> **Production-ready skills for autonomous agents. Compatible with all major agent harnesses, including OpenClaw, Claude Code, and Hermes.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

---

## What is This?

This repository contains **production-ready skills** for autonomous agents powered by [AIsa](https://aisa.one). Each skill provides a specific capability that your agent can use, and is compatible with all major agent harnesses — including OpenClaw, Claude Code, and Hermes.

---

### Available Skills

| Skill | Description | Status |
|-------|-------------|--------|
| [**MarketPulse**](./marketpulse/) | Query real-time and historical financial data across equities and crypto. | ✅ Ready |
| [**Media Gen**](./media-gen/) | Generate images & videos with AIsa. | ✅ Ready |
| [**Perplexity Search**](./perplexity-search/) | Perplexity Sonar search and answer generation through AIsa. | ✅ Ready |
| [**Prediction Market Data**](./prediction-market-data/) | Prediction markets data - Polymarket, Kalshi markets, prices, positions, and trades. | ✅ Ready |
| [**Prediction Market Arbitrage**](./prediction-market-arbitrage/) | Find and analyze arbitrage opportunities across prediction markets. | ✅ Ready |
| [**Multi-source Search**](./multi-source-search/) | Multi-source intelligent search for agents. Retrieval across web, scholar, Tavily, and Perplexity Sonar models. | ✅ Ready |
| [**Twitter**](./twitter/) | Searches and reads X (Twitter): profiles, timelines, mentions, followers, tweet search, trends, lists, communities, and Spaces. | ✅ Ready |
| [**YouTube SERP**](./youtube-serp/) | Search YouTube videos, channels, and trends. | ✅ Ready |

---

## Quick Start

### 1. Choose a Skill

Browse the skills above and pick what your agent needs.

### 2. Follow the Skill Guide

Each skill folder contains:
- `README.md` - Human-readable documentation
- `SKILL.md` - Skill specification
- Supporting scripts and references

### 3. Configure Your Agent

```bash
# Example: Set your AIsa API key
export AISA_API_KEY="your-api-key"
```

---

## Adding New Skills

Want to contribute a skill? Each skill should include:

1. **SKILL.md** - Skill specification with metadata
2. **README.md** - Human-readable documentation
3. **Scripts/Tools** - Any supporting code
4. **References** - API docs, examples

See existing skills in this repository for reference.

---

## Links

- ⚡ [AIsa](https://aisa.one) - Unified API backend
- 📖 [Documentation](https://aisa.one/docs) - API reference

---

## License

Apache 2.0 License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>AIsa Agent Skills</b> - Extend your agent's capabilities.
</p>
