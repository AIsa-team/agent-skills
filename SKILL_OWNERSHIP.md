# Skill maintenance ownership

The `owner` field identifies the maintenance contact, not an author credit.
These initial assignments implement the contributor mapping reviewed in PR #55:
21 skills have individual contacts and 25 remain explicitly `unassigned`.

Evidence comes from the pre-migration main history, following file renames and
checking GitHub commit attribution. For older skills, restored paths and derived
variants can trace to a predecessor; that evidence does not establish current
ownership by itself. The individual contacts were selected from that history for
this PR and should be updated when the team changes responsibility. Existing
third-party attribution is preserved.

The other 25 skills entered through the [bulk catalog import][bulk-import],
with subsequent catalog restoration by Jing Li (`@lijing-22`). Importing or
restoring a catalog does not establish maintenance ownership for every skill.
`@xiaofengxyz` and `@lijing-22` are contacts for resolving these assignments.
The monitor flags unassigned ownership even when the skill is verified current.

| Skill | Maintenance owner | Historical evidence |
|---|---|---|
| `ai-models/aisa-provider` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `ai-models/cn-llm` | @chaimengphp | [Historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/cb1015522ff7f9cd983dc14c44ae87e9b1ac9670) |
| `ai-models/llm-router` | @chaimengphp | [Historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/cb1015522ff7f9cd983dc14c44ae87e9b1ac9670) |
| `e-commerce/e-commerce-content-studio` | @chaimengphp | Replaces `creative/media-gen`; [historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/49ebd76ab3e37f54cd562da7309e428efbacc729) |
| `e-commerce/product-selection` | unassigned | New skill; maintenance responsibility not yet assigned |
| `e-commerce/product-tracking` | unassigned | New skill; maintenance responsibility not yet assigned |
| `financial/crypto-market-data` | @karensheng | [Introduction](https://github.com/AIsa-team/agent-skills/commit/2d3ebb9df897f7b095cf4c667c82461daed19008) |
| `financial/market` | @chaimengphp | [Historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/49ebd76ab3e37f54cd562da7309e428efbacc729) |
| `financial/marketpulse` | @chaimengphp | [Historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/49ebd76ab3e37f54cd562da7309e428efbacc729) |
| `financial/prediction-market-arbitrage` | @karensheng | [Historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/624084ef9b7366adefdeb74cda074551cb115280) |
| `financial/prediction-market-arbitrage-zh` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `financial/prediction-market-data` | @karensheng | [Historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/4a154c3354daf8de90a915b85c8e813d2c6064ea) |
| `financial/prediction-market-data-zh` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `financial/stock-analysis` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `financial/stock-dividend` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `financial/stock-hot` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `financial/stock-portfolio` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `financial/stock-rumors` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `financial/stock-watchlist` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `financial/trend-forecast` | @drowecode | [Introduction](https://github.com/AIsa-team/agent-skills/commit/9b25a213fb229324d487469c7a42467847178c92) |
| `financial/us-stock-analyst` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `marketing/article-seo-geo-review` | @zhenlonghe | [Introduction](https://github.com/AIsa-team/agent-skills/commit/83e995b29d4d53321c7fe9920b15b9422aee37d2) |
| `marketing/creator-marketing` | @fatflowers | [Introduction](https://github.com/AIsa-team/agent-skills/commit/205a8492dd3ad093f5779ab384889b3dae1cfc89) |
| `marketing/kol-creator-discovery` | @lijing-22 | [Introduction](https://github.com/AIsa-team/agent-skills/commit/ffbe6da3ea977c8cd1419052ab3a9c86ea283aa9) |
| `marketing/seo-keyword-research` | @lijing-22 | [Introduction](https://github.com/AIsa-team/agent-skills/commit/21b25b978205686d8fc87d6c5354a53cf6452f6c) |
| `marketing/use-similarweb` | @lhymmEU | [Introduction](https://github.com/AIsa-team/agent-skills/commit/9813811e39a8749bf38c859134c2b9bf1a3259ea) |
| `platform/aisa` | @eddiearc | [Introduction](https://github.com/AIsa-team/agent-skills/commit/6dcb21159a551e8c6cb0c509ca67627c5b69324a) |
| `search-research/aisa-tavily` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `search-research/last30days` | @karensheng | [Introduction](https://github.com/AIsa-team/agent-skills/commit/ee4a528fa40288ba4773195e2a78da637ad95a4b) |
| `search-research/last30days-zh` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `search-research/multi-search` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `search-research/multi-source-search` | @chaimengphp | [Historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/49ebd76ab3e37f54cd562da7309e428efbacc729) |
| `search-research/perplexity-research` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `search-research/perplexity-search` | @chaimengphp | [Historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/aded5339be4ac7d32cef7b1082370a40f769ecbc) |
| `search-research/scholar-search` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `search-research/smart-search` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `search-research/tavily-extract` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `search-research/tavily-search` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `search-research/web-search` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `social-media/aisa-twitter-api` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `social-media/aisa-twitter-command-center` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `social-media/aisa-twitter-post-engage` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `social-media/aisa-youtube-search` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `social-media/twitter-autopilot` | @chaimengphp | [Historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/49ebd76ab3e37f54cd562da7309e428efbacc729) |
| `social-media/twitter-command-center-search-post` | @chaimengphp | [Historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/49ebd76ab3e37f54cd562da7309e428efbacc729) |
| `social-media/x-intelligence-automation` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `social-media/youtube-search` | unassigned | [Bulk import][bulk-import]; individual owner unknown |
| `social-media/youtube-serp` | @chaimengphp | [Historical skill or predecessor](https://github.com/AIsa-team/agent-skills/commit/49ebd76ab3e37f54cd562da7309e428efbacc729) |

[bulk-import]: https://github.com/AIsa-team/agent-skills/commit/5dcdad1c6f4e0afe5b9e2c0d1b99cbfd35681a88
