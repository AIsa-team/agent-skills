---
name: youtube-search
description: 'YouTube Search API via AIsa unified endpoint. Search YouTube videos, channels, and playlists with a single AIsa API key — no Google API key or OAuth required. Use this skill when users want to search YouTube content. For other AIsa capabilities (LLM, financial data, Twitter, web search), see the aisa-core skill. Use when: the user needs YouTube search, trend discovery, channel research, or SERP analysis.'
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: 🎬
    requires:
      bins:
      - curl
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# YouTube Search (via AIsa)

Search YouTube videos, channels, and playlists through AIsa's unified API. No Google API key or OAuth setup needed — just your AIsa API key.

## Quick Start

```bash
# Search for videos (using requests — recommended)
python <<'EOF'
import os, json, requests
results = requests.get(
    'https://api.aisa.one/apis/v1/youtube/search',
    headers={'Authorization': f'Bearer {os.environ["AISA_API_KEY"]}'},
    params={'engine': 'youtube', 'q': 'coding tutorial'}
).json()
print(json.dumps(results, indent=2))
EOF
```

## Base URL

```
https://api.aisa.one/apis/v1/youtube/search
```

All YouTube search requests go through this single endpoint. AIsa handles authentication with the underlying YouTube data source — you only need your AIsa API key.

## Authentication

All requests require the AIsa API key in the Authorization header:

```
Authorization: Bearer $AISA_API_KEY
```

**Environment Variable:** Set your API key as `AISA_API_KEY`:

```bash
export AISA_API_KEY="YOUR_AISA_API_KEY"
```

### Getting Your API Key

