# E-commerce Content Studio

Create researched product images, localized listing copy and product videos for Amazon US, TikTok Shop US and Shopify. The workflow starts with real product photos, produces an evidence-backed creative playbook, and generates only after the user approves it.

Version **1.1.0** makes host-managed AIsa MCP the default for new projects. It adds native request/quote/result handoffs and model-specific templates without a fixed model-name allowlist. The original direct-API adapters remain an explicit compatibility path. Existing projects are not migrated or resubmitted automatically.

At each new invocation the skill greets the user with six options: research/playbook, images, localized copy, video, a complete package, or resume/review/export. It honors a selection already expressed in the request. Photos, research and approval remain required.

## Connection choices

| Context | Connection | Credential responsibility |
| --- | --- | --- |
| Agent host with remote MCP and browser | **Default:** AIsa MCP at `https://mcp.aisa.one/mcp` | Host-managed OAuth; no API key requested by the skill |
| Headless host with remote MCP | Same MCP endpoint | Host MCP configuration may use `AISA_API_KEY` |
| Host without MCP support | Official `@aisa-one/cli` | Official CLI login/configuration |
| Explicit direct-API compatibility | Retained REST adapters, only under the shared HTTP fallback gate | Existing `AISA_API_KEY` in the environment |

MCP is an interface; API keys are one authentication method. A key configured for headless MCP does not make the skill a direct-REST client. The native runtime stores credential-free evidence and handoffs, while the host executes the actual MCP or official CLI operations. It does not extract OAuth tokens, launch a hidden API client or silently substitute another connection.

Follow [the shared connection and spending rules in SKILL.md](SKILL.md). Verify the selected connection with the free account/balance operation. New projects default to `mcp`; the CLI mode is explicitly recorded for hosts without MCP. REST requires both MCP and CLI to be unavailable, HTTP support, a valid existing key and the separate direct-HTTP paid-call approval. An authentication or generation failure does not establish that fallback gate.

## Supported content

| Platform | Market and scope |
| --- | --- |
| Amazon | US listing main images, gallery images, copy and product videos |
| TikTok Shop | US product-listing images, copy and videos |
| Shopify | Product pages with explicit destination country, language and actual theme/layout |

Support means planning and export profiles, not account integrations, analytics access, publishing or guaranteed platform acceptance. Other marketplaces, ads, organic campaigns and marketplace feeds remain outside this release. Planned additions are Etsy US/eBay US, followed by Amazon UK/DE/JP and TikTok Shop UK, then selected Shopee/Lazada/AliExpress markets; these have no committed release dates. See [platform scope](references/platforms.md).

- **Original-photo export:** `local-photo-export` with `imageMode: "preserve"` fits/resizes an already suitable photo without redrawing or cropping. It does not remove its background or create unseen angles. This remains the only mode for Amazon main images.
- **Native images/video:** select a suitable model from current AIsa discovery, verify its input/output contract and approve its model-specific options. Product-reference conditioning is required; a text-only model is not a substitute for a product-reference task. A newly listed model does not require adding its name to a local allowlist, but its actual request/response must fit the validated handoff.
- **Localized copy:** use a suitable native text operation with approved facts, fields and limits. Explicitly approved `host-copy` deliverables can import copy prepared by the host.
- **Direct-API compatibility:** retained GPT Image/Gemini image adapters, chat copy and experimental Wan video have their own fixed contracts and limitations. They do not limit the native catalog. See [compatibility contracts](references/aisa-contract.md).

Disclose the selected video model's verification and quality limits in the playbook. The retained REST Wan adapter specifically remains experimental and requires `allowExperimentalVideo: true` plus approval of that limitation. The runtime does not upload references, assemble clips, compose deterministic typography or add captions. Reference conditioning cannot guarantee product fidelity. Catalog discovery and offline validation do not establish successful live generation or marketplace acceptance.

## What the user provides

At least one clear photo of the actual product for **every requested SKU**, including copy-only jobs; target platform/market/category/placement/language; verified facts, variants, included items and brand assets; intended audience, deliverables and budget. Request further views when a shot or detail cannot be established. Competitor images and generated concepts are not product evidence.

Example requests:

> 用这几张产品照片，帮我做一套 Amazon 美国站商品图和英文文案，先给我看方案。

> Compare the available AIsa models for this product's Shopify images, then propose a playbook for approval.

> 用这张商品照片做一个 TikTok Shop 美国站短视频，先确认卖点、费用和分镜。

No usable product photos means no product research or production. No explicit approval of the exact playbook means no generated previews or final copy. Selecting a menu item is not approval.

## Runtime responsibilities

The **host agent** discovers live tools/models, checks model contracts, researches policies and comparable creatives, prepares the playbook, obtains user approval, executes native calls and inspects outputs. The **TypeScript runtime** validates photos and records, binds requests to approval/reference/quote evidence, tracks attempts and saved tasks, materializes outputs and validates artifacts.

