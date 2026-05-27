---
name: seo-keyword-research
description: Use this skill when a user asks for SEO keyword research, keyword discovery, search volume analysis, keyword difficulty, search intent mapping, topic clusters, content opportunities, competitor keyword gaps, or a keyword strategy for a domain, URL, product, market, or seed topic. When a website is provided, crawl and interpret the site first, then use AIsa API access to DataForSEO keyword, SERP, trend, Labs, and OnPage endpoints plus AIsa LLM reasoning to find non-brand keyword opportunities.
license: MIT
compatibility: "Works with any agentskills.io-compatible harness, including Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3, curl, and AISA_API_KEY."
metadata:
  short-description: AIsa-powered SEO keyword research
  aisa:
    homepage: https://aisa.one
    requires:
      bins:
        - python3
        - curl
      env:
        - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    harnesses:
      - claude-code
      - claude
      - opencode
      - cursor
      - codex
      - gemini-cli
      - openclaw
      - hermes
      - goose
---

# SEO Keyword Research

This skill builds a practical SEO keyword strategy from a domain, URL, seed topic, product, market, or competitor set. When the user provides a website, start by crawling and interpreting that website. Use the crawl to understand the product, audience, features, use cases, and business direction before querying keyword data. Then combine structured DataForSEO data through AIsa with AIsa LLM reasoning for clustering, search-intent interpretation, opportunity scoring, SERP-based page recommendations, and content planning.

## Requirements

This skill requires an AIsa API key.

```bash
export AISA_API_KEY="your-aisa-api-key"
```

Use these AIsa endpoints:

- Data APIs: `https://api.aisa.one/apis/v1/...`
- LLM gateway: `https://api.aisa.one/v1/chat/completions`

Never print or commit API keys. If the key is missing, ask the user to set `AISA_API_KEY`.

## Compatibility

Works with any agentskills.io-compatible harness, including Claude Code, Claude, OpenAI Codex, Cursor, Gemini CLI, OpenCode, Goose, OpenClaw, Hermes, and other agent runtimes that support skill folders.

Requires Python 3, curl, and `AISA_API_KEY`. Get an API key at `https://aisa.one`.

## Quick Start

```bash
export AISA_API_KEY="your-aisa-api-key"

python3 {baseDir}/scripts/site_crawler.py \
  https://example.com \
  --max-pages 12 \
  --out site-profile.json

python3 {baseDir}/scripts/aisa_client.py data \
  /apis/v1/dataforseo/dataforseo_labs/google/keyword_suggestions/live \
  payload.json \
  --out keyword-suggestions.json
```

Use the crawl output to generate seed topics first. Then use AIsa DataForSEO endpoints to validate search demand, difficulty, intent, and SERP reality. Finally use the AIsa LLM gateway to cluster, score, and summarize the verified keyword data.

## When to Use

Use this skill for requests like:

- "Find SEO keywords for this site."
- "Build a keyword strategy for my SaaS."
- "Research keywords for this product category."
- "Find keyword gaps between us and competitors."
- "Cluster these keywords by search intent."
- "Pick the best SEO content topics for next month."
- "Create a keyword map for these landing pages."

Do not use this skill for full technical audits, backlink audits, schema implementation, or content writing unless the user specifically asks for keyword research as part of that workflow.

## Core Workflow

### 1. Define the research scope

Collect or infer:

- Target domain or URL
- Seed topics, products, services, or categories
- Target country, language, and search engine
- Competitors, if provided
- Business goal: traffic, leads, sales, awareness, local visibility, or content planning
- Constraints: brand terms only, non-brand terms only, blog topics, landing pages, commercial pages, or programmatic pages

If country and language are missing, default to the user's market when obvious. Otherwise use United States and English, and note the assumption.

### 2. Crawl the website before keyword research

When the user provides a domain or URL, crawl the site before querying keyword tools.

```bash
python3 {baseDir}/scripts/site_crawler.py \
  https://example.com \
  --max-pages 12 \
  --out site-profile.json
```

Prioritize:

- Homepage
- Product, feature, pricing, docs, integrations, use case, comparison, blog, and about pages
- Sitemap URLs when available
- Navigation labels and internal links
- Page titles, meta descriptions, headings, schema hints, and visible copy

Use the crawl to produce a short business profile:

- Product category
- Main features and capabilities
- Target audience and buyer roles
- Use cases and jobs to be done
- Integrations, platforms, APIs, or supported tools
- Pricing model or conversion goal, if visible
- Competitors, alternatives, and category language mentioned on the site
- Existing content themes and gaps

Do not start with brand or domain keywords unless the user explicitly asks for brand SEO. Keep brand keywords in a separate "brand validation" section only after the product and category opportunities are mapped.

If the local crawl is blocked, shallow, or heavily JavaScript-rendered, use AIsa/DataForSEO OnPage helpers as fallback evidence:

