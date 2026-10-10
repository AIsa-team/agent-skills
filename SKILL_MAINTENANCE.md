# Skill versions, releases, and freshness

Each skill has an independent `metadata.version` in `SKILL.md`, a
`CHANGELOG.md`, and a `skill.json` manifest. Existing declared versions are
preserved; previously unversioned skills start at `1.0.0`. Baselines do not
claim recent verification: `maintenance/reviews.json` starts empty.

## Editing and releasing

Use patch bumps for compatible fixes to code, instructions, or examples;
minor bumps for compatible capabilities; major bumps for incompatible inputs,
outputs, authentication, or runtime requirements. Choose bumps explicitly,
including for retained pre-1.0 versions.

```sh
.venv/bin/python .github/scripts/skill_lifecycle.py bump \
  --skill platform/aisa --part patch \
  --message 'Align connection instructions with the current MCP contract'
.venv/bin/python .github/scripts/catalog_quality.py --changed-from origin/main
.venv/bin/python .github/scripts/skill_lifecycle.py validate --changed-from origin/main
.venv/bin/python .github/scripts/skill_lifecycle.py checks
.venv/bin/python .github/scripts/skill_lifecycle.py catalog --check
```

The helper updates the canonical version, existing vendor version fields,
Node package/lock versions when present, and the changelog. CI rejects changed
managed bundles without a higher version and a changelog entry. Category license
changes require bumping affected skills. Owner/upstream manifest changes are
bundle changes. Review records live outside bundles and do not require releases.

Pull requests validate and build without publishing. Pushes to `main` must pass
validation, declared runtime checks, and packaging before publishing starts.
Artifacts are tied to the exact source SHA. Each skill gets a reproducible
tarball, payload/archive SHA-256 digests, an immutable source tag, and a GitHub
release named `skills/<name>/v<version>`. Different content under an existing
version is rejected. Published releases are never overwritten; interrupted
draft uploads can be resumed for the same source revision.

Archives unpack to `<name>/` plus the category license where applicable. Install
the skill directory and preserve the accompanying license. Bundles contain
complete sources, references, manifests, and built entrypoints. Builds must match
the checked-in distribution; consumers do not need this monorepo.

Destinations are configured in `.github/skill-catalog.json`. Category publishing
skips identical contents, commits onto destination history, and uses normal
pushes. `SOURCE.json` records the most recent content update's source revision.
Platform deliberately has no category destination but has individual releases.
The obsolete SaaS workflow was removed because its source skills are absent.

## Monitoring upstream changes

`maintenance/upstreams.json` defines sources. Each skill declares applicable
source IDs in `skill.json`. Sources are fetched once per configured ID, with four
concurrent readers and bounded responses/timeouts. Initial dependency mappings
use category API families and documentation referenced by the skill. Owners
should narrow scopes where more specific contracts become available.
Each source runs in a disposable worker with a 90-second deadline, covering
DNS, response streaming, pagination, and parsing as well as socket timeouts.

- CLI: monitor the official npm release version, executable metadata, runtime
  requirements, and distribution integrity. A change requests review of relevant
  command help/flags; the monitor does not install or run new CLI releases.
- MCP: initialize and enumerate all `tools/list` pages, recording tool names,
  descriptions, and schemas. Also monitor the public AIsa MCP catalog. No tool
  execution, paid probes, or sign-in automation occurs. Router tool-list changes
  do not reveal every nested capability change; API contracts/docs provide
  additional coverage, and owners inspect relevant router schemas during review.
- Docs: fetch Markdown pages and normalize line endings/trailing whitespace.
  HTML error pages and failed fetches become monitoring failures. Referenced
  URLs may themselves be stale; correct reported failures rather than excluding
  them silently.
- REST: select relevant OpenAPI paths and follow transitive component references.
  Changes to unrelated endpoints/components do not invalidate scoped snapshots.

Monitoring runs daily at **09:00 Asia/Shanghai**, on manual dispatch, or on a
`repository_dispatch` event of type `skill-upstream-changed`. GitHub scheduled
runs may be delayed. Observations/reports are stored on the independent
`skill-maintenance-state` branch and retained as artifacts for 30 days. State
updates do not trigger publication. The first observation is a comparison
baseline, not an approved review.

