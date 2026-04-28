# OpenClaw Twitter Engagement

Like, unlike, follow, and unfollow X/Twitter content through the relay-backed runtime.

This workflow is for engagement actions, not publishing. If the user asks to send, post, reply, or quote on X/Twitter, use `./references/post_twitter.md`.

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## Python Client

```bash
python3 {baseDir}/scripts/twitter_engagement_client.py list-tweets --user "@elonmusk" --limit 10
python3 {baseDir}/scripts/twitter_engagement_client.py like-latest --user "@elonmusk"
python3 {baseDir}/scripts/twitter_engagement_client.py unlike-latest --user "@elonmusk"
python3 {baseDir}/scripts/twitter_engagement_client.py follow-user --user "@elonmusk"
python3 {baseDir}/scripts/twitter_engagement_client.py unfollow-user --user "@elonmusk"
```

## Agent Instructions

When the user asks to like, unlike, follow, or unfollow on X/Twitter:

1. Do not ask the user to manually paste tweet links or IDs.
2. If the user first asked to query tweets, keep the returned `tweets[]` structure in OpenClaw context.
3. Map ordinal follow-up requests to remembered tweet or author context.
4. If multiple user candidates match a natural-language name, stop and ask the user to confirm the account.
5. Do not claim the action succeeded unless the relay request actually returns success.

## Guardrails

- Do not guess a target account when multiple candidates are returned.
- Do not fabricate tweet IDs or user IDs from natural language.
- Do not use local file-based conversation memory for this workflow; rely on OpenClaw context only.
- Relay endpoints for this workflow are `/like_twitter`, `/unlike_twitter`, `/follow_twitter`, and `/unfollow_twitter`.

## ClawHub Suspicious Review Notes

- Engagement actions are relay-based and go to `api.aisa.one`.
- Required secret: `AISA_API_KEY`.
- This workflow does not use passwords, browser cookies, cache sync, or home-directory persistence.
