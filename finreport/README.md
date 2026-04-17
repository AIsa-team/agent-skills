# FinReport

Automated investment research reports combining real-time financial data (MarketPulse) with citation-backed qualitative analysis (Perplexity Sonar). Produces a full markdown report in one agent session — equity or crypto.

---

## What it does

FinReport chains two data sources into a single workflow:

1. **MarketPulse** — prices, financial statements, SEC filings, insider trades, analyst estimates, and news
2. **Perplexity Sonar** — synthesized web intelligence with inline citations

Output is a structured 6-section markdown report saved to disk.

---

## Prerequisites

- Python 3.8+
- `AISA_API_KEY` environment variable set
- No external pip packages required (uses stdlib `urllib`)

---

## Installation

```bash
git clone https://github.com/your-org/agent-skills
cd agent-skills/openclaw-skills/finreport
```

---

## Authentication

```bash
# Option 1: Shell environment
export AISA_API_KEY=your_key_here

# Option 2: .env file at project root (add to .gitignore)
echo "AISA_API_KEY=your_key_here" > .env
```

---

## Usage

```bash
# Equity report — NVIDIA
python3 scripts/finreport_client.py \
  --ticker NVDA \
  --name "NVIDIA Corporation" \
  --sector "Technology"

# Equity report with custom output path
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

Default output path (no `--out`): `reports/{TICKER}_{YYYYMMDD}.md`

---

## Output structure

| Section | Content |
|---|---|
| Executive Summary | 3–5 sentence synthesis of the most actionable finding |
| 1. Financial Snapshot | Price, 30-day change, key metrics table, insider trades, SEC filings |
| 2. Market Narrative | Full Perplexity Sonar Pro analysis with inline citations |
| 3. Macro & Sector Context | Fed policy, sector trends, regulatory developments |
| 4. Recent News | 5 latest headlines with source and date |
| 5. Risk Factors | 3–5 labeled risks (MARKET / REGULATORY / COMPETITIVE / MACRO) |
| 6. Data Sources | Attribution for all data |

---

## How it works

```
MarketPulse API ─────┐
  - prices            │
  - financials        ├──► report_builder.py ──► {TICKER}_report.md
  - insider trades    │
  - SEC filings       │
  - news              │
                      │
Perplexity Sonar ────┘
  - sonar-pro (market narrative + citations)
  - sonar (macro & sector context)
```

---

## Running tests

```bash
python -m pytest tests/test_finreport.py -v
# or
python tests/test_finreport.py
```

All tests mock the network layer — no API key needed to run the test suite.

---

## File structure

```
finreport/
├── SKILL.md                     ← OpenClaw skill spec
├── README.md                    ← This file
├── scripts/
│   ├── finreport_client.py      ← CLI entry point
│   ├── market_fetcher.py        ← MarketPulse API wrapper
│   ├── perplexity_fetcher.py    ← Perplexity Sonar wrapper
│   └── report_builder.py        ← Report assembly
├── templates/
│   └── report_template.md       ← Report structure reference
└── tests/
    └── test_finreport.py        ← Unit tests (no live API calls)
```
