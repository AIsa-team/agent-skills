# Changelog

## v1.0.0 (2026-03-30)

Initial release. Rewritten from the original `multi-search-engine` skill (v2.0.1) to use AIsa API as the unified backend.

### Added

- Seven agent tools registered via the OpenClaw plugin SDK:
  - `aisa_web_search` — Web search via AIsa Scholar Web endpoint
  - `aisa_scholar_search` — Academic paper search with year range filtering
  - `aisa_smart_search` — Intelligent hybrid search (web + academic)
  - `aisa_tavily_search` — Advanced Tavily search with depth, topic, time, and domain filters
  - `aisa_tavily_extract` — Content extraction from URLs
  - `aisa_perplexity_search` — Deep research via Perplexity Sonar models (sonar, sonar-pro, sonar-reasoning-pro, sonar-deep-research)
  - `aisa_multi_search` — Parallel multi-source search with deterministic confidence scoring and optional AI synthesis via AIsa Explain
- Python CLI client (`scripts/search_client.py`) with subcommands for all search modes
- Native OpenClaw plugin manifest (`openclaw.plugin.json`) with config schema, auth metadata, and UI hints
- Confidence scoring engine (source availability, result quality, source diversity, recency)

### Changed (from original multi-search-engine)

- Replaced 17 browser-based search engine URLs with AIsa API endpoints
- Moved from a skill (SKILL.md-only) to a native OpenClaw code plugin with `definePluginEntry`
- Added structured result formatting, error handling, and cost tracking
- Added Perplexity deep research capability (not available in original)
- Added confidence scoring and AI synthesis (not available in original)
