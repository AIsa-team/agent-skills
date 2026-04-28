#!/usr/bin/env python3
"""
Deep Analysis Example

This example shows how to perform a comprehensive deep analysis of a stock,
using all available data sources and multiple AI models.
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
    """Run comprehensive deep analysis."""
    
    # Get API key
    api_key = os.environ.get("AISA_API_KEY")
    if not api_key:
        print("Error: AISA_API_KEY environment variable not set")
        return
    
    # Stock to analyze
    ticker = input("Enter stock ticker to analyze (e.g., AAPL): ").strip().upper()
    if not ticker:
        ticker = "AAPL"
    
    print("\n" + "="*70)
    print("DEEP STOCK ANALYSIS")
    print("="*70)
    print(f"\nPerforming comprehensive analysis of {ticker}")
    print("This will use all available data sources and may take 30-60 seconds")
    print("Estimated cost: $0.05-0.10\n")
    
    # Initialize analyst
    analyst = AIsaStockAnalyst(api_key=api_key)
    
    try:
        # Run deep analysis with multiple models
        report = await analyst.analyze_stock(
            ticker=ticker,
            depth="deep",
            models=["gpt-4", "claude-3-opus"]  # Multi-model analysis
        )
        
        # Print comprehensive report
        print("\n" + "="*70)
        print("COMPREHENSIVE ANALYSIS REPORT")
        print("="*70)
        
        print(f"\nCompany: {report['metadata']['ticker']}")
        print(f"Analysis Date: {report['metadata']['analysis_date'][:10]}")
        print(f"Analyst: {report['metadata']['analyst']}")
        
        print("\n" + "-"*70)
        print("EXECUTIVE SUMMARY")
        print("-"*70)
        print(report['investment_summary'])
        
        print("\n" + "-"*70)
        print("FINANCIAL METRICS")
        print("-"*70)
        metrics = report['key_metrics']
        print(f"Market Cap:     ${metrics.get('market_cap', 0)/1e9:.2f}B")
        print(f"P/E Ratio:      {metrics.get('pe_ratio', 'N/A')}")
        print(f"Revenue:        ${metrics.get('revenue', 0)/1e9:.2f}B")
        print(f"EPS:            ${metrics.get('eps', 'N/A')}")
        print(f"Profit Margin:  {metrics.get('profit_margin', 0)*100:.1f}%")
        print(f"ROE:            {metrics.get('roe', 0)*100:.1f}%")
        
        print("\n" + "-"*70)
        print("SENTIMENT ANALYSIS")
        print("-"*70)
        sentiment = report['sentiment_analysis']
        print(f"Overall Sentiment: {sentiment.get('sentiment', 'N/A').upper()}")
        print(f"Confidence Level:  {sentiment.get('confidence', 'N/A')}")
        if sentiment.get('key_themes'):
            print(f"Key Themes:")
            for i, theme in enumerate(sentiment.get('key_themes', []), 1):
                print(f"  {i}. {theme}")
        print(f"\nSummary: {sentiment.get('summary', '')}")
        
        print("\n" + "-"*70)
        print("VALUATION ASSESSMENT")
        print("-"*70)
        valuation = report['valuation']
        print(f"Assessment:        {valuation.get('valuation_assessment', 'N/A').upper()}")
        if 'price_target_12m' in valuation:
            print(f"12M Price Target:  ${valuation['price_target_12m']:.2f}")
        if 'key_metrics' in valuation:
            print(f"\nValuation Metrics:")
            for key, value in valuation['key_metrics'].items():
                print(f"  {key}: {value}")
        print(f"\nReasoning: {valuation.get('reasoning', '')}")
        
        print("\n" + "-"*70)
        print("DATA SOURCES UTILIZED")
        print("-"*70)
        for source, count in report['data_sources'].items():
            print(f"  • {source}: {count}")
        
        # Print sample of raw data
        print("\n" + "-"*70)
        print("SAMPLE RAW DATA")
        print("-"*70)
        
        # Insider trades sample
        if 'insider_trades' in report['raw_data']:
            insider_data = report['raw_data']['insider_trades']
            if insider_data and 'data' in insider_data:
                print("\nRecent Insider Trades:")
                for trade in insider_data['data'][:3]:
                    print(f"  • {trade.get('insider_name', 'N/A')}: {trade.get('transaction_type', 'N/A')}")
        
        # News sample
        if 'news' in report['raw_data']:
            news_data = report['raw_data']['news']
            if news_data and 'data' in news_data:
                print("\nRecent News Headlines:")
                for article in news_data['data'][:3]:
                    print(f"  • {article.get('title', 'N/A')}")
        
        print("\n" + "="*70)
        print("DISCLAIMER")
        print("="*70)
        print(report['disclaimer'])
        
        # Save full report
        output_file = f"{ticker}_deep_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n" + "="*70)
        print(f"✓ Full report saved to: {output_file}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        await analyst.close()


if __name__ == "__main__":
    asyncio.run(main())
