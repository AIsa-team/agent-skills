---
name: prediction-market-arbitrage-zh
description: '通过 AIsa API 发现 Polymarket 和 Kalshi 预测市场的套利机会。扫描体育市场跨平台价差、比较实时赔率、验证订单簿流动性。适用场景：预测市场套利、跨平台价差、体育博彩套利、赔率对比、无风险利润、市场低效。 Use when: the user needs market data, stock analysis, watchlists, or portfolio workflows.'
license: MIT
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: ⚖️
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# 预测市场套利

通过 [AIsa API](https://aisa.one) 发现 [Polymarket](https://polymarket.com) 和 [Kalshi](https://kalshi.com) 之间的套利机会。

## 配置

```bash
export AISA_API_KEY="your-key"
```

在 [aisa.one](https://aisa.one) 获取 Key（$0.01/次查询，按量付费）。

## 工作流程

发现套利机会的步骤：

1. **扫描匹配市场**（`scan` 批量扫描，`match` 分析特定市场）
2. **查看价差** — 工具自动计算跨平台价格差异
3. **验证流动性** — 用 `prediction_market_client.py orderbooks` 检查订单簿深度后再行动

## 快速示例

### 扫描某项运动的套利机会

```bash
# 扫描指定日期所有 NBA 市场 — 自动显示价差
python3 scripts/arbitrage_finder.py scan nba --date 2025-04-01
```

### 分析特定市场

```bash
# 通过 Polymarket slug
python3 scripts/arbitrage_finder.py match --polymarket-slug <slug>

# 通过 Kalshi ticker
python3 scripts/arbitrage_finder.py match --kalshi-ticker <ticker>
```

### 行动前验证流动性

```bash
# 检查两边的订单簿深度
python3 scripts/prediction_market_client.py polymarket orderbooks --token-id <id>
python3 scripts/prediction_market_client.py kalshi orderbooks --ticker <ticker>
```

## 命令参考

### arbitrage_finder.py — 自动检测

```bash
python3 scripts/arbitrage_finder.py scan <运动类型> --date <YYYY-MM-DD> [--min-spread <百分比>] [--min-liquidity <美元>] [--json]
python3 scripts/arbitrage_finder.py match --polymarket-slug <slug> [--min-spread <百分比>] [--min-liquidity <美元>] [--json]
python3 scripts/arbitrage_finder.py match --kalshi-ticker <ticker> [--min-spread <百分比>] [--min-liquidity <美元>] [--json]
```

支持：`nba`、`nfl`、`mlb`、`nhl`、`soccer`、`tennis`。

### prediction_market_client.py — 原始市场数据

用于手动价格检查和深入分析。

```bash
# 搜索市场
python3 scripts/prediction_market_client.py polymarket markets --search <关键词> --status open --limit 5
python3 scripts/prediction_market_client.py kalshi markets --search <关键词> --status open --limit 5

# 获取价格（使用 markets 输出中的 token_id / market_ticker）
python3 scripts/prediction_market_client.py polymarket price <token_id>
python3 scripts/prediction_market_client.py kalshi price <market_ticker>

# 跨平台体育市场匹配
python3 scripts/prediction_market_client.py sports by-date <运动类型> --date <YYYY-MM-DD>
python3 scripts/prediction_market_client.py sports matching (--polymarket-slug <slug> | --kalshi-ticker <ticker>)

# 订单簿深度
python3 scripts/prediction_market_client.py polymarket orderbooks --token-id <id>
python3 scripts/prediction_market_client.py kalshi orderbooks --ticker <ticker>
```

## 理解套利

当不同平台上所有互斥结果的合计成本低于 `1.0` 时，套利机会存在：

> Polymarket 上 "Yes" 价格 `0.40` + Kalshi 上 "No" 价格 `0.55` = 成本 `0.95`，保证回报 `1.00` → 5.3% 利润。

务必验证订单簿深度 — 没有流动性的价差无法执行。

## 安全与权限

**需要：** `AISA_API_KEY` 环境变量。

所有操作均为**只读**，通过 HTTPS GET 请求 `api.aisa.one`。套利价差在本地计算。不执行交易、不连接钱包、除 API Key 外不发送个人数据。每个响应包含 `usage.cost` 和 `usage.credits_remaining`。

完整文档：[AIsa API 参考](https://docs.aisa.one/reference/)。
