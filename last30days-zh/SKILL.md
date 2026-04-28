---
name: last30days-zh
description: '聚合最近 30 天的 Reddit、X/Twitter、YouTube、TikTok、Instagram、Hacker News、Polymarket 和 web search 结果. Use when: the user needs recent multi-source research across the last 30 days.'
license: MIT
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, bash, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: 📰
    requires:
      bins:
      - python3
      - bash
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, bash, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# last30days 中文版

聚合最近 30 天的社交平台、社区论坛、预测市场和 grounded web 结果，再合成为一份研究简报。

## 触发条件

- 当用户需要最近 30 天的人物、公司、产品、市场、工具或趋势研究时使用。
- 当用户需要竞品对比、发布反应、社区情绪、近期动态总结时使用。
- 当用户需要结构化 JSON 输出，例如 `query_plan`、`ranked_candidates`、`clusters`、`items_by_source` 时使用。

## 不适用场景

- 不适合纯百科类、没有时效要求的问题。
- 不适合只想看单一官方来源、完全不需要社区和社交信号的场景。

## 能力

- 通过 AISA 提供规划、重排、综合、grounded web search、X/Twitter、YouTube 和 Polymarket。
- Reddit 和 Hacker News 走公开路径。
- TikTok、Instagram、Threads、Pinterest 在启用时走托管发现路径。
- 对外发布层现在只保留无状态研究主链，不再默认携带旧的 watchlist / briefing / 第二凭证 GitHub 扩展面。

## 环境要求

- 主凭证：`AISA_API_KEY`
- Python `3.12+`
- 统一使用仓库相对路径下的 `scripts/` 命令，避免运行时变量替换失败。
- 可选 repo-local 配置文件：`./.last30days-data/config.env`，也可以直接传 `--api-key`。

## 快速命令

```bash
bash scripts/run-last30days.sh "$ARGUMENTS" --emit=compact
python3 scripts/last30days.py "$ARGUMENTS" --api-key="$AISA_API_KEY"
python3 scripts/last30days.py "$ARGUMENTS" --emit=json
python3 scripts/last30days.py "$ARGUMENTS" --quick
python3 scripts/last30days.py "$ARGUMENTS" --deep
python3 scripts/last30days.py --diagnose
```

## 示例

- `last30days OpenAI Agents SDK`
- `last30days Peter Steinberger`
- `last30days OpenClaw vs Codex`
- `last30days Kanye West --quick`
