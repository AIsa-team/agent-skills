---
name: multi-source-search
description: 'Confidence-scored multi-source retrieval across web, scholar, Tavily, and Perplexity-backed research. Use when: the user needs cross-source verification, consensus checks, or one report that compares multiple search surfaces. Supports parallel retrieval, confidence scoring, and synthesis-ready outputs.'
version: 1.0.1
license: MIT
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: 🔎
    requires:
      bins:
      - curl
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# Multi-Source Search Verification Engine

Compare multiple search surfaces in one pass and score how confident the result set looks before you synthesize it.

## When to use

- The user wants the same topic checked across multiple search surfaces instead of one provider.
- The user needs confidence scoring, cross-source verification, or a consensus-style research output.
- The user wants a growth-variant search lane focused on validation, not just lookup.

## When NOT to use

- The user only needs one flagship search entry for lookup, cited answers, or deep research; use `search`.
- The task is provider-specific and fits `scholar-search`, `tavily-search`, or `perplexity-search`.
- The workflow must avoid relay-based calls to `api.aisa.one`.

## Capabilities

- Parallel retrieval across structured web, scholar, smart search, Tavily, and Perplexity-backed flows.
- Confidence scoring that highlights source coverage, diversity, and result quality.
- Synthesis-ready outputs for research comparison, verification, and decision support.

One API key gives you:
- Structured web search
- Scholar search
- Hybrid scholar search
- Tavily search and extraction tools
- Perplexity Sonar answer-generation endpoints with citations

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness, including:

