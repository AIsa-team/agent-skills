---
name: e-commerce-content-studio
description: "Prepare platform-specific e-commerce product images and listing copy with AIsa, plus experimental product-video generation. Use for 商品图、商品文案 and listing content for Amazon US, TikTok Shop US or Shopify product pages. Requires real user-supplied product photos, current platform research, an evidence-backed creative playbook and explicit user approval before production."
license: MIT
compatibility: "Requires Node.js 22+, ffmpeg, ffprobe and a host agent with research and visual inspection tools. Compiled JavaScript ships without npm runtime dependencies. Direct AIsa REST production requires network access and AISA_API_KEY; native MCP research can use its own OAuth connection. Profiles support content preparation and validation, not account integration or publishing."
metadata:
  version: "1.0.0"
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

Turn verified product references into a researched, user-approved content package. The host agent researches, makes creative decisions and inspects media; the TypeScript executable records workflow state, calls supported AIsa operations and validates production artifacts. A successful API response alone is not a finished asset.

## Opening greeting — every invocation

At the start of every new invocation, whether initiated by a user or another agent, make the following concise greeting and menu the **first user-facing response**, before research, setup checks or production. Use the user's language; show one language only. An invoking agent must surface this menu to the user before continuing. Show it once per invocation, not before every command or follow-up within the same invocation.

> Welcome to E-commerce Content Studio. What would you like to work on?
>
> 1. Research platform requirements and propose a playbook
> 2. Create product images
> 3. Write localized listing copy
> 4. Create product videos **(experimental)**
> 5. Prepare a complete content package
> 6. Resume a project, review outputs or export
>
> Platforms: **Amazon US · TikTok Shop US · Shopify**.
> New projects need real product photos; generation starts after you approve the playbook.

If the request already identifies an option, acknowledge that selection after the menu and proceed with the supplied information; do not make the user choose again. Otherwise ask for an option or a natural-language goal. For a new project, request only missing product photos and target-platform details, then follow the photo gate below. For an existing project, reuse its verified photos and approval state and ask only for a missing project location. Showing the menu or explaining platform support does not require photos; research and content production do. A menu selection never substitutes for playbook approval.

## Supported scope

| Platform / market | Supported placements |
| --- | --- |
| Amazon US | `amazon-main`, `amazon-gallery`, `amazon-copy`, `amazon-video` |
| TikTok Shop US | `tiktok-gallery`, `tiktok-copy`, `tiktok-video` for product listings |
| Shopify storefront | `shopify-gallery`, `shopify-copy`, `shopify-video` for product pages; require destination country, language and theme/layout context |

These are workflow profiles and export checks. They do not grant seller eligibility, connect account analytics or upload listings. TikTok paid ads, organic campaigns, Shopify marketplace feeds and other countries/platforms are outside version 1.0.0. Read [references/platforms.md](references/platforms.md) for source selection and the explicitly unsupported roadmap.

**Video generation is experimental.** Only the Wan 2.7 image-to-video adapter is implemented; its gateway translation and output quality have not been verified by authenticated end-to-end generation. A video deliverable must set `allowExperimentalVideo: true`, disclose this limitation in the rendered playbook and receive the user's approval. Platform video profiles do not establish reliable video production.

## 1. Require product photos

**Stop before research or generation unless every requested SKU has at least one usable user-supplied photo of the real product. This also applies to copy-only jobs.** A description, competitor image, AI concept, inaccessible URL or placeholder is not a substitute. Ask for the missing product photos and wait; do not silently omit a SKU.

Open the supplied files and verify they are decodable, sufficiently clear and depict the relevant variant. Record their local paths, hashes, SKU/variant mapping and what each view proves. Request more views if a required angle, label or feature cannot be established. Never infer hidden construction, materials, dimensions or included accessories from appearance alone.

