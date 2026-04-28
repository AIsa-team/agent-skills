---
name: aisa-multi-search-engine
description: 'Multi-source search engine powered by AIsa API. Combines Tavily web search, Scholar academic search, Smart hybrid search, and Perplexity deep research — all through a single AIsa API key. Includes confidence scoring and AI synthesis. Use when: the user needs web search, research, source discovery, or content extraction.'
version: 1.0.2
license: MIT
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, node, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: 🔎
    requires:
      bins:
      - python3
      - node
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, node, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# AIsa Multi Search Engine v1.0.0

Multi-source search engine powered by [AIsa API](https://aisa.one). One API key unlocks web search, academic search, Tavily integration, and Perplexity deep research with confidence-scored results.

## Quick Start

```bash
export AISA_API_KEY="your-key-here"
```

Get your API key at [aisa.one](https://aisa.one).

## Search Tools

This plugin registers seven agent tools, each backed by a different AIsa API endpoint.

| Tool | Description | AIsa Endpoint |
|------|-------------|---------------|
| `aisa_web_search` | Structured web search results | `/scholar/search/web` |
| `aisa_scholar_search` | Academic paper search with year filtering | `/scholar/search/scholar` |
| `aisa_smart_search` | Intelligent hybrid search (web + academic) | `/scholar/search/smart` |
| `aisa_tavily_search` | Advanced web search with depth, topic, time, domain filters | `/tavily/search` |
| `aisa_tavily_extract` | Extract clean content from URLs | `/tavily/extract` |
| `aisa_perplexity_search` | Deep research via Perplexity Sonar models | `/sonar`, `/sonar-pro`, etc. |
| `aisa_multi_search` | Parallel multi-source search with confidence scoring | Multiple endpoints |

## Usage Examples

### Web Search

Search the web for structured results.

```
Use aisa_web_search to find "latest developments in AI agents 2025"
```

### Academic Search

Search scholarly papers with optional year filtering.

```
Use aisa_scholar_search to find papers on "transformer architecture" from 2024 to 2025
```

### Smart Search

Intelligent hybrid search combining web and academic sources.

```
Use aisa_smart_search to research "autonomous AI agents"
```

### Tavily Search (Advanced)

Advanced web search with filtering options.

```
Use aisa_tavily_search for "AI startup funding" with topic "news" and time_range "month"
```

### Tavily Extract

Extract full content from specific URLs.

```
Use aisa_tavily_extract to get content from ["https://example.com/article"]
```

### Perplexity Deep Research

Use Perplexity Sonar models for synthesized answers with citations.

```
Use aisa_perplexity_search to answer "What is the current state of quantum computing?" with model "sonar-pro"
```

| Model | Best For |
|-------|----------|
| `sonar` | Quick answers, fast response |
| `sonar-pro` | Detailed answers with more citations |
| `sonar-reasoning-pro` | Complex reasoning and analysis |
| `sonar-deep-research` | Exhaustive multi-step research |

### Multi-Source Search (Verity-Style)

Parallel search across all sources with confidence scoring and AI synthesis.

```
Use aisa_multi_search to comprehensively research "Is quantum computing ready for enterprise use?"
```

## Confidence Scoring

The `aisa_multi_search` tool provides a deterministic confidence score based on four factors.

| Factor | Weight | Description |
|--------|--------|-------------|
| Source Availability | 40% | How many search sources returned results |
| Result Quality | 35% | Volume of results relative to expectations |
| Source Diversity | 15% | Mix of academic and web sources |
| Recency | 10% | Bonus for having any successful sources |

| Score | Level | Interpretation |
|-------|-------|----------------|
| 90-100 | Very High | Strong consensus across sources |
| 70-89 | High | Good agreement, reliable sources |
| 50-69 | Medium | Mixed signals, verify independently |
| 30-49 | Low | Conflicting or sparse sources |
| 0-29 | Very Low | Insufficient data |

## Python CLI Client

A standalone Python client is included for command-line use.

```bash
# Web search
python3 scripts/search_client.py web --query "latest AI news" --count 10

# Academic search
python3 scripts/search_client.py scholar --query "transformer architecture" --year-from 2024

# Smart search
python3 scripts/search_client.py smart --query "autonomous agents" --count 10

# Tavily search
python3 scripts/search_client.py tavily --query "AI developments" --depth advanced

# Extract content from URLs
python3 scripts/search_client.py extract --urls "https://example.com/article"

# Perplexity deep research
python3 scripts/search_client.py sonar --query "quantum computing" --model sonar-pro

# Multi-source search with confidence scoring
python3 scripts/search_client.py verity --query "Is quantum computing ready?"
```

## API Endpoints Reference

All endpoints use the AIsa API base URL `https://api.aisa.one/apis/v1`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scholar/search/web` | POST | Web search with structured results |
| `/scholar/search/scholar` | POST | Academic paper search |
| `/scholar/search/smart` | POST | Intelligent hybrid search |
| `/scholar/explain` | POST | Generate result explanations with confidence |
| `/tavily/search` | POST | Tavily web search |
| `/tavily/extract` | POST | Extract content from URLs |
| `/tavily/crawl` | POST | Crawl web pages |
| `/tavily/map` | POST | Generate site maps |
| `/sonar` | POST | Perplexity Sonar (fast) |
| `/sonar-pro` | POST | Perplexity Sonar Pro (detailed) |
| `/sonar-reasoning-pro` | POST | Perplexity Sonar Reasoning Pro |
| `/sonar-deep-research` | POST | Perplexity Sonar Deep Research |

## Configuration

The plugin accepts the following configuration options.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `aisaApiKey` | string | — | AIsa API key (or set `AISA_API_KEY` env var) |
| `defaultMaxResults` | integer | 10 | Default max results per search (1-100) |
| `defaultSearchDepth` | string | `basic` | Default Tavily search depth |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Query                             │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌─────────┐     ┌─────────┐     ┌─────────┐
        │ Scholar  │     │   Web   │     │  Smart  │
        └─────────┘     └─────────┘     └─────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                    ┌─────────────────┐
                    │  Tavily Search  │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  AIsa Explain   │
                    │ (Meta-Analysis) │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Confidence Score│
                    │  + Synthesis    │
                    └─────────────────┘
```

## Pricing

| API | Approximate Cost |
|-----|-----------------|
| Web search | ~$0.001 |
| Scholar search | ~$0.002 |
| Smart search | ~$0.002 |
| Tavily search | ~$0.002 |
| Explain | ~$0.003 |
| Perplexity Sonar | ~$0.005 |


## Resources

- [AIsa](https://aisa.one) — Get your API key
- [AIsa API Reference](https://aisa.one/docs/api-reference) — Complete endpoint documentation
- [ClawHub](https://clawhub.ai) — Plugin marketplace

## License

MIT
