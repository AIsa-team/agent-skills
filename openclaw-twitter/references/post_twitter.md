# OpenClaw Twitter OAuth

OAuth-based X/Twitter posting for autonomous agents through the AISA relay.

## When to use

- The user wants to publish, reply, or quote on X/Twitter.
- The user has approved OAuth or is ready to receive an authorization link.
- The user attached local image or video files that should be uploaded as part of the post.

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## Python Client

```bash
# Show current client configuration
python3 {baseDir}/scripts/twitter_oauth_client.py status

# Request an authorization link
python3 {baseDir}/scripts/twitter_oauth_client.py authorize

# Optional: open the authorization link in the default browser
python3 {baseDir}/scripts/twitter_oauth_client.py authorize --open-browser

# Publish a text post
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Hello from Twitter OAuth"

# Publish an image-only post
python3 {baseDir}/scripts/twitter_oauth_client.py post --media-file ./workspace/photo.png

# Publish a video-only post
python3 {baseDir}/scripts/twitter_oauth_client.py post --media-file ./workspace/demo.mp4

# Publish an image with text
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Shipping day." --media-file ./workspace/photo.png

# Publish a video with text
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Demo clip" --media-file ./workspace/demo.mp4

# Publish a threaded post using reply relationships between chunks
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Hello from Twitter OAuth" --type reply

# Quote another tweet and include its link in the new post
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "My take on this:" --type quote --quote-tweet-url "https://x.com/example/status/1888888888888888888"

# Start the thread from a specific external tweet
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Reply content" --type reply --in-reply-to-tweet-id "1888888888888888888"
```

## Core Behavior

Recommended flow:

1. Try to publish the requested content first.
2. If posting fails because access has not been authorized yet, return an authorization link.
3. After the user completes authorization, publish using the authorized account.
4. Use `--open-browser` only when the user explicitly wants local browser launch instead of receiving the URL.

### OpenClaw Attachment Flow

When the user drops image or video files into OpenClaw:

1. OpenClaw stores the attachment in the local workspace and provides the workspace file path to the skill.
2. The skill passes that local path through `--media-file <workspace_path>`.
3. The Python client reads the local file and sends it to the relay backend as `multipart/form-data`.
4. The relay backend uploads the media to Twitter/X and then publishes the tweet.
5. The skill returns the final publish result, including the tweet link or tweet ID when available.

## Agent Instructions

When the user asks to publish content to X/Twitter:

1. Check whether `AISA_API_KEY` is configured.
2. Try `post` first when the user intent is to publish content.
3. If the user attached workspace files, pass each image or video path with `--media-file`.
4. If the user explicitly wants to quote another tweet, require the tweet URL and pass it with `--quote-tweet-url`.
5. If posting indicates that authorization is required, run `authorize` and return the approval link.
6. Do not claim the post succeeded until the publish step actually succeeds.

## Guardrails

- Do not ask the user for their Twitter password.
- Do not use cookie-based login or proxy-based login unless the user explicitly asks for legacy behavior.
- Do not default to `--open-browser`; return the authorization link unless the user explicitly wants local browser launch.
- Do not invent remote URLs for attachments; always use the provided local workspace file path with `--media-file`.
- If the user provides a single image attachment, do not duplicate it or turn it into a multi-image post.
- If the user did not provide tweet text, do not generate or attach any caption text.

## ClawHub Suspicious Review Notes

- Posting, OAuth, and approved media uploads are relay-based and go to `api.aisa.one`.
- Required secret: `AISA_API_KEY`.
- This workflow does not use passwords, browser cookies, cache sync, or home-directory persistence.