Capture the platform, market, product category, placement, destination language, audience, deliverables and budget. Obtain product facts, dimensions/units, variant counts, included items, substantiated claims and brand assets. Shopify requires `themeUrl` or `themeDescription` for the actual theme/intended page layout and crops. Mark missing facts as unknown; product photos do not prove performance claims or certifications. Use [assets/brief.example.json](assets/brief.example.json) for the intake shape, replacing all illustrative values.

## 2. Research before proposing creative

Read [references/platforms.md](references/platforms.md). Recheck applicable official sources during each run; bundled profiles and source links are starting points, not a promise of current policy. Record **platform × market × category × placement**, source URL, retrieval date, effective date where available, mandatory rule versus recommendation and any unresolved conflict. A material unresolved requirement blocks that placement.

Prefer AIsa's authorized native MCP connection and its OAuth flow for research. Direct REST search/extract adapters require the shared rules' HTTP fallback gate and an existing `AISA_API_KEY`. Discover operation schemas, availability and prices before use. The captured [research contracts](references/research-contracts.json) are discovery evidence from 18 October 2026, not proof of current execution access or paid use. If a required operation is unavailable, report the gap; do not invent an endpoint. Use another research method only within the user's authorized scope and disclose it.

Inspect a focused set of comparable creatives in the same category, market, audience and placement. Cite the actual listing or creative and record its observation date. Separate measured business outcomes, platform-selected performance examples and public proxies. Sales rank, reviews, views and search position do not prove that a particular creative caused sales. When conversion evidence is unavailable, label examples as references with observable signals rather than proven winners.

## 3. Present the report and approval gate

Read [references/creative-playbook.md](references/creative-playbook.md). Save a source-backed research report and versioned playbook with the proposed image sequence, copy structure, storyboards, factual claims, visual direction, platform rules, production variants, cost estimates/attempt allowances and QA criteria. Estimates do not cap provider billing. Use the [research](assets/research.example.json) and [playbook](assets/playbook.example.json) templates, replacing placeholder facts, dates, models and prices. Explain which patterns are observations and which are creative hypotheses. Do not copy competitors' images, branding, wording or unsupported claims.

**Stop and ask the user to confirm or modify that exact playbook before generating any product image, video or final listing copy.** Research notes, positioning options and a storyboard belong before this gate; finished copy and generated previews belong after it. Record the user's explicit approval against the approved version/hash. An agent cannot approve on the user's behalf. Material changes to product references, facts, requirements, creative direction or deliverables require a revised playbook and renewed approval.

## 4. Produce through AIsa

Read [references/aisa-contract.md](references/aisa-contract.md) before production. The bundled production executable implements REST, not an MCP/CLI bridge. Use it only when the shared rules' direct-HTTP fallback gate and paid-call approval requirements are met; playbook approval alone does not establish that gate. With an available MCP/CLI connection, discover and quote the required native capability. If native generation is unavailable, report that limitation; do not claim this runtime can execute native operations or silently switch to REST. The implemented modes are:

- **`local-photo-export` / `imageMode: "preserve"`:** resize and fit the supplied photo on a white canvas without generative redrawing or cropping. It does not remove the existing background, isolate the product or create a new angle. This is the only mode allowed for `amazon-main` in 1.0.0; provide an already compliant product photo and check the final framing.
- **GPT Image reference editing / `imageMode: "edit"`:** send inline product photos through `/v1/images/edits` with an explicitly selected GPT Image 2 model whose current catalog advertises that route. This adapter requests one PNG at medium quality: `1K` square/3:2/2:3 or `2K` square. See the contract reference for exact dimensions and verification status; no automatic model fallback is allowed.
- **Gemini reference editing / `imageMode: "edit"`:** the `/v1beta/models/{model}:generateContent` adapter remains available, but the authenticated catalog check on **2026-10-21** found no compatible image model. Recheck before selecting it; an old example model cannot establish availability. Native generation size and final export dimensions are separate.
- **Listing copy:** a catalog-compatible chat model through `/v1/chat/completions`, using the approved product facts and field limits.
- **Experimental video:** only `wan2.7-i2v`, with `allowExperimentalVideo: true` and a user-supplied public HTTPS `remoteUrl` whose downloaded bytes match the inspected local photo. There is no upload endpoint or text-to-video fallback. Missing hosting stops video production; never silently upload the user's photo elsewhere.

