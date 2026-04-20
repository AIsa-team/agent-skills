# Prediction Market

Get current odds, prices, and market data from prediction markets like Polymarket and Kalshi. Access historical orderbook data, candlestick charts, trade history, wallet positions, and more.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: **Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**,
**Gemini CLI**, **OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and
others that implement the
[Agent Skills specification](https://agentskills.io/specification).

Requires Python 3, a POSIX shell, and `AISA_API_KEY`.

## Features

- **Polymarket**: Search markets, live prices, trade history, orderbooks, candlesticks, wallet positions, P&L
- **Kalshi**: Search markets, live prices, trade history, orderbooks
- **Cross-Platform**: Match equivalent sports markets across Polymarket and Kalshi

## Quick Start

```bash
export AISA_API_KEY="your-key"

# Search Polymarket for election markets
python scripts/prediction_market_client.py polymarket markets --search "election" --status open

# Get current price for a Polymarket token
python scripts/prediction_market_client.py polymarket price <token_id>

# Search Kalshi for Fed rate markets
python scripts/prediction_market_client.py kalshi markets --search "fed rate"

# Get current price for a Kalshi market
python scripts/prediction_market_client.py kalshi price <market_ticker>

# Find matching NBA markets across platforms
python scripts/prediction_market_client.py sports by-date nba --date 2025-03-01
```

## API Reference

Specific endpoints this skill hits:

- [Polymarket Markets](https://aisa.one/docs/api-reference/prediction-market/get_polymarket-markets), [Events](https://aisa.one/docs/api-reference/prediction-market/get_polymarket-events), [Market Price](https://aisa.one/docs/api-reference/prediction-market/get_polymarket-market-price), [Candlesticks](https://aisa.one/docs/api-reference/prediction-market/get_polymarket-candlesticks)
- [Polymarket Activity](https://aisa.one/docs/api-reference/prediction-market/get_polymarket-activity), [Orderbook History](https://aisa.one/docs/api-reference/prediction-market/get_polymarket-orderbooks), [Trade History](https://aisa.one/docs/api-reference/prediction-market/get_polymarket-orders)
- [Kalshi Markets](https://aisa.one/docs/api-reference/prediction-market/get_kalshi-markets)
- [Matching Markets — Sports](https://aisa.one/docs/api-reference/prediction-market/get_matching-markets-sports), [Sports by Date](https://aisa.one/docs/api-reference/prediction-market/get_matching-markets-sports-by-sport)

Full catalog: [aisa.one/docs/api-reference](https://aisa.one/docs/api-reference).