1. Sign in or create an account at [AIsa Marketplace](https://marketplace.aisa.one)
2. Navigate to your Dashboard
3. Copy your API key

## API Reference

### YouTube Search

```bash
GET /apis/v1/youtube/search
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `engine` | string | Yes | Must be `youtube` |
| `q` | string | Yes | Search query (same syntax as YouTube search box) |
| `sp` | string | No | YouTube filter token for pagination or advanced filters |
| `gl` | string | No | Country code for localized results (e.g., `us`, `jp`, `gb`). Not all country codes are supported — see notes below |
| `hl` | string | No | Interface language (e.g., `en`, `zh`, `ja`) |

#### Example: Basic Search

```bash
curl -s -X GET "https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=machine+learning+tutorial" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Example: Search with Country & Language

```bash
curl -s -X GET "https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=AI+news&gl=us&hl=en" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Example: Pagination with `sp` Token

```bash
# Use the sp token from a previous response to get the next page
curl -s -X GET "https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=python+tutorial&sp=EgIQAQ%3D%3D" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Response

The API returns structured YouTube search results including video metadata, channel info, thumbnails, and pagination tokens.

**Note:** The response structure may vary by query language. English queries typically return results in the `videos` array. Some non-English queries may return results grouped in a `sections` array instead. Always check for both fields.

```json
{
  "search_metadata": {
    "status": "Success",
    "total_time_taken": 1.2
  },
  "search_parameters": {
    "engine": "youtube",
    "q": "machine learning tutorial"
  },
  "next_page_token": "CBQQABoCEgA%3D",
  "videos": [
    {
      "position_on_page": 1,
      "title": "Machine Learning Full Course for Beginners",
      "link": "https://www.youtube.com/watch?v=abc123xyz",
      "channel": {
        "name": "Tech Academy",
        "link": "https://www.youtube.com/channel/UCxyz123",
        "thumbnail": "https://yt3.ggpht.com/..."
      },
      "published_date": "2 months ago",
      "views": 1500000,
      "length": "3:45:20",
      "description": "Complete machine learning tutorial...",
      "thumbnail": {
        "static": "https://i.ytimg.com/vi/abc123xyz/hq720.jpg",
        "rich": "https://i.ytimg.com/an_webp/abc123xyz/mqdefault_6s.webp"
      }
    }
  ]
}
```

**Alternate response structure (non-English / some queries):**

Some queries return results grouped in `sections` instead of a flat `videos` array:

```json
{
  "sections": [
    {
      "title": "搜索结果",
      "videos": [
        {
          "title": "编程教程...",
          "link": "https://www.youtube.com/watch?v=...",
          ...
        }
      ]
    }
  ]
}
```

**Parsing both formats:**

```python
# Handle both response structures
videos = results.get('videos', [])
if not videos and 'sections' in results:
    for section in results['sections']:
        videos.extend(section.get('videos', []))
```

### Advanced Search Tips

YouTube's `q` parameter supports the same search syntax as the YouTube search box:

| Search Syntax | Description | Example |
|---------------|-------------|---------|
| Basic keywords | Standard search | `q=python tutorial` |
| Exact phrase | Quote for exact match | `q="machine learning basics"` |
| Channel filter | Search within a channel | `q=channel:GoogleDevelopers python` |
| Duration hint | Combine with keywords | `q=python tutorial long` |

### Using the `sp` Filter Token

The `sp` parameter accepts YouTube's encoded filter tokens. Common values:

| Filter | `sp` Value | Description |
|--------|-----------|-------------|
| Videos only | `EgIQAQ%3D%3D` | Filter to video results only |
| Channels only | `EgIQAg%3D%3D` | Filter to channel results only |
| Playlists only | `EgIQAw%3D%3D` | Filter to playlist results only |
| Live now | `EgJAAQ%3D%3D` | Currently live streams |
| This week | `EgIIAw%3D%3D` | Uploaded this week |
| This month | `EgIIBA%3D%3D` | Uploaded this month |
| Short (<4 min) | `EgIYAQ%3D%3D` | Short duration videos |
| Long (>20 min) | `EgIYAg%3D%3D` | Long duration videos |

You can also obtain `sp` tokens from the `next_page_token` field in previous API responses for pagination.

#### Pagination

Use the `next_page_token` from a response to fetch the next page of results:

```python
# First page
results = requests.get(
    'https://api.aisa.one/apis/v1/youtube/search',
    headers=headers,
    params={'engine': 'youtube', 'q': 'python tutorial'}
).json()

# Get next page token
next_token = results.get('next_page_token')
if next_token:
    page2 = requests.get(
        'https://api.aisa.one/apis/v1/youtube/search',
        headers=headers,
        params={'engine': 'youtube', 'q': 'python tutorial', 'sp': next_token}
    ).json()
```

## Code Examples

### JavaScript

```javascript
const headers = {
  'Authorization': `Bearer ${process.env.AISA_API_KEY}`
};

// Basic YouTube search
const results = await fetch(
  'https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=AI+agents+tutorial',
  { headers }
).then(r => r.json());

console.log(results.videos);

// Search with filters
const filtered = await fetch(
  'https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=deep+learning&gl=us&hl=en&sp=EgIQAQ%3D%3D',
  { headers }
).then(r => r.json());
```

### Python

```python
import os
import requests

headers = {'Authorization': f'Bearer {os.environ["AISA_API_KEY"]}'}

# Basic YouTube search
results = requests.get(
    'https://api.aisa.one/apis/v1/youtube/search',
    headers=headers,
    params={'engine': 'youtube', 'q': 'AI agents tutorial'}
).json()

for video in results.get('videos', []):
    print(f"{video['title']} - {video.get('views', 'N/A')} views")

# Search with country and language
results_jp = requests.get(
    'https://api.aisa.one/apis/v1/youtube/search',
    headers=headers,
    params={'engine': 'youtube', 'q': 'プログラミング', 'gl': 'jp', 'hl': 'ja'}
).json()
```

### Python (urllib, no dependencies)

> **Note:** `urllib` may encounter 403 errors due to its default User-Agent. Using `requests` (above) is recommended. If you must use `urllib`, always set a custom User-Agent header.

```python
import urllib.request, urllib.parse, os, json

def youtube_search(query, gl=None, hl=None, sp=None):
    """Search YouTube via AIsa API."""
    params = {'engine': 'youtube', 'q': query}
    if gl: params['gl'] = gl
    if hl: params['hl'] = hl
    if sp: params['sp'] = sp
    
    url = f'https://api.aisa.one/apis/v1/youtube/search?{urllib.parse.urlencode(params)}'
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {os.environ["AISA_API_KEY"]}')
    req.add_header('User-Agent', 'AIsa-Skill/1.0')
    return json.load(urllib.request.urlopen(req))

# Search
results = youtube_search('OpenClaw tutorial', gl='us', hl='en')

# Handle both response formats
videos = results.get('videos', [])
if not videos and 'sections' in results:
    for section in results['sections']:
        videos.extend(section.get('videos', []))

print(json.dumps(videos[:3], indent=2))
```

## Combining with Other AIsa APIs

One of the key advantages of AIsa is the **unified API key**. Use the same `AISA_API_KEY` to combine YouTube search with other AIsa capabilities:

### YouTube Search + LLM Summary

```python
import os, requests, json

headers = {'Authorization': f'Bearer {os.environ["AISA_API_KEY"]}'}

# 1. Search YouTube
yt_results = requests.get(
    'https://api.aisa.one/apis/v1/youtube/search',
    headers=headers,
    params={'engine': 'youtube', 'q': 'latest AI developments 2026'}
).json()

# 2. Summarize with LLM (same API key!)
video_titles = [v['title'] for v in yt_results.get('videos', [])[:5]]
summary = requests.post(
    'https://api.aisa.one/v1/chat/completions',
    headers={**headers, 'Content-Type': 'application/json'},
    json={
        'model': 'qwen3-flash',
        'messages': [
            {'role': 'user', 'content': f'Summarize the trending AI topics based on these YouTube videos: {json.dumps(video_titles)}'}
        ]
    }
).json()

print(summary['choices'][0]['message']['content'])
```

### YouTube Search + Web Search

```python
# Search both YouTube and the web for comprehensive research
yt_results = requests.get(
    'https://api.aisa.one/apis/v1/youtube/search',
    headers=headers,
    params={'engine': 'youtube', 'q': 'AI agent frameworks 2026'}
).json()

web_results = requests.get(
    'https://api.aisa.one/apis/v1/search/smart',
    headers=headers,
    params={'q': 'AI agent frameworks 2026'}
).json()
```

## Notes

- All requests are **pay-per-use** through your AIsa balance — no separate YouTube API quota management
- The `engine` parameter must always be set to `youtube`
- Video URLs follow the format `https://www.youtube.com/watch?v={videoId}`
- Channel URLs follow the format `https://www.youtube.com/channel/{channelId}`
- Use `next_page_token` from previous responses as the `sp` value for pagination
- The `gl` (country) parameter does **not** support all ISO country codes. Known unsupported values include `cn` (China). If you get `Unsupported value` errors, try omitting `gl` or use a different country code
- Non-English queries may return results in a `sections` array instead of a flat `videos` array — always handle both formats
- IMPORTANT: Python `urllib` may return 403 errors due to its default User-Agent. Use the `requests` library instead, or add a custom `User-Agent` header
- IMPORTANT: When using curl commands, ensure environment variables like `$AISA_API_KEY` are properly expanded
- IMPORTANT: When piping curl output to `jq`, use `-s` flag and ensure the API key is set

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Successful search response |
| 400 | Invalid request parameters (missing `engine` or `q`) |
| 401 | Unauthorized — invalid or missing AIsa API key |
| 429 | Rate limited |
| 500 | Internal server error |

### Troubleshooting: API Key Issues

1. Check that the `AISA_API_KEY` environment variable is set:

```bash
echo $AISA_API_KEY
```

2. Verify the API key works with a simple test:

```bash
python <<'EOF'
import os, json, requests
try:
    result = requests.get(
        'https://api.aisa.one/apis/v1/youtube/search',
        headers={'Authorization': f'Bearer {os.environ["AISA_API_KEY"]}'},
        params={'engine': 'youtube', 'q': 'test'}
    ).json()
    videos = result.get('videos', [])
    print(f"✅ API key is valid. Results: {len(videos)} videos found")
except Exception as e:
    print(f"❌ Error: {e}")
EOF
```

### Troubleshooting: No Results

1. Verify your query is not empty
2. Try a broader search term
3. If using `gl`, verify the country code is supported — not all ISO codes work (e.g., `cn` is unsupported). Try omitting `gl` to test
4. Ensure `engine=youtube` is included in every request
5. Check if results are in `sections` instead of `videos` (common for non-English queries)

## Resources

- [AIsa API Documentation](https://docs.aisa.one)
- [AIsa Dashboard / Marketplace](https://marketplace.aisa.one)
- [YouTube Search API Reference](https://docs.aisa.one/reference/get_youtube-search)
- [AIsa Smart Search API](https://docs.aisa.one/reference/get_search-smart)
- [AIsa Chat Completions API](https://docs.aisa.one/reference/createchatcompletion)
- [ClawHub Skills](https://clawhub.ai)
