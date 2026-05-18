# Skill 去重合并分析

生成时间：2026-05-18

## 最新结论

- `targetSkills` 原始来源：54 个 skill
- AIsa 原仓库：10 个 skill
- 第一轮补齐后：54 个 skill
- 第二轮按功能去重后：25 个 skill
- 本轮删除功能重复/别名重包：29 个 skill

## 去重原则

- 优先保留 AIsa 仓库原本已有且覆盖面更完整的 canonical skill。
- 删除 `openclaw-*`、长别名、旧包装、单一子命令包装等功能重复项。
- 如果两个 skill 指向同一 API、脚本相同或功能完全包含，只保留覆盖面更清晰的一项。
- 保留有明确差异化使用场景的专用 skill，例如 `perplexity-search`、`aisa-tavily`、`marketpulse`、`stock-*` 工作流、中文本地化包。

## 删除的重复 skills

- openclaw-media-gen: alias of media-gen with identical media_gen_client.py
- youtube: alias of youtube-serp with identical youtube_client.py
- openclaw-youtube: OpenClaw repack of YouTube SERP functionality
- aisa-youtube-serp-scout: alias of youtube-serp with identical youtube_client.py
- openclaw-aisa-youtube-aisa: OpenClaw repack of YouTube SERP functionality
- youtube-search: older/minimal duplicate of aisa-youtube-search
- twitter: alias of twitter-autopilot
- twitter-command-center-search-post-interact: alias of twitter-autopilot
- twitter-command-center-search-post: subset of twitter-autopilot without engagement actions
- aisa-twitter-api: subset/alternate packaging of twitter-autopilot
- aisa-twitter-command-center: same auxiliary files as aisa-twitter-api
- aisa-twitter-engagement-suite: same auxiliary files as aisa-twitter-post-engage and covered by twitter-autopilot
- aisa-twitter-post-engage: covered by twitter-autopilot read/post/engagement workflow
- openclaw-twitter: OpenClaw repack of Twitter read/post workflow
- openclaw-twitter-post-engage: OpenClaw repack of Twitter read/post/engage workflow
- x-intelligence-automation: same functional surface as Twitter engagement variants
- aisa-multi-search-engine: overlaps multi-source-search search umbrella
- multi-search: same script as several narrower search wrappers and covered by multi-source-search
- search: same script family as multi-source-search; command-center alias
- openclaw-search: OpenClaw repack of multi-source search
- web-search: single-mode subset covered by multi-source-search
- scholar-search: single-mode subset covered by multi-source-search
- smart-search: single-mode subset covered by multi-source-search
- tavily-search: single-mode subset covered by multi-source-search and aisa-tavily
- tavily-extract: single-mode subset covered by multi-source-search and aisa-tavily
- perplexity-research: covered by existing perplexity-search
- prediction-market: alternate packaging of prediction-market-data
- prediction-market-arbitrage-api: alternate packaging of prediction-market-arbitrage
- cn-llm: Chinese LLM subset covered by llm-router; OpenClaw provider setup kept in aisa-provider

## 最终保留 skills

- aisa-provider
- aisa-tavily
- aisa-youtube-search
- crypto-market-data
- last30days
- last30days-zh
- llm-router
- market
- marketpulse
- media-gen
- multi-source-search
- perplexity-search
- prediction-market-arbitrage
- prediction-market-arbitrage-zh
- prediction-market-data
- prediction-market-data-zh
- stock-analysis
- stock-dividend
- stock-hot
- stock-portfolio
- stock-rumors
- stock-watchlist
- twitter-autopilot
- us-stock-analyst
- youtube-serp

## 仍需 reviewer 注意的近邻能力

- `market` 与 `marketpulse` 都是市场数据，但前者覆盖 equities + crypto，后者是更深的 equities/filings/macro 数据。
- `stock-analysis` 与 `us-stock-analyst` 都做股票分析，但前者偏快速评分，后者偏完整研究报告。
- `aisa-provider`、`llm-router` 都与模型接入有关；前者是 OpenClaw provider 配置，后者是通用 LLM router 调用。
- `last30days` 与 `last30days-zh` 功能相近，但中文包包含本地化说明和中文/国内平台研究路径，暂保留给 reviewer 决策。
- `prediction-market-*` 的 `-zh` 包是中文工作流本地化版本，暂保留给 reviewer 决策。
