# E-commerce Content Studio

An AIsa-powered workflow for 商品图、商品文案 and experimental product videos. It starts with real product photos, researches current platform requirements and comparable creatives, proposes a playbook, then produces content after the user approves that playbook.

Version **1.0.0** supersedes the general-purpose Python `media-gen` workflow with a product-focused TypeScript implementation. The new name, inputs, runtime and approval flow are breaking changes; old Python commands are not the interface for this skill.

The skill includes a greeting at each new invocation, followed by six options: research/playbook, product images, localized copy, experimental video, a complete package, or resuming/reviewing/exporting an existing project. The menu uses the user's language and honors a choice already made in the request. Product-photo and playbook-approval requirements still apply.

## Supported in 1.0.0

| Platform | Market and scope |
| --- | --- |
| Amazon | US product main images, gallery images, listing copy and product videos |
| TikTok Shop | US product listing images, copy and product videos |
| Shopify | Storefront product pages, with an explicit destination country, language and theme/layout |

Support means workflow profiles and export validation. It does not mean native seller-account integrations, analytics access, automatic uploading or guaranteed platform acceptance. TikTok paid ads and organic campaigns, Shopify marketplace feeds and other marketplaces are excluded from this version.

**Video generation is experimental and has not been verified by authenticated end-to-end generation.** Only the Wan 2.7 image-to-video adapter is implemented. Its experimental status must appear in the playbook, and `allowExperimentalVideo: true` requires the user's approval of that playbook. A supported video profile does not establish a working, high-quality video result.

The proposed roadmap is **next: Etsy US and eBay US; following: Amazon UK/DE/JP and TikTok Shop UK; later: Shopee SG/MY, Lazada SG/MY and AliExpress US/EU**. These are planned, unsupported targets with no committed dates. Each needs current policy research, placement-specific validation, usable AIsa capabilities and verification before support can be claimed. See [platform scope and sources](references/platforms.md).

## Implemented production modes

- **Original-photo export:** fit/resize the supplied photograph on a white canvas without redrawing or cropping the product. It does not remove the original background. This is the only production mode for Amazon main images in 1.0.0; they need an already compliant source photo and reviewed final framing.
- **GPT Image product-image edits:** send inline product references to `/v1/images/edits` with an explicitly selected GPT Image 2 model advertised by the current catalog. Request one PNG at medium quality: `1K` square/3:2/2:3 or `2K` square. A direct `gpt-image-2` adapter test on **2026-10-21** returned a decoded 1024×1024 PNG. Other models/sizes and the full CLI workflow were not verified by that call. No automatic model fallback is allowed.
- **Gemini product-image edits:** the inline-reference adapter remains implemented, but the authenticated catalog check on **2026-10-21** found no compatible image model. Recheck current routes before choosing it; previous example model names are not evidence of availability.
- **Listing copy:** generate the approved fields from verified product facts through a compatible AIsa chat model.
- **Experimental Wan 2.7 video:** requires a user-supplied public HTTPS URL for the exact same photo inspected locally. There is no automatic photo upload or text-to-video fallback.

The runtime does not remove backgrounds, assemble videos, compose deterministic typography or add captions. It cannot guarantee product fidelity from a generation prompt. Live model availability and output quality must be verified during the actual authorized run; mocked checks and catalog discovery are separate from that verification. These REST adapters do not establish native MCP image generation in the WorkBuddy expert, which uses a separate host-mediated execution path.

The live test produced a usable image file but reinterpreted the tumbler's lid/rim, so it was **not approved for listing use**. Its 222×222 reference also fell below the full workflow's 256-pixel intake minimum; this was an authorized transport smoke test, not proof of a completed product-content workflow.

## What to provide

- At least one clear photo of the actual product for **every requested SKU**, including copy-only requests. More views may be needed for particular shots or claims.
- Target platform, market, category, placement and language.
- Verified specifications, dimensions, variants, included items, supported claims and brand assets.
- Intended audience, deliverables, creative preferences and production budget.

Without usable product photos, the workflow stops before research. Without approval of the proposed playbook, it stops before image/video generation and final copy. Competitor imagery and generated concepts cannot replace product references.

Example request:

> Use the attached photos and specification sheet to prepare Amazon US product content for SKU BOTTLE-01. Research current requirements and comparable listings, then propose the image sequence, copy approach and video storyboard for my approval. Preserve the actual bottle, logo and included parts.

