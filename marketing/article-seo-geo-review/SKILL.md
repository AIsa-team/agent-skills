---
name: article-seo-geo-review
description: Use this skill when a user wants an article, blog post, landing page draft, or published URL reviewed for SEO and GEO (generative engine optimization, AI search visibility, being cited by AI Overviews, Google AI Mode, ChatGPT, or Perplexity). It runs one pipeline through AIsa APIs — keyword metrics (DataForSEO + SEMrush), live Google SERP and AI Mode, top-ranking competitor pages, content-gap detection, deterministic on-page SEO and GEO checks, AI answer-engine citation checks, LLM rewrite suggestions — and returns a scored Markdown report plus JSON evidence. Trigger phrases include "review this article for SEO", "GEO audit", "will AI cite this", "content gap vs competitors", "SEO scorecard", "/review-article".
license: MIT
compatibility: "Works with any agentskills.io-compatible harness, including Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3.9+ and AISA_API_KEY. Paid API calls; shows a spend estimate first."
metadata:
  version: "1.0.1"
  short-description: AIsa-powered SEO + GEO article review
  aisa:
    homepage: https://aisa.one
    requires:
      bins:
        - python3
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

# Article SEO + GEO Review

<!-- aisa-rules:start -->
## AIsa agent rules (shared)

<!-- Generated from _shared/aisa-rules.md by scripts/sync_shared_rules.py. Do not edit this block in place. -->

These rules apply to every AIsa-backed skill and are copied from https://aisa.one/llms.txt, the single authoritative agent rule source. When this block and the rest of this skill disagree, follow this block.

### Connect (MCP first)

Pick the first option that applies. Run the command yourself; the user only approves the browser sign-in.

- **A. Your client supports remote MCP and can open a browser (default).** Add a remote MCP server named `AIsa` with URL `https://mcp.aisa.one/mcp` (Streamable HTTP), using your client's own command or config file. Auth: browser OAuth, no key needed. In a chat app (Claude, ChatGPT), the user adds it as a custom connector in settings. Adding the server does not always start sign-in. If no sign-in window opens, start it from the client's own MCP authentication entry (a menu, command, or connector button); if only the user can reach that entry, tell them where it is. Sign-in is the slow step, not the API. Before it starts, tell the user in one line that an AIsa sign-in window or card is about to open and to click **Allow** (one click if the browser is already signed in to AIsa). Do not call step 2 until the user says sign-in is done or the AIsa tools appear; calling it earlier only returns 401, so do not retry in a loop. If the client must restart to load the server, tell the user and wait. If you cannot add the connector yourself (sandbox, permission denied), give the user the server name and URL above and wait. Do not fall back to another method.
- **B. Your client supports remote MCP but has no browser (CI, SSH, container).** Same endpoint, with the header `Authorization: Bearer $AISA_API_KEY` set in your client's MCP config instead of browser sign-in. If `AISA_API_KEY` is not set, ask the user to create a key at https://console.aisa.one/api-keys and set it in the environment; never ask them to paste it into chat. Never print, log, or commit the key.
- **C. The client has no MCP support.** Use the CLI: `npm install -g @aisa-one/cli && aisa login` (Node.js 18+). Guide: https://aisa.one/docs/get-started/cli.md
- **D. Calling AIsa over HTTP from your own code.** LLMs, OpenAI-compatible: `https://api.aisa.one/v1` (Gemini GenerateContent: `https://api.aisa.one/v1beta`). Data APIs: `https://api.aisa.one/apis/v1`. Auth: `Authorization: Bearer $AISA_API_KEY`. Exact paths and schemas: https://aisa.one/docs/api-reference

