# Research, approval and creative production

Use this reference to make the report and playbook concrete enough to approve and the final assets inspectable. It describes host-agent responsibilities; JSON field names and executable commands come from the shipped CLI contract.

Use the [brief](../assets/brief.example.json), [research](../assets/research.example.json), [playbook](../assets/playbook.example.json), [approval](../assets/approval.example.json) and [review](../assets/review.example.json) templates. They are record shapes, not researched evidence or permission. Replace every illustrative value before use. Read [native-workflow.md](native-workflow.md) for the default MCP/CLI handoff and [aisa-contract.md](aisa-contract.md) for retained direct-API compatibility.

## Input evidence and product identity

Before any research, open at least one user-supplied real-product photo for every requested SKU. Record file hash, variant, angle, visible labels, condition and limitations. Reject unreadable files, placeholders, competitor images and generated concepts as product evidence. A URL must be accessible and its image inspected. If an essential view is missing, request it and stop the dependent work.

Maintain a product-facts ledger with a source for each fact: SKU, product name, dimensions/units, material, color, quantity, included parts, supported use, compatibility, care, warranty and substantiated claims. Separate user assertions from facts visible in photos or supported by a specification/document. Images alone cannot establish chemical composition, load rating, certifications or performance. Ask about consequential contradictions rather than choosing the more marketable version.

A multi-SKU job needs an explicit photo-to-variant map. Do not transfer one variant's color, accessory bundle, compatibility or measurements to another. Treat required warnings and brand spelling as controlled content.

Record each product's required `category`. Shopify targets require `themeUrl` or `themeDescription`, destination country and language. For native images/video, discover whether the selected model accepts inline bytes or requires a public HTTPS reference. When a URL is required, obtain a user-supplied `remoteUrl` whose downloaded bytes match the inspected local photo; never publish a private product photo silently to obtain one. The compatibility Wan adapter specifically requires that URL. No upload service is implemented.

## Research report

Keep the report focused on decisions the user can change. Include:

1. **Brief and scope:** product, SKUs, audience, destination, platform/category/placement, language and intended outputs.
2. **Requirement matrix:** current official sources and retrieval dates, mandatory constraints, recommendations, category exceptions, unresolved conflicts and resulting checks. See [platforms.md](platforms.md).
3. **Comparable creative review:** directly inspected examples with URLs, dates, market/category/placement match, observed signals and evidence tier.
4. **Patterns and gaps:** composition, product visibility, information sequence, buying objections, proof, localization and missing product facts. Distinguish observation from inference.
5. **Recommended playbook:** proposed direction, alternatives that matter, production scope/cost and testable hypotheses.

Start with a focused comparable set, usually 3–5 relevant examples per platform/placement group; expand only if evidence is too thin or contradictory. This is a research budget, not a claim that a tiny sample represents the market. Prefer several sellers/brands and comparable price/product contexts. Search results alone do not establish image layout or video behavior: open the listing, inspect the image or view the relevant video frames before describing them.

Do not use a competitor's source image as a generation reference for the user's product. Extract abstract patterns such as information order or framing; create original execution grounded in the user's materials.

## Performance evidence tiers

| Tier | What can be said | Limits to record |
| --- | --- | --- |
| Measured outcome | User-provided purchase conversion, revenue, order or randomized-test results tied to identified creatives | Source/account scope, period, sample size, attribution, placement and whether the design permits causal conclusions |
| Platform-selected performance example | A platform identifies a creative as high-performing under a stated metric | Exact metric, objective, period, selection bias, relative versus absolute measure; conversions may not mean purchases |
| Public proxy | A listing/creative has an observed sales rank, review count, views, engagement or search position | Product popularity and visibility are not proof that this content caused sales; rankings and counts change |
| Visual reference only | Useful composition, storytelling or copy pattern was directly inspected | No performance evidence; treat proposed benefits as hypotheses |

Never fabricate CTR, ROAS, conversion, sales or ad spend. Do not translate “popular” into “high-converting.” When no business outcome is available, title that part of the report “Comparable creative references and observed signals,” explaining the evidence gap while still providing a useful playbook.

The executable accepts `measured`, `platform-selected` and `proxy` metric tiers. Encode a visual-only reference as `proxy` with `{ "name": "performance unavailable", "value": null, "window": null }` and an explicit limitation that it has no performance evidence. This preserves the unknown instead of inventing a metric or using an unsupported tier value.