## How the work is divided

The **host agent** conducts live research, inspects comparable creatives, writes the report/playbook, obtains user approval and visually reviews output against product references. The **TypeScript executable** provides workflow records, supported AIsa requests, artifact handling and deterministic validation. Running a command does not replace research or visual review.

The output package contains saved media and copy, the source-backed report, approved playbook, generation provenance and validation results. Public popularity signals are labeled as proxies; “top-performing” is reserved for evidence whose metric and limitations are recorded. A final package is prepared for user review and manual use; this skill does not publish it.

## Requirements

Node.js 22 or later, `ffmpeg`, `ffprobe`, and a host with web research and image/video inspection capabilities. The package includes TypeScript source and compiled JavaScript with no npm runtime dependencies. Media tools are needed for actual decoding, technical QA and photo exports; this package does not implement a video-editing workflow.

Use the authorized AIsa MCP/OAuth connection first. The bundled production executable implements REST and has no MCP/CLI bridge; it is available only under the shared rules' HTTP fallback gate, with an existing `AISA_API_KEY` and the required paid-call approval. Missing native generation capability must be reported, not treated as permission to switch transports. Live model availability, accepted reference formats, usage limits and prices must be checked before production.

Read [SKILL.md](SKILL.md) for the agent workflow and [the creative playbook reference](references/creative-playbook.md) for research, approval and QA records. Mocked or offline checks do not establish successful live AIsa generation; production success must be recorded from the actual run.

## Executable workflow

From the installed skill directory, run `node dist/cli.js --help`. Use absolute paths for project/input/output locations when invoking it elsewhere. The host prepares evidence and review records from work actually performed; importing a record does not perform that research or inspection.

| Command after `node dist/cli.js` | Purpose |
| --- | --- |
| `platforms` | Inspect the supported platform/placement profiles |
| `models` | Discover AIsa catalog routes using `AISA_API_KEY`; this does not verify generation |
| `init <brief.json> <project-dir>` | Validate product references and initialize a project |
| `research-import <project-dir> <research.json>` | Record current requirements and inspected comparable evidence |
| `playbook-import <project-dir> <playbook.json>` | Record the proposed production playbook |
| `report <project-dir>` | Prepare the report/playbook for user review |
| `approve <project-dir> <approval.json>` | Record the user's explicit approval of the exact playbook |
| `generate <project-dir> <deliverable-id>` | Produce an approved deliverable |
| `resume <project-dir> <deliverable-id>` | Make one status check or resume saved-output recovery |
| `retry <project-dir> <deliverable-id>` | Retry a confirmed failure or reviewed rejection within the approved allowance |
| `review <project-dir> <review.json>` | Record inspection findings for the actual saved artifacts |
| `status <project-dir>` | Show approval and production state |
| `export <project-dir> <new-destination>` | Export a fully reviewed package to a new destination |

Do not automate `approve` from an agent-authored recommendation or generate review passes without opening the artifacts. Run one stage at a time, inspect its result and resolve failures before continuing. No production command replaces the user's required playbook confirmation.

Start from the [brief](assets/brief.example.json), [research](assets/research.example.json), [playbook](assets/playbook.example.json), [approval](assets/approval.example.json) and [review](assets/review.example.json) templates. Replace illustrative models, facts, dates, pricing and constraints with real evidence; approval/review examples deliberately do not grant approval. Unsupported image dimensions fail before reserving an attempt. The budget limits estimated spend and attempt count, not actual provider billing. Available settled-cost headers and request IDs are recorded separately; absent cost metadata remains unknown. Do not resubmit an ambiguous charged request; inspect `status` and reconcile its saved job first.

The [adapter contract](references/aisa-contract.md) documents implemented routes and gaps. The [research-contract snapshot](references/research-contracts.json) records free MCP schema discovery on 18 October 2026; it does not establish paid execution or current availability. Native AIsa MCP research is preferred; direct search/extract adapters require the same HTTP fallback gate.

## API reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for current endpoint contracts and the [model catalog](https://aisa.one/docs/guides/models) for discovery. Available documentation, authenticated execution access and a completed generation are separate checks.

## License

MIT — see [LICENSE](../LICENSE).