- `/apis/v1/dataforseo/on_page/content_parsing/live`
- `/apis/v1/dataforseo/on_page/task_post`
- `/apis/v1/dataforseo/on_page/pages`
- `/apis/v1/dataforseo/on_page/raw_html`
- `/apis/v1/dataforseo/on_page/summary/{id}`

### 3. Convert the site profile into seed topics

Use AIsa LLM reasoning to turn the crawl into seed topics. These are hypotheses, not final keywords.

Generate seed topics from:

- Product category terms
- Feature and capability terms
- Use case terms
- Integration and platform terms
- Pain points and problem terms
- Competitor and alternative terms
- Buyer role terms
- Transactional modifiers: pricing, alternative, best, tool, API, software, platform, comparison
- Informational modifiers: what is, how to, guide, examples, tutorial, checklist

Require the LLM to explain why each seed topic matches the crawled site. Remove seeds that cannot be justified from the crawl.

### 4. Build the initial keyword universe

Use AIsa DataForSEO endpoints in this order when inputs are available:

1. Crawl-derived seed expansion:
   - `/apis/v1/dataforseo/dataforseo_labs/google/keyword_suggestions/live`
   - `/apis/v1/dataforseo/dataforseo_labs/google/keyword_ideas/live`
   - `/apis/v1/dataforseo/dataforseo_labs/google/related_keywords/live`
   - `/apis/v1/dataforseo/keywords_data/google_ads/keywords_for_keywords/live`
2. Site-derived validation, after seed expansion:
   - `/apis/v1/dataforseo/dataforseo_labs/google/keywords_for_site/live`
   - `/apis/v1/dataforseo/keywords_data/google_ads/keywords_for_site/live`
3. Demand and trend checks:
   - `/apis/v1/dataforseo/keywords_data/google_ads/search_volume/live`
   - `/apis/v1/dataforseo/keywords_data/clickstream_data/global_search_volume/live`
   - `/apis/v1/dataforseo/keywords_data/dataforseo_trends/explore/live`
4. Difficulty and intent:
   - `/apis/v1/dataforseo/dataforseo_labs/google/bulk_keyword_difficulty/live`
   - `/apis/v1/dataforseo/dataforseo_labs/google/search_intent/live`
   - `/apis/v1/dataforseo/dataforseo_labs/google/keyword_overview/live`

Keep source labels for each keyword: `site`, `seed`, `suggestion`, `related`, `competitor`, `trend`, `serp`, or `llm-generated`. Treat `llm-generated` keywords as hypotheses until validated by search volume or SERP data.

### 5. Expand through competitors and SERPs

When competitors are provided, or when DataForSEO returns SERP competitors:

- Use `/apis/v1/dataforseo/dataforseo_labs/google/competitors_domain/live`
- Use `/apis/v1/dataforseo/dataforseo_labs/google/domain_intersection/live`
- Use `/apis/v1/dataforseo/dataforseo_labs/google/ranked_keywords/live`
- Use `/apis/v1/dataforseo/dataforseo_labs/google/serp_competitors/live`
- Use `/apis/v1/dataforseo/dataforseo_labs/google/relevant_pages/live`

For the strongest candidate keywords, inspect live search results:

- `/apis/v1/dataforseo/serp/google/organic/live/advanced`
- `/apis/v1/dataforseo/serp/ai_summary`
- `/apis/v1/dataforseo/serp/screenshot`

Use SERP data to identify ranking page types, dominant content formats, user intent, SERP features, freshness patterns, weak results, and content gaps.

### 6. Normalize and clean the data

Before scoring:

- Lowercase only for deduplication; preserve original keyword casing in output.
- Merge close duplicates, singular/plural variants, and obvious spelling variants.
- Remove irrelevant brand, adult, navigational, and off-market terms unless requested.
- Mark keywords with missing volume, difficulty, or intent as incomplete rather than guessing numbers.
- Keep localized variants separate when intent differs by geography.

### 7. Cluster by intent and topic

Use AIsa LLM reasoning to cluster validated keywords. Prefer compact structured output.

Suggested cluster dimensions:

- Parent topic
- Subtopic
- Search intent: informational, commercial, transactional, navigational, local, comparison, or troubleshooting
- Funnel stage: awareness, consideration, conversion, retention
- Best page type: blog post, comparison page, landing page, product page, category page, tool page, glossary page, local page, or programmatic template

Do not let the LLM invent metrics. It may classify, summarize, and prioritize, but metrics must come from AIsa/DataForSEO data or be marked as qualitative.

Each final keyword cluster must include five representative keywords with metrics when at least five validated keywords exist. If a cluster has fewer than five validated keywords, show every validated keyword and mark the cluster as needing more expansion.

### 8. Identify high-opportunity keywords

High-opportunity keywords must meet both thresholds:

- Keyword difficulty is lower than 40
- Search volume is greater than 1000