For context, [Amazon Manage Your Experiments](https://sell.amazon.com/tools/manage-your-experiments) describes randomized listing-content tests. [Shopify behavior reports](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/default-reports/behaviour-reports) define store conversion metrics. [TikTok Top Ads](https://ads.tiktok.com/resources/help/article/top-ads) describes advertiser-authorized ad examples; those are ad evidence, not proof about TikTok Shop listing performance or an expansion of supported scope.

## Playbook to approve

Assign an explicit version and content hash. The approval packet must contain enough detail to predict what will be generated:

| Part | Required decisions |
| --- | --- |
| Positioning | Audience, buying situation, primary benefit and supporting facts; separate promises from proven features |
| Product controls | Reference images/SKUs, immutable identity details, brand assets, factual claims and prohibited transformations |
| Visual direction | Background, lighting, crop, palette, typography, model/prop use and how the real product remains accurate |
| Image sequence | Per placement: shot purpose, source views, scene, text/callouts if permitted, aspect/crop and expected export |
| Copy architecture | Required fields, language/units, keyword intent, benefit hierarchy, evidence for claims and applicable constraints |
| Video storyboard | Shot sequence, duration target, camera/product motion, supported demonstration, captions/audio if applicable, source assets and export |
| Production variants | Which variants answer which hypothesis; quantity, selected model/tool route and model-specific options, exact reference mapping, current price evidence, estimate and attempt allowance; estimates do not cap billing |
| QA and delivery | Technical checks, fidelity/claim checks, disclosure requirements, deliverables and unresolved limitations |

Before approval, present positioning, outlines, shot plans and storyboards. Do not generate product images, video previews or ready-to-publish listing copy. Ask the user to confirm or revise the exact version. Persist the user's affirmative response and approved hash; elapsed time, silence or the agent's own recommendation is not approval.

For native production, approve the selected model, model-specific request template, generation dimensions/options and required reference bindings; final export dimensions remain a separate requirement. There is no native model-name allowlist. The retained REST image adapters still have their documented size mappings. **Disclose the selected operation/model's verification and quality limits in the rendered playbook.** The retained REST Wan video adapter specifically remains experimental and requires `allowExperimentalVideo: true`. Schema validation or mocked tests do not establish live generation. Obtain the user's approval of that disclosure; do not bury it in a source file or infer agreement from a generic video request.

Material changes invalidate approval: different products/references, claims, target market/placement, factual requirements, creative direction, selected model or model-specific options, quantities or cost bounds. Routine corrections that restore the approved brief do not require new approval unless they expand scope or spend. If the user edits the playbook, save the revised version and obtain approval for it before production.

## Product-faithful production

Use the selected AIsa connection and a discovered operation whose current model contract supports the actual references and desired media. Validate full schemas and model access first; do not silently fall back to REST, another model or text-only generation. Start with the smallest approved useful batch, inspect it and continue only if fidelity is acceptable. Record model/operation, input hashes, prompt, parameters, task ID, timestamps and output path/hash. Record quoted/estimated cost separately from settled charges in the native receipt or valid REST cost header. Missing settlement metadata remains unknown. An estimate or attempt allowance is not a provider billing cap.

For images, the local `preserve` mode fits/resizes the original photograph on a white canvas without cropping or generative redrawing. It does not mask the product, remove its existing background or create new product views. Use it when the source already suits the placement; Amazon main images need an already compliant photo and reviewed output framing. Reference-conditioned edits can still alter labels, geometry or finish. If acceptable fidelity cannot be achieved, request a better source or simpler treatment; do not describe a reference prompt as a preservation guarantee.

When text belongs on an image, inspect OCR and the visible result for brand spelling, measurements, units and clipping. Deterministic typography composition is not implemented by this runtime; do not promise that capability. Do not blur or re-create the product label to hide a generation error. Respect each placement's rules on text, props, packaging and product-only composition.

For video, distinguish camera movement from product functionality. Do not animate a static object as though it has powered motion, change fill/quantity between frames, invent assembly mechanisms or show unsupported demonstrations. Inspect transitions and moving details as well as the opening frame. Choose audio behavior explicitly from the selected model contract and approved storyboard; the runtime does not add captions, assemble multiple clips or produce a finished edit from a storyboard. The retained Wan REST adapter defaults to no generated audio. If the approved placement needs those capabilities, mark that deliverable unsupported rather than treating one short clip as complete.

Use the native polling/result commands to recover the existing task; a status check never creates a replacement generation. The compatibility `resume` command checks or recovers the saved REST job. Retry only after a confirmed failure or reviewed rejection within the allowance. After an ambiguous dispatch, reconcile the saved job and possible charge before resubmission. Use `status` to inspect approval and job state. Do not switch transports or use manual calls to bypass workflow gates.

Final copy must trace every objective claim to the approved ledger. Localize units, spelling and natural phrasing, while preserving specification meaning. Avoid translation that strengthens a claim or changes warranty coverage. User-supplied uncertainty remains uncertainty.

## QA record and acceptance

Tie QA to the **actual saved artifact hash**. Supply one review finding for every distinct SHA-256 exactly once; retained byte-identical outputs share that finding and its notes. Changed files require review of affected checks. Never populate a “passed” record because generation succeeded or because the prompt requested compliance.

| Check group | Inspect |
| --- | --- |
| Technical | Decodable file, actual format, dimensions/ratio, bytes, duration, required fields and current field limits |
| Product fidelity | Correct SKU, geometry, count, color/material appearance, label/logo, included parts, scale and compatibility |
| Claims and language | Evidence-backed assertions, exact quantities/units, destination language, legible typography and no invented social proof |
| Placement | Main/gallery/video distinctions, category rules, text/prop restrictions, theme crops and disclosure/metadata |
| Video/audio | Representative frames plus transitions/motion, stable identity, truthful operation, caption timing, audio content and rights |
| Provenance | Approved playbook version, source/input hashes, operation/task records, saved output and inspection findings |

Use automated probes and OCR where available, followed by actual visual inspection and comparison to original references. Inspect the complete copy. If a host cannot view video, it may inspect extracted frames and timing/audio with appropriate tools, but must disclose coverage gaps; do not claim complete motion QA from a single still. The executable review record accepts only `pass` or `fail` for each check. Leave uninspected output awaiting review, or record a failed check with the verification gap explained; never manufacture a pass or invent an `unverified` enum value.

Do not deliver a failed or unverified artifact as platform-ready. Correct failures within approved bounds, rerun the affected checks and retain the failure history. If production is blocked by unavailable capabilities or insufficient references, say which deliverable is blocked and what is needed.

## Delivery and measurement

Provide saved media, copy, report, approved playbook and a manifest linking each artifact to SKU/platform/placement, sources and QA. Distinguish ready-for-user-review outputs from blocked assets. Include manual upload notes only where supported by current official evidence; do not publish automatically.

For learning, propose a specific hypothesis, variant change, primary metric and observation window suited to the seller's available data. Use randomized content tests where the platform and seller eligibility permit. If the user later provides results, check attribution and sample size before updating the playbook. Do not promise lift from visual quality, a heuristic score or a competitor pattern alone.
