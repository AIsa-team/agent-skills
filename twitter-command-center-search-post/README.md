# AIsa Twitter Command Center 🐦

Twitter/X intelligence and automation for autonomous agents. Powered by AIsa.

This skill provides comprehensive capabilities to **read, search, write, and post (text & media)** to Twitter/X.

## Features

- **Read & Search**: Access user info, tweets, advanced search, trends, followers, lists, communities, and Spaces without requiring user login.
- **Write & Post (OAuth)**: Publish text, images, and videos, create threads, and quote/reply to tweets securely via user OAuth authorization.

## Setup

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

> **Note**: For detailed posting workflows, authorization, and multi-chunk threading, please see [`./references/post_twitter.md`](./references/post_twitter.md).

## Get API Key

Sign up at [aisa.one](https://aisa.one)

## Links

- Cross-platform mother skill for AgentSkills-compatible runtimes
- [API Reference](https://docs.aisa.one/reference/)
