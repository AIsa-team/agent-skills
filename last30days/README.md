# last30days

English ClawHub publish bundle for `last30days`.

Included:

- stateless runtime scripts for live research and synthesis
- `SKILL.md`
- license and package metadata

Excluded on purpose:

- tests and verification harnesses
- historical docs, hooks, fixtures, and other dev-only assets
- SQLite accumulation, watchlist automation, and briefing generation
- GitHub-specific retrieval paths that are not part of the AISA-first publish runtime

Runtime summary:

- `AISA_API_KEY` powers hosted planning, reranking, synthesis, X/Twitter, YouTube, Polymarket, and grounded web search.
- Reddit and Hacker News use public paths.
- This publish bundle is intentionally stateless: it keeps the `last30days.py` research CLI only.

