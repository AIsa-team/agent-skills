"""
US Stock Analyst Skill - Complete Implementation
AIsa Unified API Platform

Integrates ALL available AIsa APIs:
- Financial Data (prices, statements, metrics, analyst estimates, insider trades)
- Company News
- Web & Scholar Search
- Twitter Sentiment
- YouTube Content
- Multi-Model LLM Analysis

Base URL: https://api.aisa.one/apis/v1
LLM Base URL: https://api.aisa.one/v1
"""

import argparse
import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx

class AIsaStockAnalyst:
    """
    Professional stock analyst powered by AIsa's complete API suite.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.aisa.one/apis/v1"
        self.llm_base_url = "https://api.aisa.one/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=90.0)
    
    async def analyze_stock(
        self,
        ticker: str,
        depth: str = "standard",
        models: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for comprehensive stock analysis.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "NVDA")
            depth: Analysis depth - "quick", "standard", or "deep"
            models: Optional list of LLM models to use
            
        Returns:
            Complete analysis report
        """
        if models is None:
            models = ["gpt-4", "claude-3-opus"]
        
        print(f"\n{'='*60}")
        print(f"🔍 Analyzing {ticker.upper()}")
        print(f"{'='*60}\n")
        
        # Step 1: Gather data from all sources
        print("📊 Gathering data from multiple sources...")
        data = await self._gather_data(ticker, depth)
        
        # Step 2: Run AI analysis
        print("\n🤖 Running AI analysis...")
        analysis = await self._run_analysis(ticker, data, models)
        
        # Step 3: Synthesize report
        print("\n📝 Synthesizing report...")
        report = await self._synthesize_report(ticker, data, analysis)
        
        print(f"\n✅ Analysis complete!\n")
        
        return report
    
    async def _gather_data(self, ticker: str, depth: str) -> Dict[str, Any]:
        """Gather data from all AIsa APIs."""
        tasks = []
        
        # Core financial data (always fetch)
        tasks.append(("financial_metrics", self._get_financial_metrics(ticker)))
        tasks.append(("stock_news", self._get_stock_news(ticker)))
        tasks.append(("web_search", self._get_web_search(ticker)))
        tasks.append(("twitter", self._get_twitter_data(ticker)))
        
        # Standard depth adds more data
        if depth in ["standard", "deep"]:
            tasks.append(("analyst_estimates", self._get_analyst_estimates(ticker)))
            tasks.append(("insider_trades", self._get_insider_trades(ticker)))
            tasks.append(("youtube", self._get_youtube_content(ticker)))
        
        # Deep analysis adds everything
        if depth == "deep":
            tasks.append(("financial_statements", self._get_financial_statements(ticker)))
            tasks.append(("institutional", self._get_institutional_ownership(ticker)))
            tasks.append(("sec_filings", self._get_sec_filings(ticker)))
            tasks.append(("research", self._get_academic_research(ticker)))
        
        # Execute all API calls concurrently
        results = {}
        for name, task in tasks:
            try:
                results[name] = await task
                print(f"  ✓ {name.replace('_', ' ').title()}")
            except Exception as e:
                print(f"  ✗ {name.replace('_', ' ').title()}: {str(e)}")
                results[name] = {"error": str(e)}
        
        return results
    
    # ==================== Financial Data APIs ====================
    
    async def _get_financial_metrics(self, ticker: str) -> Dict:
        """Get comprehensive financial metrics."""
        response = await self.client.get(
            f"{self.base_url}/financial/financial-metrics/snapshot",
            params={"ticker": ticker},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_stock_news(self, ticker: str) -> Dict:
        """Get company news."""
        response = await self.client.get(
            f"{self.base_url}/financial/news",
            params={"ticker": ticker, "limit": 10},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_analyst_estimates(self, ticker: str) -> Dict:
        """Get analyst EPS estimates."""
        response = await self.client.get(
            f"{self.base_url}/financial/analyst/eps",
            params={"ticker": ticker, "period": "annual"},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_insider_trades(self, ticker: str) -> Dict:
        """Get insider trading data."""
        response = await self.client.get(
            f"{self.base_url}/financial/insider/trades",
            params={"ticker": ticker},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_institutional_ownership(self, ticker: str) -> Dict:
        """Get institutional ownership data."""
        response = await self.client.get(
            f"{self.base_url}/financial/institutional/ownership",
            params={"ticker": ticker},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_financial_statements(self, ticker: str) -> Dict:
        """Get all financial statements."""
        response = await self.client.get(
            f"{self.base_url}/financial/financial_statements/all",
            params={"ticker": ticker},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_sec_filings(self, ticker: str) -> Dict:
        """Get SEC filings."""
        response = await self.client.get(
            f"{self.base_url}/financial/sec/filings",
            params={"ticker": ticker},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== News & Search APIs ====================
    
    async def _get_web_search(self, ticker: str) -> Dict:
        """Search web for recent news."""
        response = await self.client.post(
            f"{self.base_url}/scholar/search/web",
            params={
                "query": f"{ticker} stock news analysis",
                "max_num_results": 10
            },
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_academic_research(self, ticker: str) -> Dict:
        """Search academic research."""
        response = await self.client.post(
            f"{self.base_url}/scholar/search/scholar",
            params={
                "query": f"{ticker} company analysis",
                "max_num_results": 5
            },
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Social Media APIs ====================
    
    async def _get_twitter_data(self, ticker: str) -> Dict:
        """Get Twitter mentions and sentiment."""
        response = await self.client.get(
            f"{self.base_url}/twitter/tweet/advanced_search",
            params={
                "query": f"${ticker} OR {ticker} stock",
                "queryType": "Latest"
            },
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_youtube_content(self, ticker: str) -> Dict:
        """Search YouTube for earnings calls and analysis."""
        response = await self.client.get(
            f"{self.base_url}/youtube/search",
            params={
                "engine": "youtube",
                "q": f"{ticker} earnings call latest",
                "gl": "us",
                "hl": "en"
            },
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== AI Analysis ====================
    
    async def _run_analysis(
        self,
        ticker: str,
        data: Dict,
        models: List[str]
    ) -> Dict[str, Any]:
        """Run multi-model AI analysis."""
        analyses = {}
        
        tasks = [
            ("summary", self._create_investment_summary(ticker, data, models[0])),
            ("sentiment", self._analyze_sentiment(ticker, data, models[0])),
            ("valuation", self._analyze_valuation(ticker, data, models[0]))
        ]
        
        for name, task in tasks:
            try:
                analyses[name] = await task
                print(f"  ✓ {name.capitalize()} analysis")
            except Exception as e:
                print(f"  ✗ {name.capitalize()}: {str(e)}")
                # Return proper structure for each analysis type
                if name == "summary":
                    analyses[name] = "Analysis unavailable due to API error."
                elif name == "sentiment":
                    analyses[name] = {
                        "sentiment": "neutral",
                        "confidence": "low",
                        "key_themes": [],
                        "summary": f"Sentiment analysis failed: {str(e)}"
                    }
                elif name == "valuation":
                    analyses[name] = {
                        "valuation_assessment": "uncertain",
                        "reasoning": f"Valuation analysis failed: {str(e)}"
                    }
        
        return analyses
    
    async def _create_investment_summary(
        self,
        ticker: str,
        data: Dict,
        model: str
    ) -> str:
        """Generate comprehensive investment summary."""
        # Extract key data
        metrics = data.get("financial_metrics", {}).get("data", {})
        news = data.get("stock_news", {}).get("data", [])[:5]
        web_results = data.get("web_search", {}).get("results", [])[:5]
        
        prompt = f"""Analyze {ticker} stock for investment purposes.

Financial Metrics:
{json.dumps(metrics, indent=2)}

Recent News:
{json.dumps(news, indent=2)}

Market Analysis:
{json.dumps(web_results, indent=2)}

Provide a comprehensive investment summary covering:
1. Business performance and recent developments
2. Financial health and key metrics
3. Growth opportunities
4. Key risks and concerns
5. Overall investment thesis

Be objective and data-driven. Limit response to 300 words."""

        response = await self.client.post(
            f"{self.llm_base_url}/chat/completions",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional equity analyst providing objective investment analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1500
            },
            headers=self.headers
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    async def _analyze_sentiment(
        self,
        ticker: str,
        data: Dict,
        model: str
    ) -> Dict:
        """Analyze sentiment from Twitter and news."""
        twitter_data = data.get("twitter", {})
        news_data = data.get("stock_news", {}).get("data", [])[:10]
        
        # Extract tweets
        tweets = []
        if "data" in twitter_data and "tweets" in twitter_data["data"]:
            tweets = [t.get("text", "") for t in twitter_data["data"]["tweets"][:10]]
        
        prompt = f"""Analyze sentiment for {ticker} based on:

Recent News Headlines:
{json.dumps([n.get("title", "") for n in news_data], indent=2)}

Recent Tweets:
{json.dumps(tweets, indent=2)}

Return JSON with:
- sentiment: "bullish", "neutral", or "bearish"
- confidence: "low", "medium", or "high"
- key_themes: [list of 3-5 main themes]
- summary: Brief 1-2 sentence explanation

Respond ONLY with valid JSON."""

        response = await self.client.post(
            f"{self.llm_base_url}/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 500
            },
            headers=self.headers
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        try:
            # Clean JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except:
            return {
                "sentiment": "neutral",
                "confidence": "low",
                "key_themes": [],
                "summary": "Unable to analyze sentiment"
            }
    
    async def _analyze_valuation(
        self,
        ticker: str,
        data: Dict,
        model: str
    ) -> Dict:
        """Analyze valuation and price target."""
        metrics = data.get("financial_metrics", {}).get("data", {})
        analyst = data.get("analyst_estimates", {}).get("data", {})
        
        prompt = f"""Provide valuation analysis for {ticker}:

Financial Metrics:
{json.dumps(metrics, indent=2)}

Analyst Estimates:
{json.dumps(analyst, indent=2)}

Return JSON with:
- current_price: number (if available)
- valuation_assessment: "undervalued", "fairly_valued", or "overvalued"
- key_metrics: object with P/E, PEG, etc
- price_target_12m: number (estimated)
- reasoning: brief explanation

Respond ONLY with valid JSON."""

        response = await self.client.post(
            f"{self.llm_base_url}/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 800
            },
            headers=self.headers
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except:
            return {
                "valuation_assessment": "uncertain",
                "reasoning": "Unable to determine valuation"
            }
    
    # ==================== Report Synthesis ====================
    
    async def _synthesize_report(
        self,
        ticker: str,
        data: Dict,
        analysis: Dict
    ) -> Dict[str, Any]:
        """Synthesize final report."""
        
        # Count data sources
        data_sources = {}
        for key, value in data.items():
            if not value.get("error"):
                source_name = key.replace("_", " ").title()
                if "data" in value:
                    data_sources[source_name] = len(value["data"]) if isinstance(value["data"], list) else "Available"
                elif "results" in value:
                    data_sources[source_name] = len(value["results"])
                else:
                    data_sources[source_name] = "Available"
        
        # Extract key metrics
        metrics = data.get("financial_metrics", {}).get("data", {})
        sentiment = analysis.get("sentiment", {})
        valuation = analysis.get("valuation", {})
        
        report = {
            "metadata": {
                "ticker": ticker.upper(),
                "analysis_date": datetime.now().isoformat(),
                "analyst": "AIsa Stock Analyst",
                "depth": "comprehensive"
            },
            
            "investment_summary": analysis.get("summary", "Analysis in progress..."),
            
            "key_metrics": {
                "market_cap": metrics.get("market_cap"),
                "pe_ratio": metrics.get("pe_ratio"),
                "revenue": metrics.get("revenue"),
                "eps": metrics.get("eps"),
                "profit_margin": metrics.get("profit_margin"),
                "roe": metrics.get("roe")
            },
            
            "sentiment_analysis": sentiment,
            
            "valuation": valuation,
            
            "data_sources": data_sources,
            
            "raw_data": {
                "financial_metrics": data.get("financial_metrics", {}),
                "news": data.get("stock_news", {}),
                "analyst_estimates": data.get("analyst_estimates", {}),
                "insider_trades": data.get("insider_trades", {}),
                "twitter": data.get("twitter", {}),
                "youtube": data.get("youtube", {}),
                "web_search": data.get("web_search", {})
            },
            
            "disclaimer": (
                "This analysis is for informational purposes only and should not be "
                "considered personalized investment advice. Please conduct your own "
                "research and consult with licensed financial advisors before making "
                "investment decisions."
            )
        }
        
        return report
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze a US stock with AIsa market, search, social, and LLM endpoints.",
    )
    parser.add_argument("--api-key", help="Override AISA_API_KEY instead of reading from the environment.")
    parser.add_argument("--ticker", help="Stock ticker symbol, e.g. AAPL or NVDA.")
    parser.add_argument(
        "--depth",
        choices=["quick", "standard", "deep"],
        default="standard",
        help="How many data sources to query before synthesis.",
    )
    parser.add_argument(
        "--models",
        default="gpt-4,claude-3-opus",
        help="Comma-separated LLM models used for summary/sentiment/valuation.",
    )
    parser.add_argument(
        "--output",
        help="Optional JSON output path. Defaults to <TICKER>_analysis_<YYYYMMDD>.json in the cwd.",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Print the final report as JSON instead of the human-readable summary.",
    )
    return parser


def resolve_runtime_inputs(args: argparse.Namespace) -> tuple[str, str, List[str], str, Optional[str], bool]:
    api_key = args.api_key or os.environ.get("AISA_API_KEY")
    ticker = (args.ticker or "").strip().upper()

    # Preserve the previous interactive flow as a fallback when the caller
    # does not provide CLI arguments or env vars.
    if not api_key:
        api_key = input("Enter your AIsa API key: ").strip()
    if not ticker:
        ticker = input("Enter stock ticker (e.g., NVDA, AAPL): ").strip().upper()

    if not api_key:
        raise ValueError("AISA API key is required.")
    if not ticker:
        raise ValueError("Ticker is required.")

    models = [item.strip() for item in args.models.split(",") if item.strip()]
    if not models:
        models = ["gpt-4", "claude-3-opus"]

    return api_key, ticker, models, args.depth, args.output, args.json_only


def print_report(report: Dict[str, Any]) -> None:
    print("\n" + "=" * 70)
    print("STOCK ANALYSIS REPORT")
    print("=" * 70)

    print(f"\nTICKER: {report['metadata']['ticker']}")
    print(f"DATE: {report['metadata']['analysis_date'][:10]}")

    print("\nINVESTMENT SUMMARY:")
    print(report["investment_summary"])

    print("\nKEY METRICS:")
    for key, value in report["key_metrics"].items():
        if value:
            print(f"  {key.replace('_', ' ').title()}: {value}")

    print("\nSENTIMENT:")
    sentiment = report["sentiment_analysis"]
    print(f"  {sentiment.get('sentiment', 'N/A').upper()}")
    print(f"  Confidence: {sentiment.get('confidence', 'N/A')}")
    print(f"  {sentiment.get('summary', '')}")

    print("\nVALUATION:")
    valuation = report["valuation"]
    print(f"  Assessment: {valuation.get('valuation_assessment', 'N/A').upper()}")
    if "price_target_12m" in valuation:
        try:
            print(f"  12M Target: ${valuation['price_target_12m']:.2f}")
        except (TypeError, ValueError):
            print(f"  12M Target: {valuation['price_target_12m']}")

    print("\nDATA SOURCES:")
    for source, count in report["data_sources"].items():
        print(f"  {source}: {count}")

    print("\n" + "=" * 70)
    print(report["disclaimer"])
    print("=" * 70 + "\n")


async def main() -> None:
    args = build_parser().parse_args()
    api_key, ticker, models, depth, output_path, json_only = resolve_runtime_inputs(args)

    analyst = AIsaStockAnalyst(api_key=api_key)

    try:
        report = await analyst.analyze_stock(ticker=ticker, depth=depth, models=models)

        if json_only:
            print(json.dumps(report, indent=2))
        else:
            print_report(report)

        filename = output_path or f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)

        print(f"✅ Full report saved to {filename}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        await analyst.close()


if __name__ == "__main__":
    asyncio.run(main())
