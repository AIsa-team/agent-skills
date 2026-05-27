# SEO Keyword Research

**AIsa-powered SEO keyword research for autonomous agents.**

This skill crawls a website first, turns the observed product and content signals into seed topics, validates keyword opportunities with AIsa DataForSEO endpoints, inspects SERP patterns, and produces a practical keyword strategy with page recommendations.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI,
OpenClaw, Hermes, Goose, and others.

Requires Python 3, `curl`, and `AISA_API_KEY` (get one at
[aisa.one](https://aisa.one)).

## What Can You Do?

### Find keywords for a website

```text
"Find non-brand SEO keyword opportunities for this SaaS website."
```

### Build a keyword strategy

```text
"Create a keyword map with intent clusters and recommended page types."
```

### Research competitor gaps

```text
"Compare our site with these competitors and find keyword gaps."
```

### Validate page opportunities

```text
"Which high-opportunity keywords should become landing pages, comparison pages, or blog posts?"
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

### Crawl a site

```bash
python3 scripts/site_crawler.py \
  https://example.com \
  --max-pages 12 \
  --out site-profile.json
```

### Call an AIsa DataForSEO endpoint

```bash
python3 scripts/aisa_client.py data \
  /apis/v1/dataforseo/dataforseo_labs/google/keyword_suggestions/live \
  payload.json \
  --out keyword-suggestions.json
```

### Use the AIsa LLM gateway for clustering

```bash
python3 scripts/aisa_client.py chat \
  --model gpt-5-mini \
  --system system-prompt.txt \
  --prompt cluster-prompt.txt \
  --out clusters.md
```

## Inputs and Outputs

- **Input:** a domain, URL, seed topic, product, market, competitor set, country, language, or SEO research brief.
- **Output:** a keyword research report with assumptions, crawled-site profile, keyword clusters, representative metrics, high-opportunity terms, SERP-based page recommendations, and a prioritized roadmap.

## When to use / When NOT to use

**Use when:**
- You need SEO keyword research, search demand validation, keyword difficulty checks, topic clusters, competitor gaps, or a keyword map.
- You need page recommendations grounded in observed SERP patterns.
- You want to start from a real site crawl instead of generic keyword lists.

**Do NOT use when:**
- You need a full technical SEO audit, backlink audit, schema implementation, or content drafting without keyword research.
- You need guaranteed ranking predictions. This skill prioritizes opportunities from available metrics and SERP evidence.

## Requirements

- Python 3
- `curl`
- `AISA_API_KEY`

## API Reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for the
complete catalog of endpoints this skill can call.

## License

MIT -- see [LICENSE](../LICENSE) at the repo root.
