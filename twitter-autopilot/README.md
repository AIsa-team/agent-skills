# Twitter Autopilot 🐦

Twitter/X intelligence and automation for autonomous agents. Powered by AIsa.

This skill provides comprehensive capabilities to **read, search, engage, write, and post (text & media)** on Twitter/X.

## Features

- **Read & Search**: Access user info, tweets, advanced search, trends, followers, lists, communities, and Spaces without requiring user login.
- **Engagement via Relay**: Like/unlike tweets and follow/unfollow users through the local OAuth relay service.
- **Write & Post (OAuth)**: Publish text, images, and videos, create threads, and quote/reply to tweets securely via user OAuth authorization.

## Installation

```bash
export AISA_API_KEY="your-key"
```

## Quick Start

### Read & Search
```bash
# Get user info and search tweets
python scripts/twitter_client.py user-info --username elonmusk
python scripts/twitter_client.py search --query "AI agents"
python scripts/twitter_client.py trends
```

### Post & Write (Requires OAuth)
```bash
# Publish a text post
python scripts/twitter_oauth_client.py post --text "Hello from AIsa!"

# Publish a post with media
python scripts/twitter_oauth_client.py post --text "Check out this image" --media-file ./photo.png
```

### Engagement (Requires OAuth Relay)
```bash
# Like the latest tweet from a user
python scripts/twitter_engagement_client.py like-latest --user "@elonmusk"

# Query recent tweets for indexed follow-up actions
python scripts/twitter_engagement_client.py list-tweets --user "@elonmusk" --limit 10

# Follow a user
python scripts/twitter_engagement_client.py follow-user --user "@elonmusk"
```

> **Note**: For detailed engagement workflows, please see [`./references/engage_twitter.md`](./references/engage_twitter.md). For publishing, authorization, and multi-chunk threading, see [`./references/post_twitter.md`](./references/post_twitter.md).

## Get API Key

Sign up at [aisa.one](https://aisa.one)

## Links

- [AIsa](https://aisa.one)
- [API Reference](https://docs.aisa.one/reference/)