Direct HTTP (D) is a gated fallback, not the default. Gate (https://aisa.one/docs/get-started/cli.md#direct-http-fallback): "CLI and MCP are both unavailable, HTTP requests are supported, and a valid existing AIsa API key is already available." The curl and script examples in this skill exist for that fallback; when a connection exists, run the same operation through MCP (`search` → `batch_get_schema` → `batch_quote` → `batch_use`) or the CLI (`aisa search` → `aisa schema` → `aisa quote` → `aisa call`). Take tool names and arguments from `search` or `batch_get_schema`. Never invent them.

### Verify (step 2)

Make one free authenticated call on the interface you connected:

- MCP (A, B): call `account` (no arguments). If it is not in the tool list, call `use` with `{"operation_id": "account"}` instead. Returns the key, balance, and usage.
- CLI (C): `aisa balance`. (`aisa whoami` is local only and does not count.)
- HTTP (D): `GET https://api.aisa.one/v1/models` with the Bearer header returns 200.

AIsa is connected only when this call succeeds. A tool list or a 401 response does not count.

### Spending (approval before paid calls)

- Free: docs, `GET /v1/models`, MCP `search`, `list_categories`, `batch_get_schema`, `batch_quote`, `account`, and CLI `aisa search`, `aisa schema`, `aisa quote`, `aisa balance`.
- Quote the exact calls before running them: MCP `batch_quote`, CLI `aisa quote --json`. Run only what you quoted; re-quote if the tools or arguments change. Neither `batch_use` nor `aisa call` takes a price cap.
- If the quote reports `auto_execute_eligible: true` (a small total), run it without asking, unless the user set a tighter limit or asked only for a quote.
- Otherwise, before the first such call, tell the user in one message what you plan to call, the quoted price, and a total budget for the task in USD. Wait for approval, then run calls within that budget without asking again. Ask again only if the task changes or the next call would exceed the remaining budget.
- For operations billed by rows or credits, also set the operation's own limit (for example `limit`) so the cost stays bounded.
- Do not retry a failed paid call without telling the user.
- Direct HTTP (D) follows the stricter rule at https://aisa.one/docs/get-started/cli.md#direct-http-fallback: read the endpoint's reference and published pricing first; state the exact endpoint and scope, formula or rate, and documented maximum USD exposure; then wait for a separate user message explicitly approving that scope and cap. Do not make paid calls to test availability. Docs, `/v1/models`, and capability or MCP discovery are allowed before approval.

### Cost accounting

The settled cost of a direct HTTP call is reported by the response header `X-AISA-Customer-Cost-Micros-USD` (integer micro-USD; 1 USD = 1,000,000 micro-USD), or by a successful native Tool result's `customer_cost_micros_usd`. Missing cost metadata means unknown, not free. Response bodies do not carry `usage.cost` or `usage.credits_remaining`; do not report those fields as the charge. Reference: https://aisa.one/docs/guides/pricing

### Errors

- `401`: not signed in or invalid key. Redo Connect option A (step 1A in llms.txt) or check the key.
- `402`: low balance, or the operation requires the Go-to-Market plan. The response says which and where to resolve it. Tell the user which one it is (top up the balance, or subscribe to the plan) with the link from the response; do not retry.
- `429`: rate limited. Wait and retry with backoff. Details: https://aisa.one/docs/api-reference/rate-limits
<!-- aisa-rules:end -->

Review one article — a local Markdown draft or a published URL — for classic search optimisation (SEO) and generative engine optimisation (GEO: being retrieved, quoted, and cited by AI Overviews, Google AI Mode, ChatGPT, and Perplexity). Every number comes from AIsa APIs; the LLM only interprets. Pipeline:

`Keyword → SERP → Competitor → Content gap → SEO audit → GEO audit → Rewrite suggestions → Scorecard`

Output: a Markdown scorecard (SEO 0-100, GEO 0-100, grade A-F, per-check evidence, prioritised rewrites, spend) and a JSON file with all raw evidence.

## Requirements

Set an AIsa API key:

```bash
export AISA_API_KEY="your-aisa-api-key"
```

The script also reads `AISA_API_KEY=...` from `~/.aisa/credentials`. Never print, log, or commit API keys. If the key is missing, ask the user to set `AISA_API_KEY`.

## Compatibility

Works with any agentskills.io-compatible harness, including Claude Code, Claude, OpenAI Codex, Cursor, Gemini CLI, OpenCode, Goose, OpenClaw, Hermes, and other runtimes that support skill folders.

Requires Python 3.9+ (standard library only) and `AISA_API_KEY`. Get a key at `https://aisa.one`.

## When to Use

Use this skill for requests like:

- "Review this article for SEO before we publish."
- "Will AI Overviews or ChatGPT cite this post? What do I change?"
- "Run a GEO audit on this URL."
- "Compare my draft with the pages ranking for this keyword and list the content gaps."
- "Give me an SEO + GEO scorecard and rewrite suggestions."

Do not use this skill for keyword research from scratch (use `seo-keyword-research`), full technical site audits, backlink audits, or writing the article itself.

## Quick Start

```bash
# 1. Free, offline: deterministic on-page checks + provisional score
python3 {baseDir}/scripts/review_article.py audit draft.md

# 2. Show the paid calls and the spend estimate, no calls made
python3 {baseDir}/scripts/review_article.py review draft.md --dry-run

# 3. After the user approves the estimate: full review
python3 {baseDir}/scripts/review_article.py review draft.md --yes \
  --out review.md --json-out review.json --cache-dir .review-cache

# Published article (adds domain authority and "does any AI engine cite you" checks)
python3 {baseDir}/scripts/review_article.py review https://example.com/blog/post --yes --out review.md
```

The same commands work with `python3 scripts/review_article.py ...` from the skill root.

## Spend approval protocol (required)

AIsa data endpoints are paid. Before any `review`, `keywords`, `serp`, `competitors`, or `geo` run:

1. Run `review <source> --dry-run` and show the user the call table and the **nominal** and **documented maximum** totals.
2. Wait for the user to approve that scope in their own words.
3. Re-run with `--yes`. Without `--yes` the script prints the plan and exits with code 2. `--max-usd` (default 1.00) refuses plans whose documented maximum exceeds it.

Typical spend for a default run is USD 0.10-0.30 (draft) or USD 0.15-0.35 (URL). The report's **Spend** section lists every call with the cost DataForSEO reported. `--cache-dir` stores raw responses so re-runs and re-renders are free.

## Core workflow

### 1. Load the article

- Markdown: frontmatter `title`, `description`, `slug`, `author`, `date`, `robots`, `schema` are read; headings, links, images, lists, statistics, FAQ and TL;DR blocks are extracted. CJK text is word-counted by character and readability is marked n/a.
- URL: `/apis/v1/dataforseo/on_page/content_parsing/live` returns the heading/paragraph structure; a direct fetch adds title, meta description, canonical, robots, JSON-LD types, image alt, author and dates.
- Pass `--site-domain example.com` for drafts so internal links and "is my domain cited" can be evaluated before publishing.

### 2. Keywords

- `--keyword` uses the user's target. Otherwise the AIsa LLM gateway proposes a primary keyword and up to five secondary keywords from the title, headings, and first 300 words (`--no-llm` falls back to a title n-gram heuristic).
- Metrics: DataForSEO `dataforseo_labs/google/keyword_overview/live` (volume, difficulty, intent, CPC) cross-checked with SEMrush `keyword-overview`. `--deep` adds `related_keywords` and SEMrush `question-keywords` (USD 0.36).

### 3. SERP

`serp/google/organic/live/advanced` (depth 10) gives the organic top 10, People-Also-Ask questions, featured snippet, related searches, and whether an AI Overview is shown. `serp/google/ai_mode/live/advanced` returns Google's AI Mode answer with the pages it cites.

### 4. Competitors

The top `--top` (default 5) organic pages are parsed with `on_page/content_parsing/live` (headings, word count) and rated with SEMrush `domain-overview` (rank, organic traffic). The script computes the median word count and the heading terms that recur across competitors but are missing from the article.

### 5. GEO: what AI engines answer and cite

Engines (`--engines`, comma-separated; defaults marked *):

| id | Source | Notes |
|---|---|---|
| `dfs_ai_mode`* | Google AI Mode via DataForSEO | answer + cited URLs |
| `oxy_google_search`* | Google AI Overview via Oxylabs `ai-search` | answer + publisher names |
| `dfs_chatgpt`* | ChatGPT with web search via DataForSEO `llm_responses` | answer + citations |
| `dfs_perplexity`* | Perplexity sonar via DataForSEO `llm_responses` | answer + citations |
| `dfs_llm_mentions`* | DataForSEO `llm_mentions/top_domains` (google + chat_gpt) | which domains AI answers cite most for the topic; ~USD 0.10 per platform |
| `dfs_gemini`, `dfs_claude` | Gemini / Claude with web search | opt-in |
| `oxy_google_ai_mode` | Google AI Mode via Oxylabs | opt-in |

Oxylabs realtime through AIsa only serves Google sources; ChatGPT / Perplexity / Gemini / Claude answers therefore come from DataForSEO. `--fast` skips the LLM-response engines and the executive summary. Engines run in parallel; a failed engine is a data gap, not a crash.

### 6. Deterministic SEO and GEO checks

Every check has an id, a dimension, a weight, pass / warn / fail / n/a, the evidence, and a fix. Thresholds live in `references/scoring.md`; the GEO rubric and its grounding in Google's AI-features guidance live in `references/geo-rubric.md`. Highlights:

- SEO: title 30-60 chars, meta 70-155, one H1, keyword in title / H1 / first 100 words / an H2 / slug, density 0.5-2.5%, word count ≥ 80% of competitor median, PAA coverage ≥ 50%, ≥ 2 external sources, image alt ≥ 90%, Flesch ≥ 50, author, date.
- GEO: direct answer in the first 60 words, a quotable "X is …" definition, TL;DR block, ≥ 2 question-form headings, headings matching PAA, FAQ, ≥ 3 sourced statistics, no uncited figures, first-hand data or experience, sections ≤ 300 words, descriptive headings, schema hint, fresh date, no `nosnippet` / `noindex`, and (URL mode) whether any engine already cites the page.
- `llms.txt` or "AI-specific" markup earns nothing: Google states it does not use them.

### 7. Rewrite suggestions and summary

The LLM receives the article outline, competitor outlines, PAA, engine answers and citations, and the failed checks, and returns up to 12 prioritised suggestions with example rewrites limited to facts already in the evidence. `--no-llm` substitutes the deterministic fixes. Model: `--model` or `AISA_REVIEW_MODEL` (default `gpt-5.4-mini`).

### 8. Scorecard

Dimension score = (pass weight + 0.5 × warn weight) / applicable weight × dimension max. `n/a` checks leave the denominator; a fully n/a dimension (for example *Current AI visibility* for an unpublished draft) is redistributed and noted. Overall = mean of SEO and GEO. Grade: A ≥ 85, B ≥ 70, C ≥ 55, D ≥ 40, else F.

## Commands

| Command | Purpose | Paid calls |
|---|---|---|
| `audit <src>` | On-page SEO + GEO checks and provisional score | none for files; 1 content_parsing for URLs |
| `parse <src>` | Dump the normalised article model | same as audit |
| `review <src>` | Full pipeline and report | yes, gated by `--dry-run` / `--yes` |
| `keywords <src>` | Keyword extraction + metrics | yes |
| `serp --keyword K` | Organic SERP + AI Mode | yes |
| `competitors --keyword K` | Parse and rate top pages | yes |
| `geo --keyword K [--url U]` | Query AI engines; `--url` checks citations | yes |
| `render --from review.json [--rescore]` | Re-render Markdown from saved JSON | none |

Shared flags: `--keyword`, `--site-domain`, `--location-code 2840`, `--language-code en`, `--database us`, `--geo-location "United States"`, `--top 5`, `--engines`, `--fast`, `--deep`, `--model`, `--no-llm`, `--cache-dir`, `--out`, `--json-out`. `review` adds `--dry-run`, `--yes`, `--max-usd`.

## Presenting results

- Lead with the grade and the two totals, then the top three suggestions.
- Quote check ids when explaining a score so the user can map fixes to evidence.
- Separate facts (metrics, citations, SERP) from recommendations (LLM output).
- Repeat the data-gap list; if an engine failed, say so rather than implying the page is not cited.
- For a draft, remind the user that the AI-visibility dimension can only be measured after publishing (or with `--site-domain`).

## Quality rules

- Never invent search volume, difficulty, rankings, or citations; if a stage failed, report the gap.
- Do not run paid stages before the user has seen the dry-run estimate and approved it.
- Do not credit `llms.txt`, keyword stuffing, "AI rewrites", or artificial brand mentions.
- Keep the primary keyword the user gave; propose alternatives separately if the data suggests a better one.
- Keep raw exports private when they contain unpublished drafts or client domains.

## References

- `references/aisa-api-map.md` — every endpoint used, request shape, envelope, price.
- `references/geo-rubric.md` — GEO checks and their rationale.
- `references/scoring.md` — dimensions, weights, thresholds.
- `references/report-template.md` — report sections for agents that narrate `--no-llm` output.
- `assets/sample-article.md` — deliberately imperfect demo draft.

## API Reference

This skill calls the following AIsa endpoints (bearer auth, base `https://api.aisa.one`):

- [Chat completions](https://aisa.one/docs/api-reference/chat/post_chat-completions) — keyword extraction, content gap, rewrite suggestions, summary
- [Oxylabs AI Search](https://aisa.one/docs/api-reference/search/post_oxylabs-ai-search) — Google AI Overview answers and sources
- DataForSEO `/apis/v1/dataforseo/...` — `dataforseo_labs/google/keyword_overview/live`, `related_keywords/live`, `serp/google/organic/live/advanced`, `serp/google/ai_mode/live/advanced`, `on_page/content_parsing/live`, `ai_optimization/llm_mentions/top_domains/live`, `ai_optimization/{chat_gpt,perplexity,gemini,claude}/llm_responses/live`, `backlinks/summary/live`
- SEMrush `/apis/v1/semrush/...` — `keyword-overview`, `domain-overview`, `backlinks-overview`, `url-organic-keywords`, `question-keywords`

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the category root.
