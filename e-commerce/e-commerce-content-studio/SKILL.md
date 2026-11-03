---
name: e-commerce-content-studio
description: "Create platform-specific product images, localized listing copy and product videos with AIsa. Use for 商品图、商品文案 and listing content for Amazon US, TikTok Shop US or Shopify product pages. Requires real product photos, current platform research and a user-approved creative playbook; offers suitable models from the live AIsa catalog."
license: MIT
compatibility: "Requires Node.js 22+, ffmpeg, ffprobe and a host agent with research and visual inspection tools. New projects use host-managed AIsa MCP; browser OAuth needs no API key. Headless MCP can use a host-configured key. Hosts without MCP may use the official AIsa CLI. Explicit direct-API compatibility requires an existing AISA_API_KEY and the shared HTTP fallback gate. Compiled JavaScript requires the shipped Ajv validation dependencies; install with npm ci --omit=dev."
metadata:
  version: "1.1.0"
---

# E-commerce Content Studio

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

Turn real product references into a researched, user-approved content package. The host handles AIsa discovery and native calls, research, creative decisions and visual inspection. The TypeScript runtime records approvals, prepares and validates request handoffs, tracks results and validates saved artifacts. A successful generation response is not a finished asset.

## Opening greeting — every invocation

Make this concise menu the first user-facing response on every new invocation, including invocations by another agent. Use the user's language and show it once, not before every follow-up:

> Welcome to E-commerce Content Studio. What would you like to work on?
>
> 1. Research platform requirements and propose a playbook
> 2. Create product images
> 3. Write localized listing copy
> 4. Create product videos
> 5. Prepare a complete content package
> 6. Resume a project, review outputs or export
>
> Platforms: **Amazon US · TikTok Shop US · Shopify**.
> We can compare available AIsa models for your task. New projects need real product photos; production starts after you approve the playbook.

If the request already identifies an option, acknowledge it and proceed; do not make the user choose again. Ask only for missing photos, scope or existing project location. The menu and connection/model explanations do not require photos; product research and production do. A menu selection does not approve a playbook.

## Scope and connection

| Platform / market | Supported placements |
| --- | --- |
| Amazon US | `amazon-main`, `amazon-gallery`, `amazon-copy`, `amazon-video` |
| TikTok Shop US | `tiktok-gallery`, `tiktok-copy`, `tiktok-video` for product listings |
| Shopify storefront | `shopify-gallery`, `shopify-copy`, `shopify-video`; require destination country, language and actual theme/layout |

These are planning and export profiles, not seller-account connections or publishing. Other platforms, paid ads, organic campaigns and marketplace feeds remain outside this release. See [platform scope and roadmap](references/platforms.md).

**Default to AIsa MCP at `https://mcp.aisa.one/mcp`**, following the shared connection rules above. Let the host manage browser OAuth; do not ask MCP users for an API key. Headless MCP may use a key configured in the host. Verify the actual connection with the free account call before native research or production. When the host has no MCP, use the official AIsa CLI and record that transport. Do not present a transport-choice questionnaire on every invocation.

The native runtime is a host-mediated handoff, not an OAuth client: it never extracts tokens or calls a hidden REST fallback. Its connection, schema, quote and result receipts come from the actual selected MCP/CLI interface. Direct API adapters remain an explicitly selected developer compatibility path only when the shared HTTP fallback gate applies. Keep the selected transport stable throughout a project. Existing REST projects remain readable and recoverable; do not migrate or resubmit them automatically. See [native workflow](references/native-workflow.md) and [compatibility contracts](references/aisa-contract.md).

## 1. Require product photos

**Stop before research or production unless every requested SKU has at least one usable user-supplied photo of the real product. This includes copy-only jobs.** Descriptions, competitor images, generated concepts, inaccessible URLs and placeholders do not qualify. Request the missing photos and wait; do not omit a SKU silently.

Open and inspect the photos, then record paths, hashes, SKU/variant mapping and what each view proves. Request another view if a required angle or detail cannot be established. Photos alone do not prove materials, dimensions, performance, certifications or included accessories.

Capture platform, market, product category, placement, language, audience, deliverables and budget. Obtain specifications, units, variant counts, included items, substantiated claims and brand assets. Shopify requires `themeUrl` or `themeDescription`. Use the [brief template](assets/brief.example.json), replacing illustrative values; unknown facts remain unknown.

## 2. Research and discover suitable models

Recheck applicable current official platform sources during each run. Record **platform × market × category × placement**, URL, retrieval/effective dates, mandatory rule versus recommendation and unresolved conflicts. A material unresolved requirement blocks that placement. Read [references/platforms.md](references/platforms.md).

Use AIsa discovery with the full goal, then obtain complete schemas and quote the exact calls under the shared spending rules. Use another research method only within the user's authorized scope and disclose it. The bundled [research schema snapshot](references/research-contracts.json) is historical discovery evidence, not current execution access.

Inspect comparable creatives in the same category, audience, market and placement. Cite actual listings/creatives and observation dates. Separate measured outcomes, platform-selected examples and public proxies: rank, reviews, views and search position do not prove that a creative caused sales. Label examples without conversion evidence as references with observable signals.