Do not loosen this threshold silently. If no keywords meet both thresholds, say so and provide a separate "near opportunities" section using the closest candidates.

For every high-opportunity keyword, explain:

- Why it fits the crawled site
- Which feature, use case, product category, or audience insight from the crawl supports it
- Why the metric profile is attractive
- What risk remains after reviewing the SERP

### 9. Score opportunities

Score each keyword or cluster from 0 to 25:

- Demand: search volume, trend, and market size
- Relevance: fit with the domain, product, ICP, or page
- Intent value: likelihood to drive qualified traffic
- Ranking feasibility: inverse of difficulty plus SERP weakness
- Strategic value: supports product positioning, topical authority, or conversion

Use a simple label:

- `High priority`: strong demand, clear fit, feasible SERP, valuable intent
- `Medium priority`: useful but constrained by difficulty, ambiguity, or lower demand
- `Low priority`: weak fit, weak demand, or poor feasibility
- `Validate first`: interesting idea with incomplete data

### 10. Generate SERP-based page recommendations

Inspect SERPs for high-opportunity keywords and the strongest representative keyword in each cluster. Recommend a page type based on observed ranking results:

- Landing page: SERP is dominated by product, software, API, platform, or tool pages.
- Feature page: SERP shows feature-specific vendor pages, docs, or tool capability pages.
- Comparison page: query includes `vs`, `alternative`, `competitor`, `best`, or SERP contains comparison lists and review pages.
- Blog article or guide: SERP is dominated by explainers, tutorials, how-to articles, or People Also Ask.
- Pricing page: query includes pricing, cost, cheap, free, plan, or SERP contains pricing pages.
- Documentation page: SERP contains API references, SDK docs, GitHub repos, or developer guides.
- Programmatic page: the pattern can be repeated across locations, integrations, categories, competitors, templates, or use cases.

For each recommendation, explain the SERP evidence and the suggested page angle.

### 11. Produce the final deliverable

Return a concise keyword research report with:

- Executive summary
- Research assumptions
- Crawled-site business profile
- Top keyword clusters
- Five representative keywords per cluster
- High-opportunity keywords where difficulty is lower than 40 and volume is greater than 1000
- Why those keywords are opportunities
- Priority keyword shortlist
- Best content opportunities
- SERP-based page recommendations
- Recommended next pages, updates, or programmatic templates
- Data gaps and validation notes

Use `references/report-template.md` when a full report is requested.

## AIsa LLM Usage

Use the AIsa LLM gateway for:

- Summarizing the crawled site into a product and business profile
- Generating justified seed topics from the crawl
- Classifying search intent
- Grouping keywords into clusters
- Summarizing SERP patterns
- Translating raw metrics into SEO decisions
- Drafting a keyword strategy report
- Turning keywords into page recommendations

Recommended request pattern:

```bash
curl -sS "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5-mini",
    "messages": [
      {
        "role": "system",
        "content": "You are an SEO strategist. Use only provided metrics as facts. Mark unverified ideas clearly."
      },
      {
        "role": "user",
        "content": "Cluster these keyword rows by topic, search intent, and best page type."
      }
    ]
  }'
```

## Helper Script

Use `scripts/aisa_client.py` for quick API calls:

```bash
python3 {baseDir}/scripts/site_crawler.py \
  https://example.com \
  --max-pages 12 \
  --out site-profile.json
```

```bash
python3 {baseDir}/scripts/aisa_client.py data \
  /apis/v1/dataforseo/dataforseo_labs/google/keyword_suggestions/live \
  payload.json \
  --out keyword-suggestions.json
```

```bash
python3 {baseDir}/scripts/aisa_client.py chat \
  --model gpt-5-mini \
  --system system-prompt.txt \
  --prompt cluster-prompt.txt \
  --out clusters.md
```

## Quality Rules

- When a website is provided, crawl the website before keyword research.
- Do not begin with brand keywords unless the user explicitly asks for brand SEO.
- Prefer the local crawler and live AIsa/DataForSEO data over manual browser scraping.
- Cite which endpoint groups were used.
- Separate facts from recommendations.
- Do not invent search volume, CPC, keyword difficulty, rank, or trend values.
- Use LLM output for interpretation, not as a substitute for keyword data.
- Every keyword cluster should show five representative keywords with available metrics.
- High-opportunity keywords must satisfy difficulty < 40 and search volume > 1000.
- SERP-based page recommendations must say whether the user should create a landing page, feature page, comparison page, pricing page, documentation page, programmatic page, or blog article, and why.
- Keep raw exports private if they contain customer domains, competitors, or internal strategy.
- Make the final answer actionable: the user should know which keywords to target, which page type to create, and why.

## References

- `references/aisa-api-map.md` for endpoint groups and usage notes.
- `references/report-template.md` for the final keyword research report structure.