Observed hashes and reviewed hashes are separate. Pending changes stay pending
across polls until a review records their new hashes. Failures retain the last
successful snapshot while marking it unavailable. No automatic rewrites or
version bumps occur.

## Fourteen-day warnings and reviews

The daily Actions summary and JSON report show owner, version, update age,
verification age, and pending/unavailable sources.

- Warn at 14 elapsed days without a substantive content update, even if reviewed.
- Warn when verification is absent, at least 14 days old, for a different bundle,
  or missing coverage of declared sources.
- Flag relevant upstream changes immediately, regardless of update age.
- Report unavailable monitoring separately; a successful poll is not verification.

Update dates come from committed Git content changes. Pure version, changelog,
or maintenance-manifest changes do not reset them. A no-change review can produce
“unchanged, verified current” while retaining the update-age warning. Warnings
are advisory and do not block unrelated releases.

Generate a local report without network access:

```sh
.venv/bin/python .github/scripts/skill_maintenance.py scan \
  --offline --output build/maintenance
```

Omit `--offline` to fetch evidence. Pass `--previous <state.json>` to preserve
earlier observations. Do not commit generated observations to `main`. After
assessing changes and running relevant checks, record a review using successful
snapshots collected within the last 24 hours:

```sh
.venv/bin/python .github/scripts/skill_maintenance.py review \
  --skill platform/aisa --state build/maintenance/state.json \
  --evidence 'Checked commands, schemas, and authentication guidance; no content changes required'
```

Commit the updated review ledger. Recording a review asserts human assessment;
the command cannot prove semantic correctness. Restore unavailable sources
before recording complete verification.

Scheduled runs maintain one issue per affected skill. Issues change on meaningful
status/evidence changes, not daily age increments; resolved warnings close the
issue. Owners appear in report/issue bodies. The first run may open issues for
every skill because baseline verification is unknown.

## JavaScript and TypeScript

Declare languages, runtime versions, built entrypoints, upstreams, and checks
inside each skill. Commands are argument arrays, not shell text. `{python}`
resolves to the gate's Python interpreter.

```json
{
  "schema_version": 1,
  "owner": "@aisa-barry",
  "languages": ["typescript", "javascript"],
  "runtime": {"node": "22"},
  "entrypoints": ["dist/client.mjs"],
  "checks": {
    "lint": [["npm", "run", "lint"]],
    "typecheck": [["npm", "run", "typecheck"]],
    "build": [["npm", "run", "build"]],
    "test": [["npm", "test"]]
  },
  "upstreams": ["aisa-cli"]
}
```

TS skills require local `package.json`/`package-lock.json`, typecheck/build/test
commands, and checked-in JavaScript entrypoints. Node packages declare
`engines.node`; package/lock versions match the skill version. `workspace:`,
`file:`, and `link:` dependencies are prohibited. Declare every language present.
Dependency-free JS helpers need no npm package. The catalog gate checks `.js`,
`.mjs`, and `.cjs` syntax; TS uses declared compilation checks.

Checks run in temporary standalone exports. npm uses `npm ci --ignore-scripts --engine-strict`,
so dependency installation hooks are disabled; declare builds explicitly. Code
must work without cross-skill or repository imports. Bundle runtime dependencies
or document skill-local installation. Tests should exercise shipped entrypoints.

## Workflow setup

The existing `SYNC_AISAS_KILLS_TOKEN` must push to configured category repos.
GitHub's workflow token needs contents write for releases/state and issues write
for maintenance issues. Enable repository Issues. When MCP requires credentials,
configure a supported discovery credential as `AISA_MONITOR_MCP_TOKEN`; missing
credentials cause an unavailable warning. Public docs/npm/OpenAPI need no secret.

CODEOWNERS requests review of maintenance policy and tooling. Administrators
should require `validate-catalog` before merge; CODEOWNERS alone does not enforce
branch protection. Publication depends on validation even on a direct main push.
Update this guide and `SKILL_AUTHORING.md` when lifecycle policy changes.
