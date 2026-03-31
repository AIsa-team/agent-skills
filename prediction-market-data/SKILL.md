---
name: prediction-market-api
description: Interacts with the AIsa API proxy for prediction market data (Polymarket, Kalshi) and matching markets. Use when you need to fetch prediction market data, prices, or orderbook information via the AIsa API proxy.
---

# Prediction Market API Skill

This skill provides a Python client to interact with the AIsa API proxy, which offers comprehensive access to prediction market data across platforms like Polymarket and Kalshi.

**Base URL**: `https://api.aisa.one/apis/v1`

## Capabilities

The AIsa API proxy provides access to:
1. **Polymarket Data**: Markets, Events, Trade History, Orderbooks, Activity, Market Prices, Candlesticks, Positions, Wallet Info, and PnL.
2. **Kalshi Data**: Markets, Trade History, Market Prices, and Orderbooks.
3. **Matching Markets**: Find equivalent markets across different prediction market platforms for sports events.
4. **Order Router**: Place orders on Polymarket with server-side execution.

## Bundled Resources

- `scripts/client.py`: A comprehensive Python client class (`PredictionMarketAPIClient`) that implements all major REST endpoints.

## Usage Instructions

To use the API, import the `PredictionMarketAPIClient` from the bundled script.

```python
import sys

sys.path.append('/home/ubuntu/skills/prediction-market-data/scripts')
from client import PredictionMarketAPIClient

# Initialize the client
client = PredictionMarketAPIClient(api_key="your_api_key_here")

# Example: Get Polymarket market price
market_price = client.get_polymarket_market_price("19701256321759583954581192053894521654935987478209343000964756587964612528044")
print(f"Price: {market_price.get('price')}")

# Example: Search for Kalshi markets
kalshi_markets = client.get_kalshi_markets(search="bitcoin", limit=5)
```

### Key Endpoints Available in the Client

#### Polymarket
- `get_polymarket_markets()`: Find markets with various filters.
- `get_polymarket_events()`: List events.
- `get_polymarket_orders()`: Fetch historical trade data.
- `get_polymarket_orderbooks()`: Fetch historical orderbook snapshots.
- `get_polymarket_activity()`: Fetch activity data.
- `get_polymarket_market_price()`: Get current or historical market price.
- `get_polymarket_candlesticks()`: Fetch historical candlestick data.
- `get_polymarket_positions()`: Fetch positions for a wallet.
- `get_polymarket_wallet()`: Fetch wallet info.
- `get_polymarket_wallet_pnl()`: Fetch realized PnL for a wallet.

#### Kalshi
- `get_kalshi_markets()`: Find markets.
- `get_kalshi_trades()`: Fetch historical trade data.
- `get_kalshi_market_price()`: Get current market price.
- `get_kalshi_orderbooks()`: Fetch historical orderbook snapshots.

#### Matching Markets
- `get_matching_sports()`: Find equivalent sports markets.
- `get_matching_sport_by_date()`: Find equivalent sports markets by date.

#### Order Router
- `place_order()`: Place an order on Polymarket via the AIsa API proxy.

## Websockets

Real-time data streaming is available through WebSocket connections.
You can subscribe to orders filtered by users, condition IDs, or market slugs.
