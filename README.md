# AIsa Agent Skills

Production-ready skills for autonomous agents, compatible with any
[agentskills.io](https://agentskills.io) harness: Claude Code, Claude,
OpenAI Codex, Cursor, Gemini CLI, OpenCode, Goose, OpenClaw, Hermes,
and others that implement the [Agent Skills specification](https://agentskills.io/specification).

Each top-level directory is one self-contained skill bundle with a
`SKILL.md`, optional human-facing `README.md`, and supporting scripts.
One `AISA_API_KEY` covers AIsa-powered skills.

## Review Note

This PR expands the catalog to 40 top-level skills after removing only same-function aliases and repackages. Subset skills are intentionally retained as separate discovery and entry points. The merge analysis is in [SKILL_DEDUP_ANALYSIS.md](./SKILL_DEDUP_ANALYSIS.md).

## Skills

| Skill | Description |
|---|---|
| [aisa-provider](./aisa-provider/) | Configure AIsa as a first-class model provider for OpenClaw, enabling production access to major Chinese AI models (Qwen, DeepSeek, Kimi K2.5, Doubao) through official partnerships with Alibaba Cloud, BytePlus, and Mo... |
| [aisa-tavily](./aisa-tavily/) | Search the web and extract public page content through AIsa's Tavily-backed API relay. Use when: the user needs web search, source discovery, current news lookup, or URL content extraction. Supports concise result set... |
| [aisa-twitter-api](./aisa-twitter-api/) | Twitter/X research, monitoring, watchlists, and OAuth-approved posting through AIsa. Use when: the user needs one flagship Twitter skill for trend tracking, competitor monitoring, timeline analysis, or approved postin... |
| [aisa-twitter-command-center](./aisa-twitter-command-center/) | Search X/Twitter profiles, tweets, trends, lists, communities, and Spaces through the AIsa relay, then support approved posting workflows with OAuth. Use when the user asks for Twitter research, monitoring, or posting... |
| [aisa-twitter-post-engage](./aisa-twitter-post-engage/) | Search X/Twitter profiles, tweets, trends, and approved engagement actions through the AIsa relay. Use when the user asks for Twitter/X research, posting, likes, follows, or related workflows without sharing passwords. |
| [aisa-youtube-search](./aisa-youtube-search/) | Search YouTube videos, channels, and playlists through the AIsa YouTube relay with one API key. Use when the user asks for YouTube discovery, query expansion, or pagination without managing Google credentials. |
| [cn-llm](./cn-llm/) | China LLM Gateway - Unified interface for Chinese LLMs including Qwen, DeepSeek, GLM, Baichuan. OpenAI compatible, one API Key for all models. Use when: the user needs model routing, provider setup, or Chinese LLM acc... |
| [crypto-market-data](./crypto-market-data/) | Query real-time and historical cryptocurrency market data via CoinGecko — simple prices, coin details, historical charts, OHLC candles, token prices by contract address, market-cap rankings, exchange data and tickers,... |
| [last30days](./last30days/) | Research the last 30 days across Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, GitHub, and grounded web search. Returns a ranked, clustered brief with citations. Use when the task needs recent social... |
| [last30days-zh](./last30days-zh/) | 聚合最近 30 天的 Reddit、X/Twitter、YouTube、TikTok、Instagram、Hacker News、Polymarket 和 web search 结果. Use when: the user needs recent multi-source research across the last 30 days. |
| [llm-router](./llm-router/) | Unified LLM Gateway - One API for 70+ AI models. Route to GPT, Claude, Gemini, Qwen, Deepseek, Grok and more with a single API key. Use when: the user needs model routing, provider setup, or Chinese LLM access guidance. |
| [market](./market/) | Query real-time and historical financial data across equities and crypto—prices, market moves, metrics, and trends for analysis, alerts, and reporting. Use when: the user needs market data, stock analysis, watchlists,... |
| [marketpulse](./marketpulse/) | Query real-time and historical financial data for equities—prices, news, financial statements, metrics, analyst estimates, insider and institutional activity, SEC filings, earnings press releases, segmented revenues, ... |
| [media-gen](./media-gen/) | Generate images and videos with AIsa. Four image models (Google Gemini 3 Pro Image, Alibaba Wan 2.7 image + image-pro, ByteDance Seedream) and four Wan video variants (wan2.6/2.7 × t2v/i2v). One API key; the client ro... |
| [multi-search](./multi-search/) | Parallel multi-source search combining Web, Scholar, Smart, and Tavily results with confidence scoring and AI synthesis. Best for comprehensive research requiring cross-source validation. Use when: the user needs web ... |
| [multi-source-search](./multi-source-search/) | Multi-source intelligent search for agents. Retrieval across web, scholar, Tavily, and Perplexity Sonar models. |
| [perplexity-research](./perplexity-research/) | Deep research using Perplexity Sonar models via AIsa API. Provides synthesized answers with citations. Supports 4 models from fast to exhaustive deep research. Use when: the user needs web search, research, source dis... |
| [perplexity-search](./perplexity-search/) | Perplexity Sonar search and answer generation through AIsa. Use when the task is specifically to call Perplexity Sonar, Sonar Pro, Sonar Reasoning Pro, or Sonar Deep Research for citation-backed web answers, analytica... |
| [prediction-market-arbitrage](./prediction-market-arbitrage/) | Find and analyze arbitrage opportunities across prediction markets like Polymarket and Kalshi. |
| [prediction-market-arbitrage-zh](./prediction-market-arbitrage-zh/) | 通过 AIsa API 发现 Polymarket 和 Kalshi 预测市场的套利机会。扫描体育市场跨平台价差、比较实时赔率、验证订单簿流动性。适用场景：预测市场套利、跨平台价差、体育博彩套利、赔率对比、无风险利润、市场低效。 Use when: the user needs market data, stock analysis, watchlists, or portfolio workflows. |
| [prediction-market-data](./prediction-market-data/) | Prediction markets data - Polymarket, Kalshi markets, prices, positions, and trades |
| [prediction-market-data-zh](./prediction-market-data-zh/) | 通过 AIsa API 查询跨平台预测市场数据。支持 Polymarket 和 Kalshi 的市场行情、价格、订单簿、K线、持仓和交易记录。适用场景：查询预测市场赔率、选举博彩、事件概率、市场情绪、Polymarket 价格、Kalshi 价格、体育博彩赔率、钱包盈亏、跨平台市场对比。 Use when: the user needs market data, stock analysis, watchlists, or por... |
| [scholar-search](./scholar-search/) | Search academic papers and scholarly articles via AIsa Scholar endpoint. Supports year range filtering for targeted research. Use when: the user needs web search, research, source discovery, or content extraction. |
| [smart-search](./smart-search/) | Intelligent hybrid search combining web and academic sources via AIsa Smart Search endpoint. Best when you need both web and scholarly results. Use when: the user needs web search, research, source discovery, or conte... |
| [stock-analysis](./stock-analysis/) | Analyze stocks and cryptocurrencies with 8-dimension scoring via AIsa API. Provides BUY/HOLD/SELL signals with confidence levels, entry/target/stop prices, and risk flags. Supports single or multi-ticker analysis with... |
| [stock-dividend](./stock-dividend/) | Analyze read-only dividend metrics for stocks via AIsa API. Provides yield, payout ratio, growth CAGR, safety score, income rating, and Dividend Aristocrat/King status without placing trades, making purchases, or mana... |
| [stock-hot](./stock-hot/) | Hot Scanner — find the most trending and high-momentum stocks and crypto right now via AIsa API. Top gainers, losers, most active by volume, crypto highlights, news catalysts, and top 5 watchlist picks. Use when the u... |
| [stock-portfolio](./stock-portfolio/) | Manage investment portfolios with live P&L tracking via AIsa API. Create, add, update, remove positions, rename, and show portfolio summary with real-time profit/loss. Use when the user wants to track investments, man... |
| [stock-rumors](./stock-rumors/) | Rumor Scanner — find early signals including M&A rumors, insider activity, analyst upgrades/downgrades, social whispers, and SEC/regulatory activity via AIsa API. Ranked by impact score. Use when the user asks about r... |
| [stock-watchlist](./stock-watchlist/) | Manage a stock/crypto watchlist with price target and stop-loss alerts via AIsa API. Add, remove, list, and check tickers with live price alerts. Use when the user wants to track stocks, set price alerts, manage a wat... |
| [tavily-extract](./tavily-extract/) | Extract clean, readable content from one or more URLs using Tavily Extract via AIsa API. Useful for reading full articles without visiting the page. Use when: the user needs web search, research, source discovery, or ... |
| [tavily-search](./tavily-search/) | Advanced web search via Tavily through AIsa API. Supports search depth, topic filtering (general/news/finance), time ranges, domain inclusion/exclusion, and LLM-generated answers. Use when: the user needs web search, ... |
| [trend-forecast](./trend-forecast/) | Multi-signal trend forecasting for autonomous agents. Combines prediction market odds, Twitter/X social sentiment, news velocity, and stock market data into a unified trend analysis with confidence scoring. Powered by AIsa. |
| [twitter-autopilot](./twitter-autopilot/) | Searches and reads X (Twitter): profiles, timelines, mentions, followers, tweet search, trends, lists, communities, and Spaces. Publishes posts, likes/unlikes tweets, and follows/unfollows users after the user complet... |
| [twitter-command-center-search-post](./twitter-command-center-search-post/) | Searches and reads X (Twitter): profiles, timelines, mentions, followers, tweet search, trends, lists, communities, and Spaces. Publishes posts after the user completes OAuth in the browser. Use when the user asks abo... |
| [us-stock-analyst](./us-stock-analyst/) | Professional US stock analysis with financial data, news, social sentiment, and multi-model AI. Comprehensive reports at $0.02-0.10 per analysis. Use when: the user needs market data, stock analysis, watchlists, or po... |
| [web-search](./web-search/) | Search the web using AIsa Scholar Web endpoint. Returns structured web results with titles, URLs, and snippets. Use when: the user needs web search, research, source discovery, or content extraction. |
| [x-intelligence-automation](./x-intelligence-automation/) | Search X/Twitter profiles, tweets, trends, and approved engagement actions through the AIsa relay. Use when the user asks for Twitter/X research, posting, likes, follows, or related workflows without sharing passwords. |
| [youtube-search](./youtube-search/) | YouTube Search API via AIsa unified endpoint. Search YouTube videos, channels, and playlists with a single AIsa API key — no Google API key or OAuth required. Use this skill when users want to search YouTube content. ... |
| [youtube-serp](./youtube-serp/) | YouTube SERP for agents. Search top-ranking videos, channels, and trends for content research and competitor tracking. |
