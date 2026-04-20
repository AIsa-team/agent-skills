# perplexity-search

Perplexity Sonar search and answer generation through AIsa. Use when the task is specifically to call Perplexity Sonar, Sonar Pro, Sonar Reasoning Pro, or Sonar Deep Research for citation-backed web answers, analytical reasoning, or long-form research reports.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: **Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**,
**Gemini CLI**, **OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and
others that implement the
[Agent Skills specification](https://agentskills.io/specification).

Requires Python 3, a POSIX shell, and `AISA_API_KEY`.

See [SKILL.md](SKILL.md) for the full agent-facing instructions.

## API Reference

This skill calls four Perplexity Sonar endpoints through AIsa:

- [Sonar](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar) — fast lightweight answers with citations
- [Sonar Pro](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar-pro) — stronger synthesis and comparison
- [Sonar Reasoning Pro](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar-reasoning-pro) — analytical multi-step reasoning
- [Sonar Deep Research](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar-deep-research) — exhaustive long-form reports

Full catalog: [aisa.one/docs/api-reference](https://aisa.one/docs/api-reference).
