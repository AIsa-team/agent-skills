---
name: perplexity-research
description: Deep research using Perplexity Sonar models via AIsa API. Provides synthesized answers with citations. Supports 4 models from fast to exhaustive deep research.
---

# AIsa Perplexity Deep Research

Conduct deep research using Perplexity Sonar models via the AIsa API. Returns synthesized, citation-backed answers instead of raw search results. Choose from four models depending on the depth and complexity needed.

## Setup

This skill requires the `AISA_API_KEY` environment variable. When installed as a Claude plugin, the key is configured via the plugin's `userConfig`.

## Usage

Run the search client with the `sonar` subcommand:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/perplexity-research/scripts/search_client.py sonar --query "<research question>" --model <model_name>
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--query` / `-q` | Yes | — | Research question or query |
| `--model` / `-m` | No | sonar | Model to use (see below) |

### Available Models

| Model | Speed | Depth | Best For |
|-------|-------|-------|----------|
| `sonar` | Fast | Standard | Quick factual lookups |
| `sonar-pro` | Medium | Detailed | In-depth topic exploration |
| `sonar-reasoning-pro` | Slower | Deep | Complex reasoning and analysis |
| `sonar-deep-research` | Slowest | Exhaustive | Comprehensive research reports |

### Examples

```bash
# Quick factual lookup
python3 ${CLAUDE_PLUGIN_ROOT}/skills/perplexity-research/scripts/search_client.py sonar --query "What is the current state of quantum computing?"

# Detailed research
python3 ${CLAUDE_PLUGIN_ROOT}/skills/perplexity-research/scripts/search_client.py sonar --query "Compare transformer and state-space model architectures" --model sonar-pro

# Complex reasoning
python3 ${CLAUDE_PLUGIN_ROOT}/skills/perplexity-research/scripts/search_client.py sonar --query "Will AGI be achieved by 2030? Analyze arguments for and against." --model sonar-reasoning-pro

# Exhaustive deep research
python3 ${CLAUDE_PLUGIN_ROOT}/skills/perplexity-research/scripts/search_client.py sonar --query "Comprehensive analysis of AI regulation frameworks worldwide" --model sonar-deep-research
```

## Output

The script prints:
- **Synthesized answer** — A coherent, well-structured response
- **Citations** — Source URLs backing the answer
- **Cost** — API usage cost (when available)

## When to Use

Use this skill when the user needs a synthesized, well-researched answer rather than raw search results. Best for complex questions, comparative analyses, trend reports, and any query where a thoughtful, citation-backed response is more valuable than a list of links.