**Offer the full live AIsa catalog, without a skill-maintained model allowlist.** For a suggested or user-selected model, verify the current operation, model-specific options, reference formats/counts, dimensions/duration, output format and price. Explain differences that affect the user's goal. A model's presence in a catalog does not establish its fitness for every task. Product images and videos require supported conditioning on the approved product references; a text-only model cannot silently replace that input. Use a model-specific request template grounded in the discovered contract, rather than copying one model's parameters to another. If an input format or response cannot be represented by the validated handoff, identify that concrete gap instead of claiming the model is unavailable in AIsa.

## 3. Present the report and approval gate

Read [references/creative-playbook.md](references/creative-playbook.md). Save the research report and versioned playbook with image sequence, copy structure, storyboards, claims, visual direction, platform rules, exact selected models/options, reference mapping, estimates/attempt allowances and QA criteria. Prices and estimates are not billing caps. Use the [research](assets/research.example.json) and [playbook](assets/playbook.example.json) templates.

**Stop and ask the user to confirm or modify that exact playbook before generating any product image, video or final listing copy.** Outlines and storyboards belong before this gate; generated previews and finished copy belong after it. Record explicit user approval against the playbook hash. An agent cannot approve on the user's behalf. Changes to products, references, claims, requirements, creative direction, selected model/options or deliverables require a revised playbook and renewed approval.

Disclose the verification and quality limits of the chosen operation/model. Do not claim a model passed live generation because its schema or an offline test passed. The retained REST Wan video adapter specifically remains experimental and requires `allowExperimentalVideo: true`; obtain approval of that disclosed limitation when using it.

## 4. Produce through the selected AIsa connection

Follow [references/native-workflow.md](references/native-workflow.md) for MCP/CLI production. Load complete discovered schemas, assemble the approved model-specific arguments with the real photo bytes or verified photo URLs, quote those exact arguments, prepare the bound handoff, mark dispatch before the host call and ingest its actual receipt. Do not paste truncated base64, stringify an argument object twice, invent operation names or reload schemas reflexively before every call. Refresh when incomplete, expired or contradicted by a contract error.

- **Original-photo export:** `local-photo-export` with `imageMode: "preserve"` fits/resizes the supplied photo without redrawing or cropping. It does not remove an existing background or create unseen angles. This remains the only mode for `amazon-main`; supply an already compliant source and inspect final framing.
- **Reference-conditioned images/video:** use the selected live model's supported operation and exact approved options. Never silently switch models, drop references or upload product photos elsewhere to satisfy a URL requirement.
- **Listing copy:** use a suitable discovered AIsa text operation with approved product facts and field limits. Photos are still required at intake, even if the text operation uses only the approved facts.
- **Direct-API compatibility:** use only the explicit REST path and its documented adapters under [references/aisa-contract.md](references/aisa-contract.md). Native capability failure alone does not authorize REST.

Keep every attempt within approved deliverables, estimates and allowances. A task ID means acceptance, not completion. Poll or recover the same task; do not resubmit to check status. An ambiguous paid dispatch can already have incurred a charge: reconcile its receipt/job before any retry. Authentication failures require recovery through the selected interface, not switching to another one. Missing cost metadata means unknown, not free.

Preserve product geometry, color, finish, branding, labels, quantity and variant. Reference conditioning does not guarantee fidelity. Reject invented accessories, unsupported motion/effects, distorted logos, false scale and mismatched SKUs. Localize copy from the approved claims ledger without fabricating testimonials, certifications, urgency or performance claims. The runtime does not assemble clips, add captions or compose deterministic typography; do not call one short clip a finished edit if the placement needs those steps.

## 5. Inspect, validate and deliver

Save media/copy and their generation receipts tied to the approved playbook. Validate dimensions, aspect, actual file format/size, duration, fields and text limits against the current recorded requirements. Inspect images, video frames and motion against original references; review complete copy, typography, claims, language and applicable disclosure requirements. Automated checks cannot establish truthful product appearance.

Record artifact hashes and actual pass/fail findings. Never approve unseen media or call unchecked output platform-ready. Repair within scope and budget, retain failure history and repeat affected checks. Deliver assets, report, approved playbook and provenance/validation manifest with unresolved limitations. Offer measurable test hypotheses without promising conversion lift. **Do not automatically publish listings or launch campaigns.**

## Runtime and references

TypeScript source and compiled JavaScript ship with Ajv schema validation. Run `npm ci --omit=dev` once in the installed skill directory. Node.js 22+, `ffmpeg` and `ffprobe` support decoding, technical QA and photo export. Run `node dist/cli.js --help` from the installed skill root; use absolute project/asset paths elsewhere. See [README.md](README.md) for commands, [native workflow](references/native-workflow.md) for receipt formats and [creative playbook](references/creative-playbook.md) for approval/QA. A completed command does not replace host research, user approval or visual inspection.

MIT distribution license: [LICENSE](../LICENSE).
