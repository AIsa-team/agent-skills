---
name: last30days
version: "1.0.4"
description: "Research the last 30 days across Reddit, X/Twitter, YouTube, TikTok, Instagram, Hacker News, Polymarket, GitHub, and web search. Use when: you need recent social research, company updates, person profiles, competitor comparisons, launch reactions, or trend scans. Supports AISA-powered planning, clustering, reranking, and JSON output."
argument-hint: "last30days OpenAI Agents SDK, last30days Peter Steinberger, last30days OpenClaw"
allowed-tools: Bash, Read, Write, AskUserQuestion, WebSearch
homepage: https://github.com/AIsa-team/agent-skills
repository: https://github.com/AIsa-team/agent-skills
author: mvanhorn
license: MIT
user-invocable: true
metadata:
  openclaw:
    emoji: "📰"
    requires:
      env:
        - AISA_API_KEY
      bins:
        - python3
        - bash
    primaryEnv: AISA_API_KEY
    files:
      - "scripts/*"
---

# last30days

Research recent evidence across social platforms, community forums, prediction markets, GitHub, and grounded web results, then merge everything into one brief.

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
- Official GitHub API search when `GH_TOKEN` or `GITHUB_TOKEN` is available.
- Hosted discovery for TikTok, Instagram, Threads, and Pinterest when enabled in runtime config.

## Setup

- `AISA_API_KEY` is the main hosted credential.
- `GH_TOKEN` or `GITHUB_TOKEN` is optional for GitHub search only.
- Python `3.12+` is required.

```bash
for py in /usr/local/python3.12/bin/python3.12 python3.14 python3.13 python3.12 python3; do
  command -v "$py" >/dev/null 2>&1 || continue
  "$py" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' || continue
  LAST30DAYS_PYTHON="$py"
  break
done
```

## Quick Reference

```bash
bash "${SKILL_ROOT}/scripts/run-last30days.sh" "$ARGUMENTS" --emit=compact
"${LAST30DAYS_PYTHON}" "${SKILL_ROOT}/scripts/last30days.py" "$ARGUMENTS" --emit=json
"${LAST30DAYS_PYTHON}" "${SKILL_ROOT}/scripts/last30days.py" "$ARGUMENTS" --quick
"${LAST30DAYS_PYTHON}" "${SKILL_ROOT}/scripts/last30days.py" "$ARGUMENTS" --deep
"${LAST30DAYS_PYTHON}" "${SKILL_ROOT}/scripts/last30days.py" "$ARGUMENTS" --search=reddit,x,grounding
"${LAST30DAYS_PYTHON}" "${SKILL_ROOT}/scripts/last30days.py" --diagnose
```

## Inputs And Outputs

- Input: a topic or comparison query such as `OpenAI Agents SDK`, `OpenClaw vs Codex`, or `Peter Steinberger`.
- Output: synthesized research plus `provider_runtime`, `query_plan`, `ranked_candidates`, `clusters`, and `items_by_source`.

## Example Queries

- `last30days OpenAI Agents SDK`
- `last30days Peter Steinberger`
- `last30days OpenClaw vs Codex`
- `last30days Kanye West --quick`

