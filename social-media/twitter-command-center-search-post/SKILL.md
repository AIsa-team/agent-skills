---
name: twitter-command-center-search-post
description: 'Searches and reads X (Twitter): profiles, timelines, mentions, followers, tweet search, trends, lists, communities, and Spaces. Publishes posts after the user completes OAuth in the browser. Use when the user asks about Twitter/X data, social listening, or posting without sharing account passwords.'
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  version: "1.0.1"
  aisa:
    emoji: 🐦
    requires:
      bins:
      - curl
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# AIsa Twitter Command Center 🐦

<!-- aisa-rules:start -->
## AIsa agent rules (shared)

<!-- Generated from _shared/aisa-rules.md by scripts/sync_shared_rules.py. Do not edit this block in place. -->

These rules apply to every AIsa-backed skill and are copied from https://aisa.one/llms.txt, the single authoritative agent rule source. When this block and the rest of this skill disagree, follow this block.

### Connect (MCP first)

Pick the first option that applies. Run the command yourself; the user only approves the browser sign-in.

- **A. Your client supports remote MCP and can open a browser (default).** Add a remote MCP server named `AIsa` with URL `https://mcp.aisa.one/mcp` (Streamable HTTP), using your client's own command or config file. Auth: browser OAuth, no key needed. In a chat app (Claude, ChatGPT), the user adds it as a custom connector in settings. If you cannot add the connector yourself (sandbox, permission denied), give the user the server name and URL above and wait. Do not fall back to another method.
- **B. Your client supports remote MCP but has no browser (CI, SSH, container).** Same endpoint, with the header `Authorization: Bearer $AISA_API_KEY` set in your client's MCP config instead of browser sign-in. If `AISA_API_KEY` is not set, ask the user to create a key at https://console.aisa.one/api-keys and set it in the environment; never ask them to paste it into chat. Never print, log, or commit the key.
- **C. The client has no MCP support.** Use the CLI: `npm install -g @aisa-one/cli && aisa login` (Node.js 18+). Guide: https://aisa.one/docs/get-started/cli.md
- **D. Calling AIsa over HTTP from your own code.** LLMs, OpenAI-compatible: `https://api.aisa.one/v1` (Gemini GenerateContent: `https://api.aisa.one/v1beta`). Data APIs: `https://api.aisa.one/apis/v1`. Auth: `Authorization: Bearer $AISA_API_KEY`. Exact paths and schemas: https://aisa.one/docs/api-reference

