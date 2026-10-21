# Changelog

## 1.0.1

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.
- Fix the bundled search client against the published contract: Scholar search operations send query-string parameters instead of a JSON body, the hybrid search calls `/scholar/search/mixed`, the explain step calls `/scholar/search/explain` with `search_id`, and Perplexity models post to `/perplexity/sonar*`.
- Replace `CLAUDE_PLUGIN_ROOT`-based script paths (no documented install path sets that variable) with skill-root-relative `scripts/...` paths.

## 1.0.0

- Establish the independently versioned baseline and maintenance manifest.
- Preserve the existing skill contract and declare tracked upstream sources.
