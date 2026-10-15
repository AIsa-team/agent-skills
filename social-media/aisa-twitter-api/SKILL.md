---
name: aisa-twitter-api
description: Search and inspect Twitter/X posts, profiles, timelines, communities, and trends through AIsa, or publish user-authorized posts with OAuth. Use for recent X research, account comparisons, conversation review, and approved text or media posting.
license: Apache-2.0
compatibility: Requires Python 3.11+, a POSIX system, AISA_API_KEY, and access to api.aisa.one. Executed requests require an authorized estimate budget; publishing also requires the linked X account and user authorization.
metadata:
  version: "1.1.0"
  aisa:
    emoji: 🐦
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Requires Python 3.11+, a POSIX system, AISA_API_KEY, and access to api.aisa.one. Executed requests require an authorized estimate budget; publishing also requires the linked X account and user authorization.
    version: "1.1.0"
---
# AIsa Twitter API

Use the read client for one-page research and the OAuth client for approved
posting. Both preserve provider data, report failures with nonzero exit status,
and account for requests through a durable cost ledger. This skill does not
create schedules or maintain a persistent watchlist by itself.

## Setup

Resolve commands relative to this installed skill directory, or use absolute
script paths. Python 3.11+ and a POSIX system are required; there are no third-party
runtime packages.

`AISA_API_KEY` resolves from the environment, then `~/.aisa/credentials`, then the
active Hermes profile configuration. Do not print the key or put it in command
arguments. OAuth binds the X account to that AIsa key; account authorization does
not itself authorize publishing content.

## Research

```bash
# Inspect an authenticated free quote; this does not retrieve posts.
python3 scripts/twitter_client.py search --query "AI agents" --type Latest --quote

# Execute within the user's approved estimate budget.
python3 scripts/twitter_client.py search --query "AI agents" --type Latest \
  --budget-usd "$APPROVED_BUDGET_USD" --cost-ledger research-costs.json

# Reuse the same task budget for another page or operation.
python3 scripts/twitter_client.py community-search --query "AI agents" --type Top \
  --cost-ledger research-costs.json
```

Read [cost controls and recovery](references/cost-control.md) before execution.
When a quote reports `may_exceed_estimate`, use `--allow-variable-cost` only if the
user accepted that possibility. Admission estimates are not final-charge caps.

Use `--help` for profiles, timelines, followers, searches, tweet detail/replies,
lists, and communities. Results contain original provider objects plus `_aisa`
HTTP and billing metadata. Native IDs, URLs, timestamps, metrics, and cursors are
not rewritten. Report missing data as missing; a quote is not retrieved evidence.

Requests fetch one page. Use a returned cursor only on an operation that supports
it, and reuse the ledger for additional pages. `mentions`, `user-search`, and
`quotes` reject nonempty cursors because the current parameter contracts do not
declare them despite pagination prose. `space-detail` is blocked before network
access because its contract does not declare the required cost controls.

For a time-bounded research question, include the appropriate X search operators
(e.g. `since:YYYY-MM-DD until:YYYY-MM-DD`) and inspect result dates before drawing
conclusions. Link supporting posts and describe the coverage actually retrieved.
Do not turn a one-off research request into scheduled monitoring.

## Approved posting

Read [posting and media](references/post_twitter.md) for account linking, exact
payloads, thread behavior, and recovery. Use the user's authorized text, target,
attachments, and number of posts. OAuth approval only links an account.

```bash
# Preview locally without credentials, spending, uploads, or publishing.
python3 scripts/twitter_oauth_client.py post --text "$APPROVED_TEXT" --dry-run

# Link an account when needed; --media also requests media.write for uploads.
python3 scripts/twitter_oauth_client.py authorize --media \
  --budget-usd "$APPROVED_BUDGET_USD" --cost-ledger posting-costs.json

# Publish the authorized content using the existing task budget.
python3 scripts/twitter_oauth_client.py post --text "$APPROVED_TEXT" \
  --cost-ledger posting-costs.json
```

Local files use the dedicated binary upload endpoint, followed by a post using
returned media IDs. Each request is separately quoted and recorded. Existing
media IDs can be attached directly. Oversized content requires explicit
`--thread`; inspect `--dry-run` output before publishing the expanded thread.

No external write is retried automatically. If an upload/post result is ambiguous,
inspect the account and request-specific billing evidence before continuing.
Preserve confirmed IDs and partial results. Do not republish an entire thread to
recover a failed later chunk. `status` shows local configuration, not live OAuth
account validity. Do not request X passwords or browser cookies.

## API contracts

The clients use [AIsa's Twitter API](https://aisa.one/docs/api-reference) with
Bearer authentication. The operation/parameter snapshot used by tests is in
`tests/fixtures/provider_contracts.json`; live contracts remain authoritative.

- [Advanced search](https://aisa.one/docs/api-reference/twitter/get_twitter-tweet-advanced-search)
- [Community search](https://aisa.one/docs/api-reference/twitter/get_twitter-community-get-tweets-from-all-community)
- [OAuth authorization](https://aisa.one/docs/api-reference/twitter/post_twitter-auth-twitter)
- [Media upload](https://aisa.one/docs/api-reference/twitter/post_twitter-upload-media)
- [Post creation](https://aisa.one/docs/api-reference/twitter/post_twitter-post-twitter)
- [Billing and quote semantics](https://aisa.one/docs/guides/pricing)

## Validation

```bash
python3 -m unittest discover -s tests -v
```

Tests use fixtures and mocked transport; they do not authorize accounts, upload
media, publish posts, or execute paid retrieval.
