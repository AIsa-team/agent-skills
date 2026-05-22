# 📈 Trend Forecast

Multi-signal trend analysis for autonomous agents. Powered by [AIsa](https://aisa.one).

One API key → five data streams → confidence-scored forecasts.

## What It Does

Give it any question about a trend, and it:

1. **Decomposes** your query into source-specific search terms (via LLM)
2. **Queries prediction markets** for contract odds (Polymarket, Kalshi)
3. **Searches Twitter/X** for social sentiment and discussion volume
4. **Scans news** via Tavily for article velocity and headline sentiment
5. **Pulls stock data** if a public company or financial instrument is involved
6. **Synthesizes** all signals into a forecast with a confidence score (0-100)

All through a single `AISA_API_KEY`. No juggling vendor accounts.

## Install

```bash
# For OpenClaw
npx clawhub@latest install trend-forecast

# For Claude Code
mkdir -p ~/.claude/skills
cp -r trend-forecast ~/.claude/skills/

# For Cursor / Codex
mkdir -p ~/.cursor/skills
cp -r trend-forecast ~/.cursor/skills/
```

## Setup

```bash
export AISA_API_KEY="your-key-here"
# Get one at https://aisa.one
```

## Usage

### As an agent skill

Just ask naturally:

- *"What's the outlook on the AI chip market?"*
- *"Will the Fed cut rates before September?"*
- *"Forecast Tesla based on current sentiment"*
- *"What are prediction markets saying about the 2026 midterms?"*

### As a CLI tool

```bash
# Markdown report (default)
python3 scripts/trend_forecast.py "Will the Fed cut rates in 2026?"

# JSON output
python3 scripts/trend_forecast.py "Tesla outlook" --output json

# Save to file
python3 scripts/trend_forecast.py "AI market trends" --save report.md

# Use a different synthesis model
python3 scripts/trend_forecast.py "Bitcoin outlook" --model gpt-4.1
```

## Example Output

```
📈 TREND FORECAST: Fed rate cut increasingly likely by Q3 2026

Direction: 🟢 BULLISH
Confidence: 72/100
Signal Agreement: high
Time Horizon: 3-6 months
Generated: 2026-05-21 14:30 UTC

---

## Analysis

Prediction markets currently price a Fed rate cut before September 2026 at 72%,
up from 58% two weeks ago. Twitter discussion volume around "rate cut" has
increased 3x over the past week...

## Key Signals

- Polymarket prices Fed rate cut at 72% (up from 58%)
- Twitter volume on "Fed rate cut" up 3x in 7 days
- 23 major news articles in the last week, predominantly dovish framing
- Bond ETFs (TLT, BND) up 2.1% over 5 days

## Risks & Caveats

- Inflation data release next week could shift sentiment rapidly
- Prediction markets have historically overreacted to Fed commentary
```

## Project Structure

```
trend-forecast/
├── SKILL.md                       # Skill definition (metadata + workflow)
├── README.md                      # This file
├── .gitignore                     # Ignores __pycache__/
├── scripts/
│   ├── aisa_client.py             # Reusable AIsa API client
│   └── trend_forecast.py          # Main orchestrator script
└── references/
    └── api_endpoints.md           # AIsa endpoint documentation
```

## AIsa APIs Used

| Data Source        | AIsa Endpoint                                       | Purpose                   |
|--------------------|-----------------------------------------------------|---------------------------|
| LLM Gateway        | `api.aisa.one/v1/chat/completions`                  | Query decomposition + synthesis (`gpt-4.1-mini`) |
| Prediction Markets | `api.aisa.one/apis/v1/polymarket/markets` (+ `/kalshi/markets`) | Contract odds & volume    |
| Twitter/X          | `api.aisa.one/apis/v1/twitter/tweet/advanced_search` | Social sentiment          |
| Tavily (News)      | `api.aisa.one/apis/v1/tavily/search`                | News velocity & headlines |
| MarketPulse        | `api.aisa.one/apis/v1/financial/*`                  | Prices, metrics & company news |

See [`references/api_endpoints.md`](references/api_endpoints.md) for the full list of confirmed endpoints, parameters, and per-call pricing.

## Contributing

1. Fork this repo
2. Create a feature branch
3. Test with `python3 scripts/trend_forecast.py "test query"`
4. Submit a PR to the [AIsa-team/agent-skills](https://github.com/AIsa-team/agent-skills) repo

## License

Apache 2.0 — see [LICENSE](LICENSE)

---

*Built for [AIsa](https://aisa.one) · One key, every data source.*
