---
name: prediction-market-data-zh
description: '通过 AIsa API 查询跨平台预测市场数据。支持 Polymarket 和 Kalshi 的市场行情、价格、订单簿、K线、持仓和交易记录。适用场景：查询预测市场赔率、选举博彩、事件概率、市场情绪、Polymarket 价格、Kalshi 价格、体育博彩赔率、钱包盈亏、跨平台市场对比。 Use when: the user needs market data, stock analysis, watchlists, or portfolio workflows.'
license: MIT
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: 📈
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# 预测市场数据

通过 [AIsa API](https://aisa.one) 查询 [Polymarket](https://polymarket.com) 和 [Kalshi](https://kalshi.com) 预测市场。

## 配置

```bash
export AISA_API_KEY="your-key"
```

在 [aisa.one](https://aisa.one) 获取 Key（$0.01/次查询，按量付费）。

## 工作流程

查询预测市场数据的步骤：

1. **搜索市场**获取 ID（必须从这一步开始）
2. **从返回结果中提取 ID**（`token_id`、`condition_id` 或 `market_ticker`）
3. **用 ID 查询详情**（价格、订单簿、K线等）

## 快速示例

### Polymarket：搜索 → 获取价格

```bash
# 第一步：搜索市场，提取 token_id（side_a.id 或 side_b.id）
python3 scripts/prediction_market_client.py polymarket markets --search "election" --status open --limit 5

# 第二步：用第一步的 token_id 获取价格
python3 scripts/prediction_market_client.py polymarket price <token_id>
```

### Kalshi：搜索 → 获取价格

```bash
# 第一步：搜索市场，提取 market_ticker
python3 scripts/prediction_market_client.py kalshi markets --search "fed rate" --status open --limit 5

# 第二步：用第一步的 market_ticker 获取价格
python3 scripts/prediction_market_client.py kalshi price <market_ticker>
```

### 跨平台体育市场

```bash
python3 scripts/prediction_market_client.py sports by-date nba --date 2025-04-01
```

## ID 参考

大多数命令需要从 `markets` 返回中获取 ID，务必先搜索。

| 平台 | ID 字段 | 获取位置 |
|------|---------|----------|
| Polymarket | `token_id` | markets 输出中的 `side_a.id` 或 `side_b.id` |
| Polymarket | `condition_id` | markets 输出中的 `condition_id` |
| Kalshi | `market_ticker` | markets 输出中的 `market_ticker` |

## 命令参考

### Polymarket

```bash
python3 scripts/prediction_market_client.py polymarket markets [--search <关键词>] [--status open|closed] [--min-volume <数值>] [--limit <数值>]
python3 scripts/prediction_market_client.py polymarket price <token_id> [--at-time <unix时间戳>]
python3 scripts/prediction_market_client.py polymarket activity --user <钱包地址> [--market-slug <slug>] [--limit <数值>]
python3 scripts/prediction_market_client.py polymarket orders [--market-slug <slug>] [--token-id <id>] [--user <钱包地址>] [--limit <数值>]
python3 scripts/prediction_market_client.py polymarket orderbooks --token-id <id> [--start <毫秒>] [--end <毫秒>] [--limit <数值>]
python3 scripts/prediction_market_client.py polymarket candlesticks <condition_id> --start <unix时间戳> --end <unix时间戳> [--interval 1|60|1440]
python3 scripts/prediction_market_client.py polymarket positions <钱包地址> [--limit <数值>]
python3 scripts/prediction_market_client.py polymarket wallet (--eoa <地址> | --proxy <地址>) [--with-metrics]
python3 scripts/prediction_market_client.py polymarket pnl <钱包地址> --granularity <day|week|month>
```

### Kalshi

```bash
python3 scripts/prediction_market_client.py kalshi markets [--search <关键词>] [--status open|closed] [--min-volume <数值>] [--limit <数值>]
python3 scripts/prediction_market_client.py kalshi price <market_ticker> [--at-time <unix时间戳>]
python3 scripts/prediction_market_client.py kalshi trades [--ticker <ticker>] [--start <unix时间戳>] [--end <unix时间戳>] [--limit <数值>]
python3 scripts/prediction_market_client.py kalshi orderbooks --ticker <ticker> [--start <毫秒>] [--end <毫秒>] [--limit <数值>]
```

### 跨平台体育市场

```bash
python3 scripts/prediction_market_client.py sports matching (--polymarket-slug <slug> | --kalshi-ticker <ticker>)
python3 scripts/prediction_market_client.py sports by-date <运动类型> --date <YYYY-MM-DD>
```

支持：`nfl`、`mlb`、`cfb`、`nba`、`nhl`、`cbb`、`pga`、`tennis`。

## 理解赔率

价格为小数：`0.65` = 65% 隐含概率。"Yes" 价格 = 事件发生的概率。交易量越高 = 流动性越强。

## 安全与权限

**需要：** `AISA_API_KEY` 环境变量。

所有操作均为**只读**，通过 HTTPS GET 请求 `api.aisa.one`。不执行交易、不连接钱包、除 API Key 外不发送个人数据。每个响应包含 `usage.cost` 和 `usage.credits_remaining`。

完整文档：[AIsa API 参考](https://docs.aisa.one/reference/)。
