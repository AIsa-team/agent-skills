---
name: e-commerce-content-studio
description: "Prepare platform-specific e-commerce product images and listing copy with AIsa, plus experimental product-video generation. Use for 商品图、商品文案 and listing content for Amazon US, TikTok Shop US or Shopify product pages. Requires real user-supplied product photos, current platform research, an evidence-backed creative playbook and explicit user approval before production."
license: MIT
compatibility: "Requires Node.js 22+, ffmpeg, ffprobe and a host agent with research and visual inspection tools. Compiled JavaScript ships without npm runtime dependencies. Direct AIsa REST production requires network access and AISA_API_KEY; native MCP research can use its own OAuth connection. Profiles support content preparation and validation, not account integration or publishing."
metadata:
  version: "1.0.0"
---

# E-commerce Content Studio

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

Prefer AIsa's authorized native MCP connection and its OAuth flow for research; direct REST adapters include search/extract when needed and use `AISA_API_KEY`. Discover operation schemas, availability and prices before use. The captured [research contracts](references/research-contracts.json) are discovery evidence from 18 October 2026, not proof of current execution access or paid use. If a required operation is unavailable, report the gap; do not invent an endpoint. Use another research method only within the user's authorized scope and disclose it.

Inspect a focused set of comparable creatives in the same category, market, audience and placement. Cite the actual listing or creative and record its observation date. Separate measured business outcomes, platform-selected performance examples and public proxies. Sales rank, reviews, views and search position do not prove that a particular creative caused sales. When conversion evidence is unavailable, label examples as references with observable signals rather than proven winners.

## 3. Present the report and approval gate

Read [references/creative-playbook.md](references/creative-playbook.md). Save a source-backed research report and versioned playbook with the proposed image sequence, copy structure, storyboards, factual claims, visual direction, platform rules, production variants, cost estimates/attempt allowances and QA criteria. Estimates do not cap provider billing. Use the [research](assets/research.example.json) and [playbook](assets/playbook.example.json) templates, replacing placeholder facts, dates, models and prices. Explain which patterns are observations and which are creative hypotheses. Do not copy competitors' images, branding, wording or unsupported claims.

**Stop and ask the user to confirm or modify that exact playbook before generating any product image, video or final listing copy.** Research notes, positioning options and a storyboard belong before this gate; finished copy and generated previews belong after it. Record the user's explicit approval against the approved version/hash. An agent cannot approve on the user's behalf. Material changes to product references, facts, requirements, creative direction or deliverables require a revised playbook and renewed approval.

## 4. Produce through AIsa

Read [references/aisa-contract.md](references/aisa-contract.md) before production. The implemented modes are:

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
