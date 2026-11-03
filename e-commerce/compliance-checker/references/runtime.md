# Local brief and report helper

The host agent interprets the conversation, conducts research through AIsa and inspects evidence. This dependency-free Node.js helper validates the resulting records and renders them. It does not parse natural language, call APIs, inspect certificates or determine the law. A validation success means record consistency, not legal correctness.

Run the compiled entrypoint with Node.js 22+ from the installed skill directory, or use its absolute path:

```sh
node dist/cli.js inspect-brief /absolute/path/brief.json
node dist/cli.js validate /absolute/path/assessment.json
node dist/cli.js render /absolute/path/assessment.json
```

Results go to stdout; errors go to stderr. Exit codes: 0 for a valid input/result, 1 for input/read/validation failure, 2 for command usage. Redirect output to a new user-workspace file when saving a report. Do not overwrite a prior assessment without preserving its evidence/history.

## Brief record

See [brief.example.json](../assets/brief.example.json). Each brief describes one SKU or materially identical variant family; use separate assessments for products with different facts. Several destinations/platforms can share a brief. Preserve all requested products when combining reports.

| Field | Meaning |
| --- | --- |
| `schemaVersion` | Required integer `1`. |
| `asOf` | Required research/as-of date, `YYYY-MM-DD`; keep it distinct from the selling date. |
| `product.name` | Optional during intake; the actual product when known. |
| `product.facts` | Optional string array of supplied facts with provenance in the text, such as “Seller states …” or a local report's filename/page. Do not turn unsupported claims into verified facts. |
| `destinations` | Optional array of `{country, subdivision?, platforms?}`. Use uppercase ISO alpha-2 codes, such as `US`, `DE`, `GB`. Explicit `EU` is allowed for a preliminary EU baseline, with actual member-state selection pending. Do not silently map “Europe” to `EU`. |
| `destinations[].platforms` | Array of `{name, site?}`. Record the actual platform/site; a Shopify destination does not require a storefront URL. Clarify ambiguous marketplace sites rather than assuming one. |
| `plannedSale` | Optional `{start?, end?, note?}`. Use `YYYY-MM-DD` for a known day or `YYYY-MM` for a known month: “January 2027” becomes `start: "2027-01"`, preserving month precision. Keep vague seasons or undecided timing in `note`. |
| `seller` | Optional `{location?, shipFrom?, fulfilment?}`; supply only established facts. |
| `unknowns` | Optional string array of material unanswered questions, dependencies and conflicting facts. |

Omit unknown structured values rather than inventing them. A note or `unknowns` entry preserves what the user actually said. Month precision is enough to record the selling start; the helper uses month boundaries internally for interval checks and preserves the month in the report. It must not cause the host to demand an exact day. Vague timing recorded only in a note remains preliminary: research unaffected requirements, and keep date-sensitive findings uncertain until the relevant interval is established. Do not infer a finite end to ongoing sales. For a rule changing within a selling period, explain when it applies and any transition conditions rather than implying one rule covers the entire period.

`inspect-brief` returns `readyToResearch`, `preliminary`, `missingCoreFields`, at most two `nextQuestions` and warnings. Product plus destination (including an explicitly selected EU baseline) makes research ready. These are intake hints, not a compulsory sequence: prioritize product-critical questions, translate into the user's language, and do not ask again about something they already said was undecided. Missing core fields are tracked for every destination.

## Assessment record

See [assessment.example.json](../assets/assessment.example.json), which is explicitly synthetic and contains no verified legal conclusion. Required top-level fields are `schemaVersion: 1`, `brief`, `scope`, `evidence` and `findings`; `synthetic: true` marks demonstrations. Unknown fields are rejected to catch misspellings. Use empty arrays honestly when nothing was checked.

Each evidence record contains:

- `id`, `title`, `url`: unique ID, source title and an HTTP(S) URL without credentials.
- `authority`: `regulator`, `legislation`, `platform` or `other`; this is the researcher's classification, not URL-based automatic verification.
- `jurisdictions`: country codes or `EU`; do not label a national source EU-wide without support.
- `accessedAt`: actual source-reading date, no later than `brief.asOf`.
- `excerpt`: short supporting text, with section/publication/update details where known. Preserve the original source separately if necessary; avoid copying entire documents into reports.
- `inspected`: true only after the relevant original content was read, including material exceptions. A source merely returned by search stays false.

Keep local seller documents private. Record their identifiers/pages and actual observations in product facts and the finding explanation; an authoritative web rule and a seller's report serve different evidentiary purposes. Do not upload a document just to manufacture a public URL. This runtime checks web-source references, not document authenticity or file provenance.

Each finding contains:

- `id`, `title`, `scope`: unique ID and the precise product, check and platform/site being assessed. Keep findings narrow and separate differing markets/platforms.
- `status`: `issue-found`, `insufficient-evidence`, `not-applicable`, `not-checked` or `no-issue-found` within that finding's scope.
- `kind`: `law`, `platform-policy` or `guidance`; regulator guidance is not automatically binding law.
- `jurisdiction`: country code or `EU` matching an applicable destination.
- `sourceIds`: existing evidence IDs; no invented citations.
- `explanation`, `action`: observed facts, limits and the concrete next step. Include who should act and when where known. Order findings by urgency; do not invent a legal deadline.
- `applicability.reason`: product/role/date conditions and unresolved dependencies.
- `applicability.temporalStatus`: `applies`, `uncertain` or `outside-period`.
- Optional `applicability.effectiveFrom` / `effectiveTo`: established application dates, distinct from publication and access dates.
- Optional `applicability.ruleStatus`: `enacted`, `proposed` or `unknown`. Substantive law conclusions require `enacted`. Use an unresolved finding for a proposal; never label a proposal a mandatory launch requirement.

Substantive findings need inspected authoritative support appropriate to the kind. All referenced sources for such a finding must have been inspected. EU sources may support a Germany finding; Germany-only sources cannot support an EU-wide conclusion. Supplied effective periods cannot contradict the assessed selling period. `outside-period` needs a known boundary proving the periods do not overlap; otherwise use `uncertain`. The host still must check amendments, transition conditions, actual source authority and semantic applicability.

`validate` returns `valid`, `preliminary`, `coverage`, counts, missing core fields and warnings. Coverage is always `partial` or `unchecked`, never overall clearance. `render` produces the scope, selling plan, unresolved facts, findings/actions and evidence register as Markdown, escaping supplied markup. Empty findings mean unchecked coverage. Translate or summarize the rendered report for the user without dropping uncertainty, sources or unchecked areas.

## Development

```sh
npm ci --ignore-scripts
npm run typecheck
npm run build
npm test
```

TypeScript and development dependencies are pinned in the skill-local package files. Consumers can run the checked-in JavaScript without installing those dependencies. Tests exercise the shipped CLI; regenerate `dist/` after source changes and verify an isolated export builds to identical bytes.
