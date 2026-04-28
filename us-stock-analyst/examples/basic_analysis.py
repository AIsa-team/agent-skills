#!/usr/bin/env python3
"""
Basic Stock Analysis Example

This example shows how to perform a simple stock analysis using the AIsa Stock Analyst.
"""

import asyncio
import sys
import os

# Add parent directory to path to import stock_analyst
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.stock_analyst import AIsaStockAnalyst


async def main():
    """Run basic stock analysis."""
    
    # Get API key from environment
    api_key = os.environ.get("AISA_API_KEY")
    if not api_key:
        print("Error: AISA_API_KEY environment variable not set")
        print("Set it with: export AISA_API_KEY='your-key'")
        return
    
    # Initialize analyst
    analyst = AIsaStockAnalyst(api_key=api_key)
    
    try:
        # Analyze NVIDIA
        print("\n" + "="*70)
        print("BASIC STOCK ANALYSIS EXAMPLE")
        print("="*70)
        
        ticker = "NVDA"
        print(f"\nAnalyzing {ticker}...\n")
        
        # Run standard analysis
        report = await analyst.analyze_stock(
            ticker=ticker,
            depth="standard",
            models=["gpt-4"]
        )
        
        # Print key results
        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)
        
        print(f"\nTicker: {report['metadata']['ticker']}")
        print(f"Date: {report['metadata']['analysis_date'][:10]}")
        
        print("\nINVESTMENT SUMMARY:")
        print(report['investment_summary'])
        
        print("\nKEY METRICS:")
        metrics = report['key_metrics']
        if metrics.get('market_cap'):
            print(f"  Market Cap: ${metrics['market_cap']/1e9:.1f}B")
        if metrics.get('pe_ratio'):
            print(f"  P/E Ratio: {metrics['pe_ratio']:.2f}")
        if metrics.get('revenue'):
            print(f"  Revenue: ${metrics['revenue']/1e9:.1f}B")
        if metrics.get('profit_margin'):
            print(f"  Profit Margin: {metrics['profit_margin']*100:.1f}%")
        if metrics.get('roe'):
            print(f"  ROE: {metrics['roe']*100:.1f}%")
        
        print("\nSENTIMENT:")
        sentiment = report['sentiment_analysis']
        if isinstance(sentiment, dict):
            print(f"  Overall: {sentiment.get('sentiment', 'N/A').upper()}")
            print(f"  Confidence: {sentiment.get('confidence', 'N/A')}")
            if sentiment.get('key_themes'):
                print(f"  Key Themes: {', '.join(sentiment['key_themes'][:3])}")
            print(f"  {sentiment.get('summary', '')}")
        else:
            print(f"  {sentiment}")
        
        print("\nVALUATION:")
        valuation = report['valuation']
        if isinstance(valuation, dict):
            print(f"  Assessment: {valuation.get('valuation_assessment', 'N/A').upper()}")
            if 'price_target_12m' in valuation:
                print(f"  12M Price Target: ${valuation['price_target_12m']:.2f}")
            print(f"  {valuation.get('reasoning', '')}")
        else:
            print(f"  {valuation}")
        
        print("\nDATA SOURCES USED:")
        for source, count in report['data_sources'].items():
            print(f"  {source}: {count}")
        
        print("\n" + "="*70)
        print(report['disclaimer'])
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        await analyst.close()


if __name__ == "__main__":
    asyncio.run(main())
