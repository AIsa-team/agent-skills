#!/usr/bin/env python3
"""
Portfolio Batch Analysis Example

This example shows how to analyze multiple stocks (a portfolio) efficiently.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.stock_analyst import AIsaStockAnalyst


async def main():
    """Analyze a portfolio of stocks."""
    
    # Get API key
    api_key = os.environ.get("AISA_API_KEY")
    if not api_key:
        print("Error: AISA_API_KEY environment variable not set")
        return
    
    # Define portfolio
    portfolio = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META"]
    
    print("\n" + "="*70)
    print("PORTFOLIO BATCH ANALYSIS")
    print("="*70)
    print(f"\nAnalyzing {len(portfolio)} stocks: {', '.join(portfolio)}")
    print("Using 'quick' mode for speed and cost efficiency\n")
    
    # Initialize analyst
    analyst = AIsaStockAnalyst(api_key=api_key)
    
    try:
        results = []
        
        for ticker in portfolio:
            print(f"Analyzing {ticker}...")
            
            try:
                report = await analyst.analyze_stock(
                    ticker=ticker,
                    depth="quick",  # Quick mode for batch processing
                    models=["gpt-4"]
                )
                
                # Extract key info
                summary = {
                    "ticker": ticker,
                    "sentiment": report['sentiment_analysis'].get('sentiment', 'N/A'),
                    "sentiment_confidence": report['sentiment_analysis'].get('confidence', 'N/A'),
                    "market_cap": report['key_metrics'].get('market_cap'),
                    "pe_ratio": report['key_metrics'].get('pe_ratio'),
                    "profit_margin": report['key_metrics'].get('profit_margin'),
                    "roe": report['key_metrics'].get('roe')
                }
                
                results.append(summary)
                print(f"  ✓ {ticker} complete")
                
            except Exception as e:
                print(f"  ✗ {ticker} failed: {str(e)}")
                results.append({
                    "ticker": ticker,
                    "error": str(e)
                })
        
        # Print summary table
        print("\n" + "="*70)
        print("PORTFOLIO SUMMARY")
        print("="*70)
        
        print(f"\n{'Ticker':<8} {'Sentiment':<12} {'P/E':<8} {'Margin':<10} {'ROE':<8}")
        print("-" * 70)
        
        for r in results:
            if 'error' in r:
                print(f"{r['ticker']:<8} ERROR: {r['error'][:50]}")
                continue
                
            pe = f"{r['pe_ratio']:.1f}" if r['pe_ratio'] else "N/A"
            margin = f"{r['profit_margin']*100:.1f}%" if r['profit_margin'] else "N/A"
            roe = f"{r['roe']*100:.1f}%" if r['roe'] else "N/A"
            
            print(f"{r['ticker']:<8} {r['sentiment']:<12} {pe:<8} {margin:<10} {roe:<8}")
        
        # Count sentiment breakdown
        bullish = sum(1 for r in results if r.get('sentiment') == 'bullish')
        neutral = sum(1 for r in results if r.get('sentiment') == 'neutral')
        bearish = sum(1 for r in results if r.get('sentiment') == 'bearish')
        
        print("\n" + "-" * 70)
        print(f"Sentiment Breakdown: {bullish} Bullish, {neutral} Neutral, {bearish} Bearish")
        
        # Save results
        output_file = f"portfolio_analysis_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Full results saved to {output_file}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        await analyst.close()


if __name__ == "__main__":
    asyncio.run(main())
