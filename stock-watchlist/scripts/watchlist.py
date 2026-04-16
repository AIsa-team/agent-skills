#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai>=1.0.0",
# ]
# ///
"""
Watchlist management with live alerts via AIsa API.

Watchlist stored at: ~/.clawdbot/skills/stock-analysis/watchlist.json
Current prices & signals fetched via AIsa API.

Usage:
    uv run watchlist.py add AAPL
    uv run watchlist.py add AAPL --target 220 --stop 160
    uv run watchlist.py add AAPL --alert-on signal
    uv run watchlist.py list
    uv run watchlist.py check
    uv run watchlist.py check --notify
    uv run watchlist.py remove AAPL
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from openai import OpenAI


# ─── Storage ────────────────────────────────────────────────────────────────

def get_storage_path() -> Path:
    state_dir = os.environ.get("CLAWDBOT_STATE_DIR", os.path.expanduser("~/.clawdbot"))
    p = Path(state_dir) / "skills" / "stock-analysis"
    p.mkdir(parents=True, exist_ok=True)
    return p / "watchlist.json"


def load_watchlist() -> dict:
    path = get_storage_path()
    if path.exists():
        return json.loads(path.read_text())
    return {"entries": {}}


def save_watchlist(data: dict) -> None:
    get_storage_path().write_text(json.dumps(data, indent=2))


# ─── AIsa API ────────────────────────────────────────────────────────────────

def get_client() -> OpenAI:
    api_key = os.environ.get("AISA_API_KEY")
    if not api_key:
        print("❌ Error: AISA_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    base_url = os.environ.get("AISA_BASE_URL", "https://api.aisa.one/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def fetch_watchlist_data(tickers: list[str]) -> dict:
    """Fetch current price + signal for each ticker via AIsa API."""
    if not tickers:
        return {}
    client = get_client()
    model = os.environ.get("AISA_MODEL", "gpt-4o")
    ticker_str = ", ".join(tickers)
    prompt = (
        f"For each of these tickers: {ticker_str}\n\n"
        "Fetch the current price and generate a quick BUY/HOLD/SELL signal based on "
        "RSI, trend, and recent price action.\n\n"
        "Return ONLY a JSON object. Example:\n"
        "{\n"
        "  \"AAPL\": {\"price\": 195.50, \"signal\": \"BUY\", \"change_1d\": 1.2, \"rsi\": 58},\n"
        "  \"TSLA\": {\"price\": 245.00, \"signal\": \"HOLD\", \"change_1d\": -0.8, \"rsi\": 51}\n"
        "}\n"
        "No explanation. JSON only."
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a financial data fetcher. Use your financial tools and return only JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())
    except Exception as e:
        print(f"⚠️  Could not fetch live data: {e}", file=sys.stderr)
        return {}


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_add(args):
    data = load_watchlist()
    ticker = args.ticker.upper()
    entry = {
        "ticker": ticker,
        "added": datetime.now().isoformat(),
        "target": args.target,
        "stop": args.stop,
        "alert_on": args.alert_on,
        "last_signal": None,
    }
    data["entries"][ticker] = entry
    save_watchlist(data)

    alerts = []
    if args.target:
        alerts.append(f"🎯 Target: ${args.target}")
    if args.stop:
        alerts.append(f"🛑 Stop: ${args.stop}")
    if args.alert_on == "signal":
        alerts.append("📊 Signal change alert")

    alert_str = " | ".join(alerts) if alerts else "no alerts set"
    print(f"✅ Added {ticker} to watchlist ({alert_str})")


def cmd_remove(args):
    data = load_watchlist()
    ticker = args.ticker.upper()
    if ticker not in data["entries"]:
        print(f"❌ {ticker} not on watchlist.")
        sys.exit(1)
    del data["entries"][ticker]
    save_watchlist(data)
    print(f"✅ Removed {ticker} from watchlist.")


def cmd_list(args):
    data = load_watchlist()
    if not data["entries"]:
        print("📋 Watchlist is empty. Add tickers with: watchlist.py add AAPL --target 220")
        return
    print("📋 Watchlist:")
    for ticker, entry in data["entries"].items():
        alerts = []
        if entry.get("target"):
            alerts.append(f"🎯 Target: ${entry['target']}")
        if entry.get("stop"):
            alerts.append(f"🛑 Stop: ${entry['stop']}")
        if entry.get("alert_on") == "signal":
            alerts.append("📊 Signal alert")
        alert_str = " | ".join(alerts) if alerts else "no alerts"
        added = entry.get("added", "")[:10]
        print(f"  • {ticker} (added {added}) — {alert_str}")


def cmd_check(args):
    data = load_watchlist()
    if not data["entries"]:
        print("📋 Watchlist is empty.")
        return

    tickers = list(data["entries"].keys())
    print(f"🔍 Checking {len(tickers)} watchlist items via AIsa API...\n", file=sys.stderr)

    live = fetch_watchlist_data(tickers)
    triggered = []

    print("📊 Watchlist Status:\n")
    print(f"{'Ticker':<10} {'Price':>10} {'1d%':>7} {'RSI':>6} {'Signal':>8} {'Alerts'}")
    print("─" * 65)

    for ticker, entry in data["entries"].items():
        ld = live.get(ticker, {})
        price = ld.get("price")
        signal = ld.get("signal", "—")
        change = ld.get("change_1d")
        rsi = ld.get("rsi")

        change_str = f"{change:+.1f}%" if change is not None else "N/A"
        rsi_str = str(int(rsi)) if rsi is not None else "—"
        price_str = f"${price:,.2f}" if price else "N/A"

        alerts_fired = []

        if price:
            if entry.get("target") and price >= entry["target"]:
                alerts_fired.append(f"🎯 TARGET HIT (${entry['target']})")
            if entry.get("stop") and price <= entry["stop"]:
                alerts_fired.append(f"🛑 STOP HIT (${entry['stop']})")

        if entry.get("alert_on") == "signal":
            prev_signal = entry.get("last_signal")
            if prev_signal and signal != prev_signal and signal in ("BUY", "SELL"):
                alerts_fired.append(f"📊 SIGNAL CHANGED: {prev_signal} → {signal}")
            # Update stored signal
            entry["last_signal"] = signal

        alert_str = " | ".join(alerts_fired) if alerts_fired else "—"
        print(f"{ticker:<10} {price_str:>10} {change_str:>7} {rsi_str:>6} {signal:>8} {alert_str}")

        if alerts_fired:
            triggered.append({"ticker": ticker, "price": price, "alerts": alerts_fired, "signal": signal})

    # Save updated signals
    save_watchlist(data)

    if triggered:
        print(f"\n⚡ {len(triggered)} alert(s) triggered:")
        for t in triggered:
            print(f"\n  🔔 {t['ticker']} @ ${t['price']:,.2f}")
            for a in t["alerts"]:
                print(f"     {a}")

    if args.notify and triggered:
        print("\n📬 Telegram-style notification:")
        print("─" * 40)
        lines = [f"🔔 Stock Alert Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
        for t in triggered:
            lines.append(f"\n${t['ticker']} @ ${t['price']:,.2f} | Signal: {t['signal']}")
            for a in t["alerts"]:
                lines.append(f"  {a}")
        print("\n".join(lines))
    elif not triggered:
        print("\n✅ No alerts triggered.")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Watchlist management with AIsa live alerts")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add ticker to watchlist")
    p_add.add_argument("ticker")
    p_add.add_argument("--target", type=float, default=None, help="Price target alert")
    p_add.add_argument("--stop", type=float, default=None, help="Stop loss alert")
    p_add.add_argument("--alert-on", choices=["signal"], default=None, help="Alert on signal change")

    p_remove = sub.add_parser("remove", help="Remove ticker from watchlist")
    p_remove.add_argument("ticker")

    sub.add_parser("list", help="Show watchlist")

    p_check = sub.add_parser("check", help="Check for triggered alerts")
    p_check.add_argument("--notify", action="store_true", help="Print Telegram-style notification")

    args = parser.parse_args()
    commands = {
        "add": cmd_add,
        "remove": cmd_remove,
        "list": cmd_list,
        "check": cmd_check,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
