# US Stock Analyst

Professional equity analysis powered by AIsa's unified API platform.

## Features

- **Complete Financial Data**: Metrics, prices, statements, estimates, insider trades, SEC filings
- **Multi-Source Intelligence**: News, web search, academic research, social media, video content
- **AI-Powered Analysis**: Multi-model synthesis with GPT-4, Claude, Gemini, and more
- **Flexible Depth**: Quick, standard, or deep analysis modes
- **Affordable**: $0.02-0.10 per analysis (vs $2,000/month for Bloomberg)

## Quick Start

```bash
# Set your AIsa API key
export AISA_API_KEY="your-key"

# Run basic analysis
python scripts/stock_analyst.py analyze --ticker AAPL

# Run deep analysis with custom models
python scripts/stock_analyst.py analyze --ticker NVDA --depth deep --models gpt-4 claude-3-opus
```

## Installation

```bash
# Install dependencies
pip install httpx asyncio

# Or use requirements.txt
pip install -r requirements.txt
```

## Analysis Modes

| Mode | Time | Cost | Data Sources |
|------|------|------|--------------|
| **quick** | ~10s | $0.01-0.02 | Financial metrics, news, Twitter, basic AI |
| **standard** | ~20s | $0.02-0.05 | + Analyst estimates, insider trades, YouTube |
| **deep** | ~30s | $0.05-0.10 | + Statements, institutional, SEC, research |

## Examples

### Basic Analysis

```python
from scripts.stock_analyst import AIsaStockAnalyst
import asyncio

async def main():
    analyst = AIsaStockAnalyst(api_key="your_key")
    
    report = await analyst.analyze_stock(
        ticker="AAPL",
        depth="standard"
    )
    
    print(report['investment_summary'])
    print(f"Sentiment: {report['sentiment_analysis']['sentiment']}")
    
    await analyst.close()

asyncio.run(main())
```

### Portfolio Monitoring

```python
async def monitor_portfolio():
    analyst = AIsaStockAnalyst(api_key="your_key")
    
    portfolio = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
    
    for ticker in portfolio:
        report = await analyst.analyze_stock(ticker, depth="quick")
        print(f"\n{ticker}: {report['sentiment_analysis']['sentiment']}")
        print(f"P/E: {report['key_metrics'].get('pe_ratio')}")
    
    await analyst.close()
```

See `examples/` directory for more use cases.

## Data Sources

### Financial Data (MarketPulse APIs)
- Real-time metrics (market cap, P/E, revenue, margins, ROE)
- Historical prices (any interval: second, minute, day, week, month, year)
- Financial statements (income, balance, cash flow)
- Analyst estimates and ratings
- Insider trading activity
- Institutional ownership
- SEC filings

### News & Research
- Company news aggregation
- Web search (articles and analysis)
- Academic research papers
- YouTube content (earnings calls, analyst videos)

### Social Sentiment
- Twitter mentions and trends
- AI-powered sentiment analysis

### AI Analysis
- Multi-model LLM (GPT-4, Claude, Gemini, Qwen, DeepSeek, Grok)
- Investment thesis generation
- Sentiment synthesis
- Valuation assessment

## Output Format

```json
{
  "ticker": "NVDA",
  "analysis_date": "2025-02-07T10:30:00Z",
  "investment_summary": "...",
  "key_metrics": {
    "market_cap": 1780500000000,
    "pe_ratio": 68.5,
    "revenue": 60922000000,
    "profit_margin": 0.489,
    "roe": 1.152
  },
  "sentiment_analysis": {
    "sentiment": "bullish",
    "confidence": "high",
    "key_themes": ["..."],
    "summary": "..."
  },
  "valuation": {
    "assessment": "fairly_valued",
    "price_target_12m": 850.00,
    "reasoning": "..."
  },
  "data_sources": {...}
}
```

## Pricing

- Quick Analysis: $0.01-0.02 per stock
- Standard Analysis: $0.02-0.05 per stock
- Deep Analysis: $0.05-0.10 per stock

**Compare:**
- Bloomberg Terminal: $2,000/month
- FactSet: $1,000/month
- Analyst Report: $50-500 each
- **AIsa Stock Analyst: $0.02-0.10 each**

## Use Cases

1. **Investment Research** - Comprehensive analysis before investing
2. **Portfolio Monitoring** - Daily updates on holdings
3. **Earnings Analysis** - Track quarterly results and guidance
4. **Insider Tracking** - Monitor insider buy/sell activity
5. **Sentiment Monitoring** - Track social and market sentiment
6. **Screening** - Find opportunities matching criteria

## API Reference

Complete documentation: [SKILL.md](SKILL.md)

Key endpoints:
- Financial Metrics: `GET /financial/financial-metrics/snapshot`
- Stock Prices: `GET /financial/prices`
- Company News: `GET /financial/news`
- Analyst Estimates: `GET /financial/analyst/eps`
- Insider Trades: `GET /financial/insider/trades`
- Twitter: `GET /twitter/tweet/advanced_search`
- YouTube: `GET /youtube/search`
- LLM: `POST /v1/chat/completions`

## Compliance

All analyses include regulatory disclaimer:

> This analysis is for informational purposes only and should not be considered personalized investment advice. Please conduct your own research and consult with licensed financial advisors before making investment decisions.

Compliant with: SEC Rule 15c2-1, FINRA regulations, GDPR

## Support

- **Documentation**: https://aisa.mintlify.app
- **API Reference**: https://aisa.mintlify.app/api-reference/introduction
- **Discord**: https://discord.gg/2mzptTkq
- **Email**: developer@aisa.one

## About AIsa

Unified API infrastructure for AI agents.

- **Financial Data**: Stocks, crypto, market data
- **LLM Providers**: OpenAI, Anthropic, Google, Alibaba, DeepSeek, xAI
- **Data APIs**: Search, social, research, news, multimedia
- **Payment Rails**: HTTP 402 micropayments

Single API Key. Pay-Per-Use. Agent-Native.

Website: https://aisa.one

## License

See [LICENSE](LICENSE) for details.
