# Skill Authoring SOP — AIsa-team/agent-skills

Standard operating procedure for composing and maintaining skills in this
repo. Based on the [agentskills.io specification](https://agentskills.io/specification)
with a few house-level requirements on top.

## TL;DR

1. Skill lives in `<skill-name>/` at the repo root.
2. `SKILL.md` frontmatter must be **spec-compliant** (validate with
   [`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref)
   before merging).
3. **Every skill must explicitly declare which harnesses it works with**,
   both in the `compatibility:` field and in a `## Compatibility` section
   of the SKILL.md body (or README.md). No exceptions — this is the
   value proposition of the agent-skills format.
4. Include a `README.md` with the same compatibility block so humans
   browsing the repo on GitHub see it immediately.

## Directory layout

```
<skill-name>/
├── SKILL.md          # required — metadata + agent-facing instructions
├── README.md         # required in this repo — human-facing overview
├── scripts/          # optional — runnable code
├── references/       # optional — long-form docs the agent loads on demand
├── assets/           # optional — static resources (templates, data, images)
└── ...
```

Directory name rules (enforced by the spec):

- Lowercase ASCII letters, digits, and hyphens only — `a-z 0-9 -`
- 1–64 characters
- No leading or trailing hyphen
- No consecutive hyphens
- **Must match the `name:` field in `SKILL.md` exactly.**

## `SKILL.md` frontmatter

| Field           | Required | Notes |
|-----------------|----------|-------|
| `name`          | **Yes**  | Matches directory name. See rules above. |
| `description`   | **Yes**  | 1–1024 chars. Describe **what the skill does and when to use it**. Include specific keywords that help an agent pick it. |
| `license`       | **Yes in this repo** | `MIT` unless the skill has a different license. Spec treats this as optional, but we require it. |
| `compatibility` | **Yes in this repo** | 1–500 chars. Must list the harnesses the skill works with. Spec treats this as optional; we require it. |
| `metadata`      | Recommended | Vendor metadata — `homepage`, `emoji`, `requires`, `primaryEnv`, etc. Use reasonably unique keys. |
| `allowed-tools` | Optional | Space-separated list. Experimental, support varies. |

### Canonical frontmatter template

```yaml
---
name: <directory-name>
description: "<one paragraph: what + when. 1-1024 chars. Specific keywords for agent discovery.>"
license: MIT
compatibility: "Works with any agentskills-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires <bins> and <env vars>."
metadata:
  homepage: https://aisa.one
  emoji: "<single emoji>"
  requires:
    bins: [<binary1>, <binary2>]
    env: [<ENV_VAR_1>]
  primaryEnv: <PRIMARY_ENV_VAR>
  harnesses: [claude-code, claude, opencode, cursor, codex, gemini-cli, openclaw, hermes, goose]
---
```

### Why both `compatibility:` (top-level) and `metadata.harnesses`?

- **`compatibility:`** is the agentskills.io-spec field. Human-readable
  sentence. Harnesses that read the spec surface this to the user.
- **`metadata.harnesses:`** is a machine-readable list some harnesses
  (OpenClaw, Hermes) use for install-time checks.

Include both. The sentence in `compatibility:` should remain current as
we add support for new harnesses.

## `SKILL.md` body

Follow this structure (matches the existing sibling skills in this repo):

```markdown
# <Skill Name> <emoji>

**<One-sentence tagline describing the value.> Powered by AIsa.**

<One paragraph expanding the tagline. What sources / models / workflows
it touches. Any unique capability.>

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness, including:

- **Claude Code** — via `claude skill add`
- **OpenClaw** — drops into the skill directory
- **OpenAI Codex** — via the `skills/` folder
- **Cursor** — agent skills support
- **Gemini CLI**, **Goose**, **OpenCode**, **Hermes**, and others

Requires `python3`, `bash`, and `AISA_API_KEY`.

## What Can You Do?

### <Use case 1>
```text
"<example query>"
```

### <Use case 2>
```text
"<example query>"
```

## Quick Start

```bash
export AISA_API_KEY=sk-...
python3 {baseDir}/scripts/<client>.py <subcommand> [--flags]
```

Use the literal token `{baseDir}` in SKILL.md script paths — the harness
substitutes it at load time. Do **not** use `${SKILL_ROOT}`, absolute
paths, or `./scripts/...`; `{baseDir}` is the repo convention (see
`CLAUDE.md` at the repo root).

## Inputs and Outputs

- Input: <what the user passes>
- Output: <what the skill returns — formats, fields>

## When to use / When NOT to use

- Use when: …
- Do NOT use when: …

## Requirements

- <bin> / <version>
- `AISA_API_KEY` — required, get one at [aisa.one](https://aisa.one)
- <optional creds>

## API Reference

<One-sentence description of the endpoint family this skill calls, then
a bulleted list of each specific endpoint with a link to its reference
page. Example:>

This skill calls the following AIsa endpoints directly:

- [<Endpoint name>](https://aisa.one/docs/api-reference/<category>/<slug>) — <what it's used for>
- [<Endpoint name>](https://aisa.one/docs/api-reference/<category>/<slug>) — <what it's used for>

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
```

Keep `SKILL.md` under 500 lines. Move long reference material into
`references/*.md` and link to it — agents load those on demand, saving
context.

## Where API Reference information goes

**SKILL.md gets the detailed per-endpoint list.** Agents need to know
exactly which endpoints they can call; that's part of the skill's
machine-readable contract.

**README.md gets only a one-paragraph pointer to the catalog.** Humans
landing on the folder on GitHub want orientation, not an endpoint table.
Duplicating the list creates drift — when AIsa adds a new endpoint we'd
have to update two places per skill.

Every README in this repo uses the identical block below — copy it
verbatim, don't customize:

```markdown
## API Reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for the
complete catalog of endpoints this skill can call.
```

## `README.md` body

The README is for humans landing on the skill's folder on GitHub. It
should mirror the SKILL.md body but drop the `{baseDir}` substitution
token (replace with concrete `scripts/...` paths) and any
harness-specific language. Mandatory section:

```markdown
## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI,
OpenClaw, Hermes, Goose, and others.
```

## Documentation links

Always link to the canonical docs host: **`https://aisa.one/docs/...`**

Do **not** use:

- `https://docs.aisa.one/...` (legacy subdomain; redirects today, may not later)
- `https://aisa.mintlify.app/...` (preview/staging host; not a stable URL)

Common targets:

| You want to link to | Use |
|---|---|
| Docs landing | `https://aisa.one/docs` |
| API reference index | `https://aisa.one/docs/api-reference` |
| A specific endpoint | `https://aisa.one/docs/api-reference/<category>/<slug>` |
| Model catalog | `https://aisa.one/docs/guides/models` |
| Docs index for LLMs | `https://aisa.one/docs/llms.txt` |

## Validation before submitting a PR

1. `name` matches directory name
2. `name` passes the regex: `^[a-z0-9]+(-[a-z0-9]+)*$`, length ≤ 64
3. `description` ≥ 1 char and ≤ 1024 chars
4. `license` present
5. `compatibility` present and mentions specific harnesses
6. README.md has a `## Compatibility` section
7. If the skill uses an env var, `metadata.primaryEnv` points at it
8. All doc links use `aisa.one/docs/...` (never `docs.aisa.one` or `aisa.mintlify.app`)
9. `SKILL.md` has a detailed `## API Reference` section listing each endpoint the skill calls, with links to the per-endpoint docs
10. `README.md` has the **identical one-paragraph `## API Reference` block** (copied verbatim from the SOP) — do not list specific endpoints in README
11. Spec conformance via the reference validator (optional but recommended):
    ```bash
    skills-ref validate ./<skill-name>
    ```

## Updating this SOP

If you add a new harness that supports agent skills, update:

- The canonical frontmatter template here
- The `compatibility:` field in each skill's SKILL.md
- `metadata.harnesses` in each skill's SKILL.md
- The `## Compatibility` section in each README.md

Keeping harness compatibility explicit and current is the point.