- **Claude Code** and **Claude** (Anthropic)
- **OpenAI Codex**
- **Cursor**
- **Gemini CLI** (Google)
- **OpenCode**, **Goose**, **OpenClaw**, **Hermes**
- and any other harness that implements the [Agent Skills
  specification](https://agentskills.io/specification)

Requires Python 3, a POSIX shell, and `AISA_API_KEY` (get one at
[aisa.one](https://aisa.one)).

## What This Skill Is Best For

### Fast web lookup
```text
Search the latest AI infrastructure launches and summarize the top sources.
```

### Scholar-backed research
```text
Find recent papers on multimodal reasoning from 2024 onward.
```

### Citation-rich answers
```text
Use Sonar Pro to answer which open-source agent frameworks are gaining traction and cite sources.
```

### Deep research reports
```text
Use Sonar Deep Research to produce a thorough market map of AI browser agents.
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## Example Requests

- Compare how three search surfaces describe the latest browser-use agent products.
- Verify whether a market claim shows up in web search, scholar search, and cited answer results.
- Run a confidence-scored research pass on multi-agent IDEs before writing a recommendation.

## Search APIs

### Web Search

```bash
curl -X POST "https://api.aisa.one/apis/v1/scholar/search/web?query=AI+frameworks&max_num_results=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Scholar Search

```bash
curl -X POST "https://api.aisa.one/apis/v1/scholar/search/scholar?query=transformer+models&max_num_results=10" \
  -H "Authorization: Bearer $AISA_API_KEY"

curl -X POST "https://api.aisa.one/apis/v1/scholar/search/scholar?query=LLM&max_num_results=10&as_ylo=2024&as_yhi=2025" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Hybrid Scholar Search

```bash
curl -X POST "https://api.aisa.one/apis/v1/scholar/search/smart?query=machine+learning+optimization&max_num_results=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

## Perplexity Sonar APIs

The deprecated `/search/full` and `/search/smart` nodes have been removed from this skill.

The replacement flow is the Perplexity API family:

| Endpoint | Use case |
|----------|----------|
| `/perplexity/sonar` | Lightweight, cost-effective search answers with citations |
| `/perplexity/sonar-pro` | Better for complex queries and multi-step follow-ups |
| `/perplexity/sonar-reasoning-pro` | Stronger analytical reasoning with web search |
| `/perplexity/sonar-deep-research` | Exhaustive research and long-form reports |

These descriptions are based on the AIsa docs:
- [Sonar](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar)
- [Sonar Pro](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar-pro)
- [Sonar Reasoning Pro](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar-reasoning-pro)
- [Sonar Deep Research](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar-deep-research)

### Sonar

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar",
    "messages": [
      {"role": "user", "content": "What changed in the AI agent ecosystem this week?"}
    ]
  }'
```

### Sonar Pro

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar-pro" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-pro",
    "messages": [
      {"role": "user", "content": "Compare the top browser-use agent frameworks and cite the key differences."}
    ]
  }'
```

### Sonar Reasoning Pro

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar-reasoning-pro" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-reasoning-pro",
    "messages": [
      {"role": "user", "content": "Analyze whether small vertical AI agents can defend against general-purpose copilots."}
    ]
  }'
```

### Sonar Deep Research

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar-deep-research" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-deep-research",
    "messages": [
      {"role": "user", "content": "Create a deep research report on AI coding agents in 2026, including product categories, pricing, and risks."}
    ]
  }'
```

## Tavily APIs

```bash
curl -X POST "https://api.aisa.one/apis/v1/tavily/search" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"latest AI developments"}'

curl -X POST "https://api.aisa.one/apis/v1/tavily/extract" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://example.com/article"]}'

curl -X POST "https://api.aisa.one/apis/v1/tavily/crawl" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","max_depth":2}'

curl -X POST "https://api.aisa.one/apis/v1/tavily/map" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

## Python Client

```bash
# Structured search
python3 scripts/search_client.py web --query "latest AI news" --count 10
python3 scripts/search_client.py scholar --query "transformer architecture" --count 10
python3 scripts/search_client.py smart --query "autonomous agents" --count 10

# Perplexity Sonar family
python3 scripts/search_client.py sonar --query "Summarize this week's AI launches"
python3 scripts/search_client.py sonar-pro --query "Compare AI agent frameworks with citations"
python3 scripts/search_client.py sonar-reasoning-pro --query "Analyze the defensibility of AI copilots"
python3 scripts/search_client.py sonar-deep-research --query "Write a deep research report on AI browser agents"

# Optional system instruction
python3 scripts/search_client.py sonar-pro \
  --query "Map the top coding agent products" \
  --system "Respond in markdown with a short executive summary first."

# Tavily utilities
python3 scripts/search_client.py tavily-search --query "AI developments"
python3 scripts/search_client.py tavily-extract --urls "https://example.com/article"

# Multi-source retrieval
python3 scripts/search_client.py verity --query "Is quantum computing ready for enterprise?"
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scholar/search/web` | POST | Web search with structured results |
| `/scholar/search/scholar` | POST | Academic paper search |
| `/scholar/search/smart` | POST | Hybrid scholar search |
| `/scholar/explain` | POST | Generate result explanations |
| `/perplexity/sonar` | POST | Lightweight search answers with citations |
| `/perplexity/sonar-pro` | POST | Advanced search answers for complex tasks |
| `/perplexity/sonar-reasoning-pro` | POST | Analytical reasoning with web search |
| `/perplexity/sonar-deep-research` | POST | Exhaustive research reports |
| `/tavily/search` | POST | Tavily search integration |
| `/tavily/extract` | POST | Extract content from URLs |
| `/tavily/crawl` | POST | Crawl web pages |
| `/tavily/map` | POST | Generate site maps |

## Parameters

### Scholar search query parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Search query |
| `max_num_results` | integer | Max results (default 10) |
| `as_ylo` | integer | Year lower bound |
| `as_yhi` | integer | Year upper bound |

### Perplexity request body

This skill sends a minimal OpenAI-style payload:

```json
{
  "model": "sonar-pro",
  "messages": [
    {"role": "system", "content": "Optional system instruction"},
    {"role": "user", "content": "Your question"}
  ]
}
```

Use `messages` because the AIsa Perplexity endpoints are presented as "Ask AI" endpoints in the official docs. This skill keeps the payload intentionally small for broad compatibility.

## Notes

- `/search/full` and `/search/smart` are no longer documented here because you indicated those nodes have been retired.
- The existing scholar and Tavily endpoints remain available.
- `verity` still focuses on parallel retrieval from scholar, web, hybrid scholar, and Tavily sources.

## Full API Reference

See [API Reference](https://aisa.one/docs/api-reference/) for complete endpoint documentation.

## Resources

- [AIsa Verity](https://github.com/AIsa-team/verity) - Reference implementation of confidence-scored search agent
- [AIsa Documentation](https://aisa.one/docs) - Complete API documentation
