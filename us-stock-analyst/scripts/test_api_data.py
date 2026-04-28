#!/usr/bin/env python3
"""
Simple test to show successfully retrieved data from AIsa APIs
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))
from scripts.stock_analyst import AIsaStockAnalyst


async def main():
    """Test API data retrieval."""
    
    api_key = os.environ.get("AISA_API_KEY")
    if not api_key:
        print("Error: AISA_API_KEY not set")
        return
    
    analyst = AIsaStockAnalyst(api_key=api_key)
    ticker = "AAPL"
    
    try:
        print(f"\n{'='*70}")
        print(f"Testing API Data Retrieval for {ticker}")
        print(f"{'='*70}\n")
        
        # Test individual API calls
        print("1. Testing Financial Metrics API...")
        try:
            metrics = await analyst._get_financial_metrics(ticker)
            print("   ✓ Success!")
            if "data" in metrics:
                data = metrics["data"]
                print(f"   - Market Cap: ${data.get('market_cap', 0)/1e9:.2f}B")
                print(f"   - P/E Ratio: {data.get('pe_ratio', 'N/A')}")
                print(f"   - Revenue: ${data.get('revenue', 0)/1e9:.2f}B")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
        
        print("\n2. Testing Stock News API...")
        try:
            news = await analyst._get_stock_news(ticker)
            print("   ✓ Success!")
            if "data" in news and news["data"]:
                print(f"   - Retrieved {len(news['data'])} news articles")
                print(f"   - Latest: {news['data'][0].get('title', 'N/A')[:60]}...")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
        
        print("\n3. Testing Twitter API...")
        try:
            twitter = await analyst._get_twitter_data(ticker)
            print("   ✓ Success!")
            if "data" in twitter:
                tweets_data = twitter["data"]
                if "tweets" in tweets_data:
                    print(f"   - Retrieved {len(tweets_data['tweets'])} tweets")
                else:
                    print(f"   - Twitter data structure: {list(tweets_data.keys())}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
        
        print("\n4. Testing YouTube API...")
        try:
            youtube = await analyst._get_youtube_content(ticker)
            print("   ✓ Success!")
            print(f"   - Response keys: {list(youtube.keys())}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
        
        print(f"\n{'='*70}")
        print("Test Complete!")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await analyst.close()


if __name__ == "__main__":
    asyncio.run(main())
