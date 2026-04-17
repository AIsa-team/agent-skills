#!/usr/bin/env python3
"""
FinReport — Report assembly module.

Takes raw API data dicts from market_fetcher and perplexity_fetcher and
assembles the final markdown investment report. Works defensively: all
data fields are optional; missing data is shown as "N/A" rather than crashing.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional


# ── Formatting helpers ────────────────────────────────────────────────────────

def _fmt_currency(value: Any, default: str = "N/A") -> str:
    if value is None:
        return default
    try:
        n = float(value)
        if abs(n) >= 1_000_000_000:
            return f"${n / 1_000_000_000:.2f}B"
        if abs(n) >= 1_000_000:
            return f"${n / 1_000_000:.2f}M"
        return f"${n:,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_price(value: Any, default: str = "N/A") -> str:
    if value is None:
        return default
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_pct(value: Any, default: str = "N/A") -> str:
    if value is None:
        return default
    try:
        sign = "+" if float(value) >= 0 else ""
        return f"{sign}{float(value):.2f}%"
    except (TypeError, ValueError):
        return str(value)


# ── Data extractors ───────────────────────────────────────────────────────────

def _get_nested(obj: Any, *keys: str, default: Any = None) -> Any:
    """Safely walk a nested dict by a sequence of keys."""
    for key in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(key, default)
    return obj


def _extract_ohlcv_bars(price_history: Any) -> List[Dict[str, Any]]:
    """Return a list of OHLCV bar dicts from whatever shape the API returns."""
    if not isinstance(price_history, dict):
        return []
    data = price_history.get("data") or price_history
    for key in ("results", "bars", "prices", "candles", "ohlcv"):
        candidate = data.get(key)
        if isinstance(candidate, list):
            return candidate
    return []


def _extract_price_data(price_history: Any) -> Dict[str, str]:
    """Derive current price, 30-day change, and 30-day high/low from API data."""
    result = {
        "current_price": "N/A",
        "thirty_day_change": "N/A",
        "fifty_two_week": "N/A",
    }

    if not isinstance(price_history, dict):
        return result

    data = price_history.get("data") or price_history

    # Crypto snapshot: single price field
    for price_key in ("price", "last", "close", "current_price", "lastPrice"):
        val = data.get(price_key)
        if val is not None:
            result["current_price"] = _fmt_price(val)
            break

    # OHLCV array (equities and crypto historical)
    bars = _extract_ohlcv_bars(price_history)
    if len(bars) >= 2:
        def _close(bar: Dict[str, Any]) -> Optional[float]:
            for k in ("c", "close", "Close", "adjClose"):
                v = bar.get(k)
                if v is not None:
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        pass
            return None

        first_close = _close(bars[0])
        last_close = _close(bars[-1])

        if last_close is not None:
            result["current_price"] = _fmt_price(last_close)

        if first_close and last_close:
            pct = (last_close - first_close) / first_close * 100
            result["thirty_day_change"] = _fmt_pct(pct)

        highs = [float(b["h"]) for b in bars if b.get("h") is not None]
        lows  = [float(b["l"]) for b in bars if b.get("l") is not None]
        # Fall back to "high"/"low" keys
        if not highs:
            highs = [float(b["high"]) for b in bars if b.get("high") is not None]
        if not lows:
            lows = [float(b["low"]) for b in bars if b.get("low") is not None]
        if highs and lows:
            result["fifty_two_week"] = (
                f"{_fmt_price(min(lows))} / {_fmt_price(max(highs))}"
            )

    return result


def _extract_metrics(
    financials: Any,
    analyst_estimates: Any,
) -> Dict[str, str]:
    """Extract P/E, revenue, margins from the metrics snapshot and analyst estimates."""
    m = {
        "revenue_ttm": "N/A",
        "net_income_ttm": "N/A",
        "pe_ratio": "N/A",
        "eps_estimate": "N/A",
        "forward_revenue": "N/A",
    }

    # Metrics snapshot: data.snapshot holds P/E, margins, EPS
    if isinstance(financials, dict):
        data = financials.get("data") or financials
        snapshot = data.get("snapshot") or {}
        if isinstance(snapshot, dict):
            # P/E Ratio
            v = snapshot.get("price_to_earnings_ratio")
            if v is not None:
                try:
                    m["pe_ratio"] = f"{float(v):.1f}x"
                except (TypeError, ValueError):
                    m["pe_ratio"] = str(v)

            # Revenue (TTM): back-calculate from enterprise_value / EV-to-revenue ratio
            ev = snapshot.get("enterprise_value")
            ev_rev = snapshot.get("enterprise_value_to_revenue_ratio")
            if ev is not None and ev_rev is not None:
                try:
                    revenue = float(ev) / float(ev_rev)
                    m["revenue_ttm"] = _fmt_currency(revenue)
                except (TypeError, ValueError, ZeroDivisionError):
                    pass

            # Net Income (TTM): net_margin × revenue
            net_margin = snapshot.get("net_margin")
            if net_margin is not None and m["revenue_ttm"] != "N/A":
                try:
                    # Parse back the formatted revenue for the multiplication
                    raw_ev = float(ev) / float(ev_rev)
                    m["net_income_ttm"] = _fmt_currency(float(net_margin) * raw_ev)
                except (TypeError, ValueError, ZeroDivisionError):
                    pass

            # EPS (TTM) from snapshot — used as the "EPS Estimate" row if no analyst data
            eps_snap = snapshot.get("earnings_per_share")
            if eps_snap is not None:
                try:
                    m["eps_estimate"] = f"${float(eps_snap):.2f} (TTM)"
                except (TypeError, ValueError):
                    m["eps_estimate"] = str(eps_snap)

    # Analyst estimates: data.analyst_estimates array — nearest fiscal period first
    if isinstance(analyst_estimates, dict):
        data = analyst_estimates.get("data") or analyst_estimates
        estimates: List[Any] = data.get("analyst_estimates") or []
        if isinstance(estimates, list) and estimates:
            est = estimates[0]
            # EPS estimate (analyst forward) — overrides snapshot TTM EPS
            eps_val = est.get("earnings_per_share")
            if eps_val is not None:
                try:
                    period = est.get("fiscal_period", "")
                    label = f" ({period})" if period else ""
                    m["eps_estimate"] = f"${float(eps_val):.2f}{label}"
                except (TypeError, ValueError):
                    m["eps_estimate"] = str(eps_val)
            # Forward revenue estimate from nearest fiscal period
            rv = est.get("revenue")
            if rv is not None:
                period = est.get("fiscal_period", "")
                label = f" ({period})" if period else ""
                m["forward_revenue"] = _fmt_currency(rv) + label
            # Revenue estimate — only used if snapshot back-calculation was unavailable
            if m["revenue_ttm"] == "N/A" and rv is not None:
                m["revenue_ttm"] = _fmt_currency(rv) + " (est)"

    return m


def _format_insider_trades(insider_trades: Any) -> str:
    if not insider_trades:
        return "_No insider trade data available._"

    data = insider_trades.get("data") or insider_trades
    trades: List[Any] = data.get("insider_trades") or data.get("results") or []
    if not isinstance(trades, list) or not trades:
        return "_No recent insider trades reported._"

    lines = []
    for trade in trades[:3]:
        name = trade.get("name") or "Unknown"
        role = trade.get("title") or "Executive"
        action = trade.get("transaction_type") or "Trade"
        shares = trade.get("transaction_shares")
        price = trade.get("transaction_price_per_share")
        value = trade.get("transaction_value")
        trade_date = trade.get("transaction_date") or "N/A"

        shares_str = f"{int(shares):,}" if isinstance(shares, (int, float)) else (shares or "N/A")
        price_str = f" @ {_fmt_price(price)}/share" if price is not None else ""
        value_str = f" (total {_fmt_currency(value)})" if value is not None else ""
        lines.append(
            f"- **{name}** ({role}): {action} {shares_str} shares{price_str}{value_str} on {trade_date}"
        )

    return "\n".join(lines) if lines else "_No recent insider trades reported._"


def _format_sec_filings(sec_filings: Any) -> str:
    if not sec_filings:
        return "_No SEC filing data available._"

    data = sec_filings.get("data") or sec_filings
    filings: List[Any] = data.get("filings") or data.get("results") or []
    if not isinstance(filings, list) or not filings:
        return "_No recent SEC filings found._"

    lines = []
    for filing in filings[:3]:
        filing_type = filing.get("filing_type") or "Unknown"
        filing_date = filing.get("filing_date") or "N/A"
        url = filing.get("url") or ""
        entry = f"- **{filing_type}** — Filed {filing_date}"
        if url:
            entry += f" — [View filing]({url})"
        lines.append(entry)

    return "\n".join(lines) if lines else "_No recent SEC filings found._"


def _format_news(news_data: Any) -> str:
    if not news_data:
        return "_No news data available._"

    data = news_data.get("data") or news_data
    articles: List[Any] = (
        data.get("news")
        or data.get("articles")
        or data.get("results")
        or data.get("items")
        or []
    )
    if not isinstance(articles, list) or not articles:
        return "_No recent news articles found._"

    lines = []
    for article in articles[:5]:
        headline = (
            article.get("headline")
            or article.get("title")
            or article.get("name")
            or "No headline"
        )
        source = (
            article.get("source")
            or article.get("publisher")
            or article.get("author")
            or "Unknown"
        )
        pub_date = (
            article.get("date")
            or article.get("published_at")
            or article.get("datetime")
            or article.get("publishedAt")
            or "N/A"
        )
        lines.append(f"- **{headline}** — {source} ({pub_date})")

    return "\n".join(lines) if lines else "_No recent news articles found._"


_MACRO_DISCLAIMER_PREFIXES = (
    "however, the search results",
    "limitations:",
    "the search results do not",
)


def _clean_macro_text(text: str) -> str:
    """Remove Perplexity disclaimer / limitation sentences from macro text."""
    kept = []
    for line in (text or "").splitlines():
        if line.strip().lower().startswith(_MACRO_DISCLAIMER_PREFIXES):
            continue
        kept.append(line)
    return "\n".join(kept)


def _format_risks(risks: Dict[str, Any], ticker: str) -> str:
    """Format pre-fetched Perplexity risk factors into labeled markdown bullets.

    Expects a dict with keys: market, macro, regulatory, competitive.
    Any missing or empty value is replaced by a ticker-aware fallback sentence.
    """
    t = ticker.upper() if ticker else "This asset"
    fallbacks: Dict[str, str] = {
        "market": (
            f"{t} faces demand slowdown risk if investor enthusiasm cools "
            f"or end-market ROI from AI capex fails to materialize."
        ),
        "macro": (
            f"Persistent elevated interest rates raise the cost of capital and could "
            f"slow enterprise spending in {t}'s key markets."
        ),
        "regulatory": (
            f"Expanding export controls and trade restrictions could limit "
            f"{t}'s addressable markets in key international regions."
        ),
        "competitive": (
            f"{t} faces growing competitive pressure; customers may evaluate "
            f"alternatives if the performance or cost advantage narrows."
        ),
    }
    label_map = {
        "market": "MARKET",
        "macro": "MACRO",
        "regulatory": "REGULATORY",
        "competitive": "COMPETITIVE",
    }
    bullets: List[str] = []
    for key in ("market", "macro", "regulatory", "competitive"):
        text = (risks.get(key) or "").strip() if isinstance(risks, dict) else ""
        if not text:
            text = fallbacks[key]
        if not text.endswith("."):
            text += "."
        bullets.append(f"- **[{label_map[key]}]** {text}")
    return "\n".join(bullets)


def _strip_first_h1(text: str) -> str:
    """Remove the opening H1 line that Perplexity often prepends to its response."""
    lines = text.splitlines()
    if lines and lines[0].strip().startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines)


# ── Main assembly function ────────────────────────────────────────────────────

def build_report(
    ticker: str,
    market_data: Dict[str, Any],
    narrative: str,
    macro: str,
    risks: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Assemble a markdown investment report from raw API data.

    Args:
        ticker:      Asset ticker (e.g. "NVDA", "BTC-USD")
        market_data: Dict with keys: price_history, news, and for equities:
                     financials, sec_filings, insider_trades, analyst_estimates
        narrative:   Markdown string from get_market_narrative()
        macro:       Markdown string from get_macro_context()
        risks:       Dict from get_risk_factors() with keys:
                     market, macro, regulatory, competitive.
                     Fallbacks are used for any missing key.

    Returns:
        Complete markdown report string.
    """
    today = date.today().strftime("%B %d, %Y")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    is_crypto_asset = ticker.upper().endswith("-USD")

    # Price data
    price_info = _extract_price_data(market_data.get("price_history") or {})
    price_section = (
        f"- **Current Price:** {price_info['current_price']}\n"
        f"- **30-Day Change:** {price_info['thirty_day_change']}\n"
        f"- **30-Day High / Low:** {price_info['fifty_two_week']}"
    )

    # Key metrics table
    if is_crypto_asset:
        metrics_section = "_Not applicable for crypto assets._"
        insider_section = "_Not applicable for crypto assets._"
        sec_section = "_Not applicable for crypto assets._"
    else:
        m = _extract_metrics(
            market_data.get("financials"),
            market_data.get("analyst_estimates"),
        )
        metrics_section = (
            "| Metric               | Value            |\n"
            "|----------------------|------------------|\n"
            f"| Revenue (TTM)        | {m['revenue_ttm']} |\n"
            f"| Net Income (TTM)     | {m['net_income_ttm']} |\n"
            f"| P/E Ratio            | {m['pe_ratio']} |\n"
            f"| EPS Estimate (Next)  | {m['eps_estimate']} |\n"
            f"| Forward Revenue Est. | {m['forward_revenue']} |"
        )
        insider_section = _format_insider_trades(market_data.get("insider_trades"))
        sec_section = _format_sec_filings(market_data.get("sec_filings"))

    # News
    news_section = _format_news(market_data.get("news"))

    # Clean macro text before use in Section 3
    macro_clean = _clean_macro_text(macro)

    # Risk factors — format pre-fetched Perplexity JSON; fall back per key if empty
    risk_section = _format_risks(risks or {}, ticker)

    # Executive summary — price context + first 2 salient sentences from narrative
    exec_lines = []
    if price_info["current_price"] != "N/A":
        change_str = (
            f" ({price_info['thirty_day_change']} over 30 days)"
            if price_info["thirty_day_change"] != "N/A"
            else ""
        )
        exec_lines.append(
            f"{ticker.upper()} is currently trading at "
            f"{price_info['current_price']}{change_str}."
        )
    if narrative:
        # Strip markdown header lines before extracting exec summary sentences
        narrative_prose = " ".join(
            line for line in narrative.splitlines()
            if not line.strip().startswith("#")
        )
        narrative_sentences = [
            s.strip()
            for s in narrative_prose.split(".")
            if len(s.strip()) > 100
        ][:2]
        exec_lines.extend(s + "." for s in narrative_sentences)
    if not exec_lines:
        exec_lines.append(
            f"This report provides a comprehensive analysis of {ticker.upper()} "
            "combining real-time financial data with qualitative market intelligence."
        )
    executive_summary = " ".join(exec_lines)

    return f"""# FinReport: {ticker.upper()} — {today}

---

## Executive Summary
{executive_summary}

---

## 1. Financial Snapshot

### Price & Performance
{price_section}

### Key Metrics (Equities Only)
{metrics_section}

### Recent Insider Activity
{insider_section}

### Latest SEC Filings
{sec_section}

---

## 2. Market Narrative & Qualitative Analysis
{_strip_first_h1(narrative) if narrative else "_Narrative analysis unavailable._"}

---

## 3. Macro & Sector Context
{macro_clean or "_Macro context unavailable._"}

---

## 4. Recent News
{news_section}

---

## 5. Risk Factors
{risk_section}

---

## 6. Data Sources
- MarketPulse Financial API (AIsa)
- Perplexity Sonar Pro (qualitative analysis + citations)
- Perplexity Sonar (macro context)
- SEC EDGAR (filings)
- Report generated: {generated_at}
"""