Other image-edit adapters, masking/background removal, deterministic text composition, video assembly and captions are not implemented. Do not promise those deliverables through this runtime. A direct `gpt-image-2` adapter test on **2026-10-21** returned a decoded 1024×1024 PNG; it did not test the full CLI workflow, other models or sizes. Visual review found product-detail changes, so the test image was not listing-approved. These REST adapters do not establish native MCP generation capability in the WorkBuddy expert. Keep all production within approved deliverables and attempt/estimate allowances.

Async task acceptance is not completion: retain task IDs and use `resume` for a bounded status check or saved-output recovery. Use `retry` only after a confirmed failure or inspected rejection within the allowance. An ambiguous POST timeout may have incurred a charge; reconcile it before any resubmission. Inspect terminal errors and save completed media locally.

Preserve the real product's geometry, color, texture, branding, labels, quantity and variant. Prefer the original-photo export when exact identity matters and the source already suits the placement. A reference-conditioned generation can still alter the product; do not promise pixel preservation from prompting alone. Inspect all typography, dimensions and labels. Reject invented accessories, distorted logos, false scale, unsupported effects and mismatched SKUs.

Generate final copy only from the approved claims ledger and platform field requirements. Localize meaning, units and spelling for the selected destination. Avoid fabricated testimonials, certifications, superlatives, inventory urgency or feature claims. Video must show supported behavior and preserve identity across frames. If the placement needs a longer assembled video, captions or other unimplemented editing, mark that deliverable outside the current runtime instead of calling a short generated clip complete.

## 5. Inspect, validate and deliver

Save every final image, video and copy artifact, along with generation metadata and its association with the approved playbook. Run technical validation against the current requirement records: dimensions, aspect ratio, file type/size, duration, fields and relevant text limits. Inspect actual images and video frames against the original references; review all copy and on-image text. Check category constraints, language, product identity, audio and any required AI disclosure or metadata. Automated checks support this review; they cannot establish truthful product appearance by themselves.

Record inspected artifact hashes, findings and pass/fail decisions. Never mark unseen media as approved or describe unchecked outputs as platform-ready. Repair within the approved scope and budget, then repeat the affected checks. If an asset cannot pass, deliver the status and needed next step rather than quietly replacing it with a placeholder.

Deliver the local assets and copy, research report, approved playbook, provenance/validation manifest and unresolved limitations. Offer test hypotheses tied to a measurable objective; do not guarantee conversion lift. **Do not automatically publish listings or launch campaigns.**

## Runtime and references

The executable is implemented in TypeScript and ships with compiled JavaScript without npm runtime dependencies. Node.js 22+, `ffmpeg` and `ffprobe` are required for file decoding, technical inspection and photo exports. They do not provide a video-editing workflow in this package. Resolve paths relative to the installed skill root; use absolute job and asset paths when invoking it elsewhere. Host research, approval and visual inspection remain required even when a command completes successfully.

Run `node dist/cli.js --help` from the installed skill root. The workflow is `init` → `research-import` → `playbook-import` → `report` → explicit user confirmation → `approve` → `generate`/`resume` → `review` → `export`. Use `status` for project state and `retry` for an eligible failed/rejected attempt. Use `platforms` for scope and `models` for authenticated catalog discovery; neither verifies generation. See [README.md](README.md) for arguments and the [approval](assets/approval.example.json) and [review](assets/review.example.json) record shapes.

Consult the [AIsa API Reference](https://aisa.one/docs/api-reference) and [model catalog](https://aisa.one/docs/guides/models) for live capability discovery. Supported implementation details and command usage are documented in [README.md](README.md); do not treat a documentation listing as evidence of a successful authenticated generation.

MIT distribution license: [LICENSE](../LICENSE).
