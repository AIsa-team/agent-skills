---
name: finreport
description: "Automated investment research reports combining real-time financial data (MarketPulse) with citation-backed qualitative analysis (Perplexity Sonar). Trigger when asked to research a stock or crypto asset, generate an investment report, or analyze a company's financial health and market narrative in one unified workflow."
homepage: https://openclaw.ai
metadata: {"openclaw":{"emoji":"📈","requires":{"bins":["python3"],"env":["AISA_API_KEY"]},"primaryEnv":"AISA_API_KEY"}}
---

# FinReport — Automated Investment Research Skill

## Purpose

FinReport solves a core problem in financial research: **quantitative data
without narrative context is incomplete, and narrative context without hard
data is unreliable.** This skill chains MarketPulse (hard financial data) and
Perplexity Sonar (synthesized web intelligence with citations) into a single
automated workflow that produces publication-quality investment reports.

A human analyst would take 2–4 hours to assemble this manually. FinReport
produces it in one agent session.

---

## Requirements

- Set `AISA_API_KEY` in your environment
- Python 3.8+
- Use the bundled client at `{baseDir}/scripts/finreport_client.py`

---

## Usage

```bash
# Full equity report — NVIDIA
python3 scripts/finreport_client.py \
  --ticker NVDA \
  --name "NVIDIA Corporation" \
  --sector "Technology"

# Full equity report with custom output path
python3 scripts/finreport_client.py \
  --ticker TSLA \
  --name "Tesla Inc." \
  --sector "Consumer Discretionary" \
  --out reports/tesla_deep_dive.md

# Crypto report — Bitcoin
python3 scripts/finreport_client.py \
  --ticker BTC-USD \
  --name "Bitcoin" \
  --sector "Crypto"

# Crypto report — Ethereum
python3 scripts/finreport_client.py \
  --ticker ETH-USD \
  --name "Ethereum" \
  --sector "Crypto"
```

---

## Two-Phase Workflow

```
MarketPulse API ─────┐
  - prices            ├──► report_builder.py ──► {TICKER}_report.md
  - financials        │
  - insider trades    │
  - SEC filings       │
  - news              │
                      │
Perplexity Sonar ────┘
  - sonar-pro (market narrative + citations)
  - sonar (macro & sector context)
```

---

## Output Structure

Each report contains 6 sections:

1. **Executive Summary** — 3–5 sentence synthesis of the most actionable finding
2. **Financial Snapshot** — Current price, 30-day change, key metrics, insider activity, SEC filings
3. **Market Narrative** — Full Perplexity Sonar Pro analysis with inline citations
4. **Macro & Sector Context** — Fed policy, sector trends, regulatory developments
5. **Recent News** — 5 latest headlines with source and date
6. **Risk Factors** — 3–5 labeled risks (MARKET / REGULATORY / COMPETITIVE / MACRO)

---

## Module Map (L3 Resources)

- `scripts/market_fetcher.py` — MarketPulse API wrapper
- `scripts/perplexity_fetcher.py` — Perplexity Sonar API wrapper
- `scripts/report_builder.py` — Report assembly and formatting
- `scripts/finreport_client.py` — CLI orchestrator (primary entry point)
- `templates/report_template.md` — Markdown report template

---

## API Reference

| Data | Endpoint |
|---|---|
| Stock OHLCV | `GET /apis/v1/financial/prices` |
| Crypto price | `GET /apis/v1/financial/crypto/prices/snapshot` |
| Company news | `GET /apis/v1/financial/news` |
| Financial statements | `GET /apis/v1/financial/financial_statements/all` |
| SEC filings | `GET /apis/v1/financial/sec/filings` |
| Insider trades | `GET /apis/v1/financial/insider/trades` |
| Analyst estimates | `GET /apis/v1/financial/analyst/eps` |
| Market narrative | `POST /apis/v1/perplexity/sonar-pro` |
| Macro context | `POST /apis/v1/perplexity/sonar` |

All endpoints authenticate with:
```
Authorization: Bearer $AISA_API_KEY
```
