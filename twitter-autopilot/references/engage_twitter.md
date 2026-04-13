# Twitter Engagement

**Like, unlike, follow, and unfollow X/Twitter content through the local relay service.**

This workflow is for engagement actions, not publishing.

If the user asks to send, post, reply, or quote on X/Twitter, use `./references/post_twitter.md`.

## What This Workflow Supports

### Like or Unlike the Latest Tweet
```text
Like Elon Musk's latest tweet
Remove the like from @AIsa's latest tweet
```

### Query Recent Tweets Then Operate by Index
```text
Show Elon Musk's latest 10 tweets
Like the second one
Unlike the fifth one
```

### Follow or Unfollow a User
```text
Follow Elon Musk
Unfollow @AIsa
Follow the author of the tweet we just looked at
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## Python Client

```bash
# List tweets for follow-up actions
python3 {baseDir}/scripts/twitter_engagement_client.py list-tweets --user "@elonmusk" --limit 10

# Like or unlike the latest tweet
python3 {baseDir}/scripts/twitter_engagement_client.py like-latest --user "@elonmusk"
python3 {baseDir}/scripts/twitter_engagement_client.py unlike-latest --user "@elonmusk"

# Like or unlike a tweet ID already resolved by agent context
python3 {baseDir}/scripts/twitter_engagement_client.py like-tweet --tweet-id "2040901249466593766" --label "Tweet #2" --username "elonmusk"
python3 {baseDir}/scripts/twitter_engagement_client.py unlike-tweet --tweet-id "2040901249466593766" --label "Tweet #5"

# Follow or unfollow a user
python3 {baseDir}/scripts/twitter_engagement_client.py follow-user --user "@elonmusk"
python3 {baseDir}/scripts/twitter_engagement_client.py unfollow-user --user "@elonmusk"

# Follow or unfollow a user ID already resolved by agent context
python3 {baseDir}/scripts/twitter_engagement_client.py follow-user-id --target-user-id "44196397" --username "elonmusk"
python3 {baseDir}/scripts/twitter_engagement_client.py unfollow-user-id --target-user-id "44196397" --username "elonmusk"
```

## Agent Instructions

When the user asks to like, unlike, follow, or unfollow on X/Twitter:

1. Do not ask the user for tweet IDs, tweet links, or user IDs.
2. If the user specifies a direct account such as `@elonmusk`, call the `--user` based command.
3. If the user asks for the latest tweet, use `like-latest` or `unlike-latest`.
4. If the user first asked to query tweets, keep the returned `tweets[]` structure in agent context.
5. For follow-up instructions like `Like the second one`, map the ordinal to the remembered `tweets[].index`, then call `like-tweet` or `unlike-tweet` with the resolved `tweet_id`.
6. For follow-up instructions like `Follow this author`, use the remembered tweet author's `author_id`, then call `follow-user-id` or `unfollow-user-id`.
7. If multiple user candidates match a natural-language name, stop and ask the user to confirm the account.
8. If the current conversation does not contain the required tweet or author context, tell the user you need a prior tweet query or a clearer target first.
9. Convert script results into natural conversational English for the final user response.

## Guardrails

- Do not ask the user to manually paste tweet links or IDs.
- Do not guess a target account when multiple candidates are returned.
- Do not fabricate tweet IDs or user IDs from natural language.
- Do not use local file-based conversation memory for this workflow; rely on agent context only.
- Do not claim the action succeeded unless the relay request actually returns success.
- Relay endpoints for this workflow are `/like_twitter`, `/unlike_twitter`, `/follow_twitter`, and `/unfollow_twitter`.
