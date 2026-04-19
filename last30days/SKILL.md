---
name: last30days
description: "Research the last 30 days across Reddit, X/Twitter, YouTube, TikTok, Instagram, Hacker News, Polymarket, and grounded web search. Use when: you need recent social research, launch reactions, company updates, competitor comparisons, or trend scans. Supports AISA-hosted planning, reranking, synthesis, and JSON output in a stateless publish bundle."
metadata:
  aisa:
    emoji: "📰"
    requires:
      env:
        - AISA_API_KEY
      bins:
        - bash
        - python3
    primaryEnv: AISA_API_KEY
    compatibility:
      - openclaw
      - claude-code
      - hermes
---

# last30days

Research recent evidence across social platforms, community forums, prediction markets, and grounded web results, then synthesize it into one brief.

## When to use

- Use when you need a last-30-days research brief on a person, company, product, market, tool, or trend.
- Use when you want a recent competitor comparison, launch reaction summary, creator/community sentiment scan, or shipping update.
- Use when you want structured JSON with `query_plan`, `ranked_candidates`, `clusters`, and `items_by_source`.

## When NOT to use

- Do not use for timeless encyclopedia questions with no recent evidence requirement.
- Do not use when you need only one official source and do not want social/community signals.

## Capabilities

- AISA-hosted planning, reranking, synthesis, grounded web search, X/Twitter search, YouTube search, and Polymarket search.
- Public Reddit and Hacker News retrieval with fail-soft behavior.
- Hosted discovery for TikTok, Instagram, Threads, and Pinterest when enabled in runtime config.
- Structured report fields including `provider_runtime`, `query_plan`, `ranked_candidates`, `clusters`, and `items_by_source`.
- Stateless publish bundle: no SQLite accumulation layer, watchlist scheduler, or briefing archiver.

## Setup

- `AISA_API_KEY` is required for the hosted search and synthesis path.
- This publish bundle intentionally excludes local persistence, watchlist automation, and briefing generation. Those remain in the mother repo.

## Quick Reference

```bash
bash {baseDir}/scripts/run-last30days.sh "$ARGUMENTS"
python3 {baseDir}/scripts/last30days.py "$ARGUMENTS" --emit=json
python3 {baseDir}/scripts/last30days.py "$ARGUMENTS" --quick
python3 {baseDir}/scripts/last30days.py "$ARGUMENTS" --deep
python3 {baseDir}/scripts/last30days.py "$ARGUMENTS" --search=reddit,x,grounding
python3 {baseDir}/scripts/last30days.py --diagnose
```

## Inputs And Outputs

- Input: a topic or comparison query such as `OpenAI Agents SDK`, `OpenClaw vs Codex`, or `Peter Steinberger`.
- Output: synthesized research plus `provider_runtime`, `query_plan`, `ranked_candidates`, `clusters`, and `items_by_source`.

## Example Queries

- `last30days OpenAI Agents SDK`
- `last30days Peter Steinberger`
- `last30days OpenClaw vs Codex`
- `last30days Kanye West --quick`

