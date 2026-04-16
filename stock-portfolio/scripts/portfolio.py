#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai>=1.0.0",
# ]
# ///
"""
Portfolio management with live pricing via AIsa API.

Portfolio data stored locally in ~/.clawdbot/skills/stock-analysis/portfolios.json
Current prices fetched live via AIsa API.

Usage:
    uv run portfolio.py create "Tech Portfolio"
    uv run portfolio.py list
    uv run portfolio.py show [--portfolio NAME]
    uv run portfolio.py delete "Portfolio Name"
    uv run portfolio.py rename "Old Name" "New Name"

    uv run portfolio.py add AAPL --quantity 10 --cost 150.00 [--portfolio NAME]
    uv run portfolio.py update AAPL --quantity 15 [--portfolio NAME]
    uv run portfolio.py remove AAPL [--portfolio NAME]
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
    return p / "portfolios.json"


def load_portfolios() -> dict:
    path = get_storage_path()
    if path.exists():
        return json.loads(path.read_text())
    return {"portfolios": {}, "active": None}


def save_portfolios(data: dict) -> None:
    get_storage_path().write_text(json.dumps(data, indent=2))


def get_active_portfolio(data: dict, name: str | None) -> str:
    if name:
        if name not in data["portfolios"]:
            print(f"❌ Portfolio '{name}' not found.", file=sys.stderr)
            sys.exit(1)
        return name
    if data.get("active"):
        return data["active"]
    portfolios = list(data["portfolios"].keys())
    if not portfolios:
        print("❌ No portfolios found. Create one with: portfolio.py create \"My Portfolio\"", file=sys.stderr)
        sys.exit(1)
    return portfolios[0]


# ─── AIsa API ────────────────────────────────────────────────────────────────

def get_client() -> OpenAI:
    api_key = os.environ.get("AISA_API_KEY")
    if not api_key:
        print("❌ Error: AISA_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    base_url = os.environ.get("AISA_BASE_URL", "https://api.aisa.one/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def fetch_prices(tickers: list[str]) -> dict[str, float]:
    """Fetch current prices for a list of tickers via AIsa API."""
    if not tickers:
        return {}
    client = get_client()
    model = os.environ.get("AISA_MODEL", "gpt-4o")
    ticker_str = ", ".join(tickers)
    prompt = (
        f"Fetch the current live price for each of these tickers: {ticker_str}\n\n"
        "Return ONLY a JSON object with ticker symbols as keys and current prices (numbers) as values.\n"
        "Example: {\"AAPL\": 195.50, \"BTC-USD\": 67234.10}\n"
        "No explanation. JSON only."
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a financial data fetcher. Use your tools to get current prices and return only JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        # Extract JSON from possible markdown fences
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())
    except Exception as e:
        print(f"⚠️  Could not fetch live prices: {e}", file=sys.stderr)
        return {}


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_create(args):
    data = load_portfolios()
    name = args.name
    if name in data["portfolios"]:
        print(f"❌ Portfolio '{name}' already exists.")
        sys.exit(1)
    data["portfolios"][name] = {"created": datetime.now().isoformat(), "assets": {}}
    if not data.get("active"):
        data["active"] = name
    save_portfolios(data)
    print(f"✅ Created portfolio: '{name}'")
    if data["active"] == name:
        print(f"   Set as active portfolio.")


def cmd_list(args):
    data = load_portfolios()
    if not data["portfolios"]:
        print("No portfolios yet. Create one with: portfolio.py create \"My Portfolio\"")
        return
    print("📁 Portfolios:")
    for name, pf in data["portfolios"].items():
        active_marker = " ← active" if name == data.get("active") else ""
        count = len(pf.get("assets", {}))
        print(f"  • {name} ({count} assets){active_marker}")


def cmd_add(args):
    data = load_portfolios()
    pf_name = get_active_portfolio(data, args.portfolio)
    ticker = args.ticker.upper()
    asset = {
        "ticker": ticker,
        "quantity": args.quantity,
        "cost_basis": args.cost,
        "added": datetime.now().isoformat(),
    }
    data["portfolios"][pf_name]["assets"][ticker] = asset
    save_portfolios(data)
    total = args.quantity * args.cost
    print(f"✅ Added {args.quantity} × {ticker} @ ${args.cost:.2f} (total: ${total:,.2f}) to '{pf_name}'")


def cmd_update(args):
    data = load_portfolios()
    pf_name = get_active_portfolio(data, args.portfolio)
    ticker = args.ticker.upper()
    if ticker not in data["portfolios"][pf_name]["assets"]:
        print(f"❌ {ticker} not found in '{pf_name}'")
        sys.exit(1)
    if args.quantity is not None:
        data["portfolios"][pf_name]["assets"][ticker]["quantity"] = args.quantity
    if args.cost is not None:
        data["portfolios"][pf_name]["assets"][ticker]["cost_basis"] = args.cost
    save_portfolios(data)
    print(f"✅ Updated {ticker} in '{pf_name}'")


def cmd_remove(args):
    data = load_portfolios()
    pf_name = get_active_portfolio(data, args.portfolio)
    ticker = args.ticker.upper()
    if ticker not in data["portfolios"][pf_name]["assets"]:
        print(f"❌ {ticker} not found in '{pf_name}'")
        sys.exit(1)
    del data["portfolios"][pf_name]["assets"][ticker]
    save_portfolios(data)
    print(f"✅ Removed {ticker} from '{pf_name}'")


def cmd_show(args):
    data = load_portfolios()
    pf_name = get_active_portfolio(data, args.portfolio)
    pf = data["portfolios"][pf_name]
    assets = pf.get("assets", {})

    if not assets:
        print(f"📁 Portfolio '{pf_name}' is empty. Add assets with: portfolio.py add AAPL --quantity 10 --cost 150")
        return

    print(f"\n📊 Portfolio: {pf_name}", file=sys.stderr)
    print("Fetching live prices via AIsa API...\n", file=sys.stderr)

    tickers = list(assets.keys())
    prices = fetch_prices(tickers)

    print(f"📊 Portfolio: {pf_name}")
    print(f"Created: {pf.get('created', 'unknown')[:10]}")
    print()
    print(f"{'Ticker':<12} {'Qty':>8} {'Cost':>10} {'Price':>10} {'Value':>12} {'P&L $':>12} {'P&L %':>8}")
    print("─" * 76)

    total_cost = 0.0
    total_value = 0.0

    for ticker, asset in assets.items():
        qty = asset["quantity"]
        cost = asset["cost_basis"]
        price = prices.get(ticker, None)
        cost_total = qty * cost

        if price is not None:
            value = qty * price
            pl_dollar = value - cost_total
            pl_pct = (pl_dollar / cost_total) * 100
            sign = "+" if pl_dollar >= 0 else ""
            print(f"{ticker:<12} {qty:>8.4f} {cost:>10.2f} {price:>10.2f} {value:>12,.2f} {sign}{pl_dollar:>11,.2f} {sign}{pl_pct:>7.1f}%")
            total_value += value
        else:
            print(f"{ticker:<12} {qty:>8.4f} {cost:>10.2f} {'N/A':>10} {'N/A':>12} {'N/A':>12} {'N/A':>8}")

        total_cost += cost_total

    print("─" * 76)
    total_pl = total_value - total_cost
    total_pl_pct = (total_pl / total_cost * 100) if total_cost > 0 else 0
    sign = "+" if total_pl >= 0 else ""
    print(f"{'TOTAL':<12} {'':>8} {'':>10} {'':>10} {total_value:>12,.2f} {sign}{total_pl:>11,.2f} {sign}{total_pl_pct:>7.1f}%")
    print(f"\n💰 Total Cost Basis: ${total_cost:,.2f}")
    print(f"📈 Total Value:      ${total_value:,.2f}")
    emoji = "📈" if total_pl >= 0 else "📉"
    print(f"{emoji} Total P&L:        {sign}${abs(total_pl):,.2f} ({sign}{total_pl_pct:.1f}%)")


def cmd_delete(args):
    data = load_portfolios()
    name = args.name
    if name not in data["portfolios"]:
        print(f"❌ Portfolio '{name}' not found.")
        sys.exit(1)
    del data["portfolios"][name]
    if data.get("active") == name:
        remaining = list(data["portfolios"].keys())
        data["active"] = remaining[0] if remaining else None
    save_portfolios(data)
    print(f"✅ Deleted portfolio: '{name}'")


def cmd_rename(args):
    data = load_portfolios()
    old, new = args.old_name, args.new_name
    if old not in data["portfolios"]:
        print(f"❌ Portfolio '{old}' not found.")
        sys.exit(1)
    data["portfolios"][new] = data["portfolios"].pop(old)
    if data.get("active") == old:
        data["active"] = new
    save_portfolios(data)
    print(f"✅ Renamed '{old}' → '{new}'")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Portfolio management with live AIsa pricing")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create a new portfolio")
    p_create.add_argument("name")

    sub.add_parser("list", help="List all portfolios")

    p_show = sub.add_parser("show", help="Show portfolio with live P&L")
    p_show.add_argument("--portfolio", default=None)

    p_add = sub.add_parser("add", help="Add asset to portfolio")
    p_add.add_argument("ticker")
    p_add.add_argument("--quantity", type=float, required=True)
    p_add.add_argument("--cost", type=float, required=True, help="Cost per share/unit")
    p_add.add_argument("--portfolio", default=None)

    p_update = sub.add_parser("update", help="Update asset quantity or cost")
    p_update.add_argument("ticker")
    p_update.add_argument("--quantity", type=float, default=None)
    p_update.add_argument("--cost", type=float, default=None)
    p_update.add_argument("--portfolio", default=None)

    p_remove = sub.add_parser("remove", help="Remove asset from portfolio")
    p_remove.add_argument("ticker")
    p_remove.add_argument("--portfolio", default=None)

    p_delete = sub.add_parser("delete", help="Delete a portfolio")
    p_delete.add_argument("name")

    p_rename = sub.add_parser("rename", help="Rename a portfolio")
    p_rename.add_argument("old_name")
    p_rename.add_argument("new_name")

    args = parser.parse_args()

    commands = {
        "create": cmd_create,
        "list": cmd_list,
        "show": cmd_show,
        "add": cmd_add,
        "update": cmd_update,
        "remove": cmd_remove,
        "delete": cmd_delete,
        "rename": cmd_rename,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
