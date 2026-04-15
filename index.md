# AIsa Agent Skills Index

这份索引面向正式发布仓库：

- Repository: <https://github.com/AIsa-team/agent-skills>
- Branch: `agentskills`
- Branch URL: <https://github.com/AIsa-team/agent-skills/tree/agentskills>

当前整理完成的 skills 如下。

## Twitter / X

### `aisa-twitter-command-center`

- GitHub: <https://github.com/AIsa-team/agent-skills/tree/agentskills/aisa-twitter-command-center>
- Summary: Search X/Twitter profiles, tweets, trends, lists, communities, and Spaces through the AIsa relay, then support approved posting workflows with OAuth.
- Includes:
  - `scripts/twitter_client.py`
  - `scripts/twitter_oauth_client.py`
  - `references/post_twitter.md`

### `aisa-twitter-api`

- GitHub: <https://github.com/AIsa-team/agent-skills/tree/agentskills/aisa-twitter-api>
- Summary: Search X/Twitter profiles, tweets, trends, lists, communities, and Spaces through the AIsa relay, then support approved posting workflows with OAuth.
- Includes:
  - `scripts/twitter_client.py`
  - `scripts/twitter_oauth_client.py`
  - `references/post_twitter.md`

### `aisa-twitter-post-engage`

- GitHub: <https://github.com/AIsa-team/agent-skills/tree/agentskills/aisa-twitter-post-engage>
- Summary: Search X/Twitter profiles, tweets, trends, and approved engagement actions through the AIsa relay, including posting, likes, follows, and related workflows.
- Includes:
  - `scripts/twitter_client.py`
  - `scripts/twitter_oauth_client.py`
  - `scripts/twitter_engagement_client.py`
  - `references/post_twitter.md`
  - `references/engage_twitter.md`

### `aisa-twitter-engagement-suite`

- GitHub: <https://github.com/AIsa-team/agent-skills/tree/agentskills/aisa-twitter-engagement-suite>
- Summary: Search X/Twitter profiles, tweets, trends, and approved engagement actions through the AIsa relay, with a bundled engagement workflow suite.
- Includes:
  - `scripts/twitter_client.py`
  - `scripts/twitter_oauth_client.py`
  - `scripts/twitter_engagement_client.py`
  - `references/post_twitter.md`
  - `references/engage_twitter.md`

### `x-intelligence-automation`

- GitHub: <https://github.com/AIsa-team/agent-skills/tree/agentskills/x-intelligence-automation>
- Summary: Search X/Twitter profiles, tweets, trends, and approved engagement actions through the AIsa relay, packaged under the X Intelligence Automation brand.
- Includes:
  - `scripts/twitter_client.py`
  - `scripts/twitter_oauth_client.py`
  - `scripts/twitter_engagement_client.py`
  - `references/post_twitter.md`
  - `references/engage_twitter.md`

## YouTube

### `aisa-youtube-search`

- GitHub: <https://github.com/AIsa-team/agent-skills/tree/agentskills/aisa-youtube-search>
- Summary: Search YouTube videos, channels, and playlists through the AIsa YouTube relay with one API key.
- Includes:
  - `SKILL.md`
  - `README.md`
  - `LICENSE.txt`

### `aisa-youtube-serp-scout`

- GitHub: <https://github.com/AIsa-team/agent-skills/tree/agentskills/aisa-youtube-serp-scout>
- Summary: Search YouTube videos, channels, and trends through the AIsa YouTube SERP client for content research, competitor tracking, and trend discovery.
- Includes:
  - `scripts/youtube_client.py`
  - `SKILL.md`
  - `README.md`

## Recommended Publish Order

1. `aisa-twitter-command-center`
2. `aisa-twitter-post-engage`
3. `aisa-youtube-search`
4. `aisa-youtube-serp-scout`
5. `aisa-twitter-api`
6. `aisa-twitter-engagement-suite`
7. `x-intelligence-automation`

## Notes

- `aisa-twitter-command-center` 可以作为 Twitter 主推母版。
- `aisa-twitter-post-engage` 是能力更完整的读写一体版。
- `aisa-twitter-api` 与 `aisa-twitter-command-center` 能力接近，后续可以考虑收敛。
- `aisa-twitter-engagement-suite` 与 `x-intelligence-automation` 更适合作为品牌或渠道变体。