Direct HTTP (D) is a gated fallback, not the default. Gate (https://aisa.one/docs/get-started/cli.md#direct-http-fallback): "CLI and MCP are both unavailable, HTTP requests are supported, and a valid existing AIsa API key is already available." The curl and script examples in this skill exist for that fallback; when a connection exists, run the same operation through MCP (`search` → `batch_get_schema` → `batch_quote` → `batch_use`) or the CLI (`aisa search` → `aisa schema` → `aisa quote` → `aisa call`). Take tool names and arguments from `search` or `batch_get_schema`. Never invent them.

### Verify

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

**Twitter/X data access and automation for autonomous agents. Powered by AIsa.**

One API key. Full Twitter intelligence.

## What Can You Do?

### Monitor Influencers
```text
"Get Elon Musk's latest tweets and notify me of any AI-related posts"
```

### Track Trends
```text
"What's trending on Twitter worldwide right now?"
```

### Social Listening
```text
"Search for tweets mentioning our product and analyze sentiment"
```

### Competitor Intel
```text
"Monitor @anthropic and @GoogleAI - alert me on new announcements"
```

## Posting Workflows

This file does not define publishing logic.

If the user asks to send, publish, or reply, or quote on X/Twitter, handle that workflow with `./references/post_twitter.md`.

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## Core Capabilities

### Read Operations (No Login Required)

#### User Endpoints

```bash
# Get user info
curl "https://api.aisa.one/apis/v1/twitter/user/info?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user profile about (account country, verification, username changes)
curl "https://api.aisa.one/apis/v1/twitter/user_about?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Batch get user info by IDs
curl "https://api.aisa.one/apis/v1/twitter/user/batch_info_by_ids?userIds=44196397,123456" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user's latest tweets
curl "https://api.aisa.one/apis/v1/twitter/user/last_tweets?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user mentions
curl "https://api.aisa.one/apis/v1/twitter/user/mentions?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user followers
curl "https://api.aisa.one/apis/v1/twitter/user/followers?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user followings
curl "https://api.aisa.one/apis/v1/twitter/user/followings?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user verified followers (requires user_id, not userName)
curl "https://api.aisa.one/apis/v1/twitter/user/verifiedFollowers?user_id=44196397" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Check follow relationship between two users
curl "https://api.aisa.one/apis/v1/twitter/user/check_follow_relationship?source_user_name=elonmusk&target_user_name=BillGates" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Search users by keyword
curl "https://api.aisa.one/apis/v1/twitter/user/search?query=AI+researcher" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Tweet Endpoints

```bash
# Advanced tweet search (queryType is required: Latest or Top)
curl "https://api.aisa.one/apis/v1/twitter/tweet/advanced_search?query=AI+agents&queryType=Latest" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Search top tweets
curl "https://api.aisa.one/apis/v1/twitter/tweet/advanced_search?query=AI+agents&queryType=Top" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get tweets by IDs (comma-separated)
curl "https://api.aisa.one/apis/v1/twitter/tweets?tweet_ids=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get tweet replies
curl "https://api.aisa.one/apis/v1/twitter/tweet/replies?tweetId=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get tweet quotes
curl "https://api.aisa.one/apis/v1/twitter/tweet/quotes?tweetId=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get tweet retweeters
curl "https://api.aisa.one/apis/v1/twitter/tweet/retweeters?tweetId=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get tweet thread context (full conversation thread)
curl "https://api.aisa.one/apis/v1/twitter/tweet/thread_context?tweetId=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get article by tweet ID
curl "https://api.aisa.one/apis/v1/twitter/article?tweet_id=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Trends, Lists, Communities & Spaces

```bash
# Get trending topics (worldwide)
curl "https://api.aisa.one/apis/v1/twitter/trends?woeid=1" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get list members
curl "https://api.aisa.one/apis/v1/twitter/list/members?list_id=1585430245762441216" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get list followers
curl "https://api.aisa.one/apis/v1/twitter/list/followers?list_id=1585430245762441216" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get community info
curl "https://api.aisa.one/apis/v1/twitter/community/info?community_id=1708485837274263614" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get community members
curl "https://api.aisa.one/apis/v1/twitter/community/members?community_id=1708485837274263614" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get community moderators
curl "https://api.aisa.one/apis/v1/twitter/community/moderators?community_id=1708485837274263614" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get community tweets
curl "https://api.aisa.one/apis/v1/twitter/community/tweets?community_id=1708485837274263614" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Search tweets from all communities
curl "https://api.aisa.one/apis/v1/twitter/community/get_tweets_from_all_community?query=AI" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get Space detail
curl "https://api.aisa.one/apis/v1/twitter/spaces/detail?space_id=1dRJZlbLkjexB" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

## Python Client

```bash
# User operations
python3 scripts/twitter_client.py user-info --username elonmusk
python3 scripts/twitter_client.py user-about --username elonmusk
python3 scripts/twitter_client.py tweets --username elonmusk
python3 scripts/twitter_client.py mentions --username elonmusk
python3 scripts/twitter_client.py followers --username elonmusk
python3 scripts/twitter_client.py followings --username elonmusk
python3 scripts/twitter_client.py verified-followers --user-id 44196397
python3 scripts/twitter_client.py check-follow --source elonmusk --target BillGates

# Search & discovery
python3 scripts/twitter_client.py search --query "AI agents"
python3 scripts/twitter_client.py search --query "AI agents" --type Top
python3 scripts/twitter_client.py user-search --query "AI researcher"
python3 scripts/twitter_client.py trends --woeid 1

# Tweet operations
python3 scripts/twitter_client.py detail --tweet-ids 1895096451033985024
python3 scripts/twitter_client.py replies --tweet-id 1895096451033985024
python3 scripts/twitter_client.py quotes --tweet-id 1895096451033985024
python3 scripts/twitter_client.py retweeters --tweet-id 1895096451033985024
python3 scripts/twitter_client.py thread --tweet-id 1895096451033985024

# List operations
python3 scripts/twitter_client.py list-members --list-id 1585430245762441216
python3 scripts/twitter_client.py list-followers --list-id 1585430245762441216

# Community operations
python3 scripts/twitter_client.py community-info --community-id 1708485837274263614
python3 scripts/twitter_client.py community-members --community-id 1708485837274263614
python3 scripts/twitter_client.py community-tweets --community-id 1708485837274263614
python3 scripts/twitter_client.py community-search --query "AI"
```

## API Endpoints Reference

### Read Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/twitter/user/info` | Get user profile | `userName` |
| `/twitter/user_about` | Get user profile about | `userName` |
| `/twitter/user/batch_info_by_ids` | Batch get users by IDs | `userIds` |
| `/twitter/user/last_tweets` | Get user's recent tweets | `userName`, `cursor` |
| `/twitter/user/mentions` | Get user mentions | `userName`, `cursor` |
| `/twitter/user/followers` | Get user followers | `userName`, `cursor` |
| `/twitter/user/followings` | Get user followings | `userName`, `cursor` |
| `/twitter/user/verifiedFollowers` | Get verified followers | `user_id`, `cursor` |
| `/twitter/user/check_follow_relationship` | Check follow relationship | `source_user_name`, `target_user_name` |
| `/twitter/user/search` | Search users by keyword | `query`, `cursor` |
| `/twitter/tweet/advanced_search` | Advanced tweet search | `query`, `queryType` (Latest/Top), `cursor` |
| `/twitter/tweets` | Get tweets by IDs | `tweet_ids` (comma-separated) |
| `/twitter/tweet/replies` | Get tweet replies | `tweetId`, `cursor` |
| `/twitter/tweet/quotes` | Get tweet quotes | `tweetId`, `cursor` |
| `/twitter/tweet/retweeters` | Get tweet retweeters | `tweetId`, `cursor` |
| `/twitter/tweet/thread_context` | Get tweet thread context | `tweetId`, `cursor` |
| `/twitter/article` | Get article by tweet | `tweet_id` |
| `/twitter/trends` | Get trending topics | `woeid` (1=worldwide) |
| `/twitter/list/members` | Get list members | `list_id`, `cursor` |
| `/twitter/list/followers` | Get list followers | `list_id`, `cursor` |
| `/twitter/community/info` | Get community info | `community_id` |
| `/twitter/community/members` | Get community members | `community_id`, `cursor` |
| `/twitter/community/moderators` | Get community moderators | `community_id`, `cursor` |
| `/twitter/community/tweets` | Get community tweets | `community_id`, `cursor` |
| `/twitter/community/get_tweets_from_all_community` | Search all community tweets | `query`, `cursor` |
| `/twitter/spaces/detail` | Get Space detail | `space_id` |

## Pricing

| API | Cost |
|-----|------|
| Twitter read query | ~$0.0004 |

The settled cost of each call is returned in the `X-AISA-Customer-Cost-Micros-USD` response header (integer micro-USD; 1 USD = 1,000,000). Do not look for a cost field in the response body.

## Get Started

1. Sign up at [aisa.one](https://aisa.one)
2. Get your API key
3. Add credits (pay-as-you-go)
4. Set environment variable: `export AISA_API_KEY="your-key"`

## Full API Reference

See [API Reference](https://docs.aisa.one/reference/) for complete endpoint documentation.
