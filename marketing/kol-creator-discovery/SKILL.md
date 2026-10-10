---
name: kol-creator-discovery
description: Use this skill when a user needs KOL or influencer research, creator email lookup, similar-creator discovery, outreach-list building, influencer prospecting, or a contact table from TikTok, Instagram, or YouTube profile URLs. It uses AIsa's WaveInflu APIs to find verified creator emails, match similar YouTube or TikTok creators, enrich each recommended profile with contact emails, and return an outreach-ready Markdown table without inventing missing data.
license: MIT
compatibility: "Works with any agentskills.io-compatible harness, including Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3, curl, and AISA_API_KEY."
metadata:
  version: "1.0.0"
  short-description: AIsa-powered KOL email and creator discovery
  aisa:
    homepage: https://aisa.one
    requires:
      bins:
        - python3
        - curl
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

# KOL Creator Discovery

Build a contact-ready creator list from one social profile. Use AIsa WaveInflu to look up the seed creator's email, find similar creators, enrich every recommended profile with its own email lookup, and return one evidence-based table.

## Requirements

Set an AIsa API key:

```bash
export AISA_API_KEY="your-aisa-api-key"
```

Never print, log, or commit API keys. If the key is missing, ask the user to set `AISA_API_KEY`.

## Compatibility

Works with any agentskills.io-compatible harness, including Claude Code, Claude, OpenAI Codex, Cursor, Gemini CLI, OpenCode, Goose, OpenClaw, Hermes, and other runtimes that support skill folders.

Requires Python 3, curl, and `AISA_API_KEY`. Get a key at `https://aisa.one`.

## Quick Start

```bash
python3 {baseDir}/scripts/kol_creator_discovery.py research \
  "https://www.youtube.com/@mkbhd" \
  --limit 10 \
  --out kol-report.md \
  --json-out kol-report.json
```

With explicit content direction and audience filters:

```bash
python3 {baseDir}/scripts/kol_creator_discovery.py research \
  "https://www.tiktok.com/@creator" \
  --platform tiktok \
  --content-direction "consumer AI apps and productivity tools" \
  --regions US,GB \
  --languages en \
  --min-followers 10000 \
  --max-followers 500000 \
  --limit 15 \
  --out kol-report.md
```

## Core Workflow

### 1. Validate the brief

Collect or infer:

- One seed TikTok, Instagram, or YouTube creator profile URL
- Target discovery platform: `youtube` or `tiktok`
- Number of recommendations; default to 10
- Optional content direction, regions, languages, follower range, and average-view range

Infer the target platform from a YouTube or TikTok seed URL. If the seed is Instagram, ask for both the target platform and a content-direction description because WaveInflu similarity matching does not accept Instagram seed profiles.

Do not call an API until the input is a creator profile URL. Do not use individual post or video URLs as seeds.

### 2. Look up the seed creator's contact data

Call `POST /apis/v1/waveinflu/email-lookup` with the submitted profile URL. Preserve the returned platform, username, normalized profile link, region, emails, contacts, and quota metadata.

Treat returned email values as API-sourced contact data. Never infer an email pattern or manufacture a missing address.

### 3. Find similar creators

Call `POST /apis/v1/waveinflu/similar` with:

- `platform`: `youtube` or `tiktok`
- `seedProfileUrl`: include only for YouTube or TikTok seeds
- `contentDirection`: include when supplied; require it for Instagram seeds
- `limit`: default 10, maximum 100
- `filters`: include only the filters requested by the user

The API returns creators sorted by `similarityScore`. Preserve that order after removing duplicates and the seed creator.

### 4. Enrich every recommendation with an email lookup

For each returned creator profile URL, call `POST /apis/v1/waveinflu/email-lookup`. Use the primary `email` when present; otherwise use the first unique value in `emails`. If no email is returned, write `Not found` rather than guessing.

Default to 10 email enrichments. Before enriching more than 25 creators, tell the user how many email-lookup calls will be made and confirm the scope because each lookup can consume quota.

Continue when one creator lookup fails. Record `Lookup failed` for that row and finish the remaining list.

### 5. Normalize and rank

- Deduplicate by normalized profile URL, platform user ID, or channel ID.
- Keep WaveInflu's descending similarity order.
- Preserve exact follower and average-view counts in JSON.
- Use compact display values such as `125K` only in Markdown.
- Mark absent region, language, metrics, or emails as `—` or `Not found`.
- Separate API facts from any operator recommendation.

### 6. Return the deliverable

Use `references/report-template.md`. The main output must include:

- Seed creator and resolved discovery scope
- Number of similar creators returned and email coverage
- One Markdown table containing the seed and all similar creators
- Role, rank, creator, platform, profile URL, similarity score, followers, average views, region/language, email, and lookup status
- Quota or API limitations that materially affect completeness

Do not expose raw API payloads unless requested. Do not initiate outreach, send email, or upload the list to another system without separate user authorization.

## Helper Script

Run the complete workflow:

```bash
python3 {baseDir}/scripts/kol_creator_discovery.py research PROFILE_URL \
  --platform youtube \
  --content-direction "AI productivity creators" \
  --limit 10 \
  --out report.md \
  --json-out report.json
```

Run only email lookup:

```bash
python3 {baseDir}/scripts/kol_creator_discovery.py lookup \
  "https://www.instagram.com/onkimia/"
```

Run only similar-creator discovery:

```bash
python3 {baseDir}/scripts/kol_creator_discovery.py similar \
  --platform youtube \
  --seed-profile-url "https://www.youtube.com/@mkbhd" \
  --limit 10
```

Read `references/api-reference.md` before changing payload fields or interpreting response fields.

## Quality Rules

- Use only `https://api.aisa.one/apis/v1/waveinflu/...` endpoints.
- Never call WaveInflu directly or ask for a separate WaveInflu credential.
- Never invent, pattern-match, or infer email addresses.
- Do not claim that every creator has a public or deliverable email.
- Distinguish `Not found` from `Lookup failed`.
- Preserve profile URLs so an operator can verify every row.
- State when the target platform or content direction was assumed.
- Keep the result table concise and sort recommendations by API similarity score.
- Treat contact data as sensitive operational data; do not publish it or transmit it elsewhere without authorization.

## API Reference

This skill calls these AIsa endpoints directly:

- [WaveInflu Email Lookup](https://aisa.one/docs/api-reference/waveinflu/post_waveinflu-email-lookup) — retrieve creator emails and normalized profile details from TikTok, Instagram, or YouTube profile URLs.
- [WaveInflu Similar Creators](https://aisa.one/docs/api-reference/waveinflu/post_waveinflu-similar) — match similar YouTube or TikTok creators from a seed profile and/or content direction.

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