Requirements: Node.js 22+, `ffmpeg`, `ffprobe`, and host research/image/video inspection tools. TypeScript source and compiled JavaScript ship with Ajv validation dependencies. Run `npm ci --omit=dev` once in the installed skill directory before using the compiled CLI. Local status, review, export and photo preservation do not require an AIsa credential.

## Commands

From the installed skill directory run `node dist/cli.js --help`. Use absolute project/input/output paths when calling it elsewhere. JSON examples are record shapes, not evidence or authorization.

| Command after `node dist/cli.js` | Purpose |
| --- | --- |
| `platforms` | Show supported profiles and roadmap |
| `models [--transport mcp\|cli\|rest]` | Default: give host discovery instructions; only explicit REST uses the direct catalog client |
| `init <brief.json> <project-dir> [--transport mcp\|cli\|rest]` | Validate real-product references; persist the selected transport, default MCP |
| `research-import <project-dir> <research.json>` | Record current requirements and inspected comparable evidence |
| `playbook-import <project-dir> <playbook.json>` | Validate and record the proposed playbook and native contract/templates |
| `report <project-dir>` | Write the report and exact playbook for user review |
| `approve <project-dir> <approval.json>` | Record explicit user approval of its hash |
| `connection-import <project-dir> <receipt.json>` | Record a successful native account/balance check without credentials |
| `build-native-request <project-dir> <deliverable-id> [--job <job-id>]` | Write exact native arguments and hash; `--job` builds an existing-task status request |
| `prepare-native <project-dir> <request.json>` | Bind the generation handoff to the approved deliverable, connection, schema and exact quote |
| `cancel-native-prepared <project-dir> <operation-id>` | Cancel an operation that was prepared but never dispatched; retain its audit record |
| `mark-native-dispatched <project-dir> <operation-id>` | Record intent immediately before the host sends that exact call |
| `ingest-native-result <project-dir> <operation-id> <result.json>` | Import the actual native response/receipt and retain task IDs, errors and costs |
| `prepare-native-poll <project-dir> <job-id> <request.json>` | Prepare a quoted status check of the same saved task |
| `resume-native <project-dir> <deliverable-id>` | Recover/materialize saved native results locally; does not submit a replacement |
| `import-host-copy <project-dir> <deliverable-id> <copy.json>` | Import copy only for an approved `host-copy` deliverable |
| `generate / resume / retry <project-dir> <deliverable-id>` | Local photo work or the explicit REST compatibility path; native paid generation uses the handoff commands above |
| `review <project-dir> <review.json>` | Record inspection against saved artifact hashes |
| `status <project-dir>` | Show project, approval and production state |
| `export <project-dir> <new-destination>` | Export a fully reviewed package to a new location |

The native execution sequence is **build arguments → quote the exact call → prepare → mark dispatched → host executes once → ingest result → recover/poll as needed → review → export**. Read [native-workflow.md](references/native-workflow.md) for exact receipt shapes, response mappings and failure handling. Do not treat the command table as a replacement for that contract.

For existing projects without a recorded transport, local inspection/export stays available. Their original REST generation/recovery path requires explicit `--transport rest` on network commands; do not automatically reinterpret an old paid job as a native request. Do not manually edit a project to bypass the transport lock or approval hash.

## Evidence, testing and delivery

Start from the [brief](assets/brief.example.json), [research](assets/research.example.json), [native playbook](assets/playbook.example.json), [approval](assets/approval.example.json) and [review](assets/review.example.json) templates. The native example intentionally requires real model/contract/pricing evidence before it can pass. The separate [REST playbook example](assets/playbook.rest.example.json) is only for explicitly selected compatibility projects. Replace all illustrative models, dates, pricing and facts. Approvals must come from the user; reviews must follow inspection of actual artifacts.

Run `npm ci`, `npm run typecheck`, `npm run build` and `npm test` for development checks. Offline fixtures test workflow/contracts, not live provider access, billing or output fidelity. The historical REST GPT Image smoke test returned a decoded PNG but changed product details and was not approved for listing use; see [its contract record](references/aisa-contract.md). No historical test establishes the current behavior of every discovered model.

The delivered package includes assets/copy, research, the approved playbook, provenance and QA. Separate estimates/quotes from known settled costs; missing cost metadata is unknown. An uncertain paid dispatch must be reconciled before resubmission, not retried through a different connection. Generation success alone never establishes product fidelity or platform readiness.

Read [the creative playbook guide](references/creative-playbook.md) for research evidence and QA. Public popularity is a proxy, not proof of conversion. This skill does not publish listings or promise conversion lift.

## License

MIT — see [LICENSE](../LICENSE).
