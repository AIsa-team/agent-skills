import requests
import urllib.parse
from typing import Dict, Any, Optional, List, Union

class PredictionMarketAPIClient:
    """
    Client for the AIsa API proxy for prediction market data.
    Provides access to Polymarket, Kalshi, and Matching Markets.
    """
    
    BASE_URL = "https://api.aisa.one/apis/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AIsa API proxy client.
        
        Args:
            api_key: Optional API key. Can be passed in headers or query params.
        """
        self.api_key = api_key
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            
    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.BASE_URL}{endpoint}"
        
        # Clean up None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}
            
        response = self.session.request(method, url, params=params, json=json_data)
        response.raise_for_status()
        return response.json()

    # ==========================================
    # Polymarket Endpoints
    # ==========================================

    def get_polymarket_events(self, event_slug: Optional[str] = None, tags: Optional[List[str]] = None, 
                              status: Optional[str] = None, include_markets: Optional[bool] = None,
                              start_time: Optional[int] = None, end_time: Optional[int] = None,
                              game_start_time: Optional[int] = None, limit: int = 10, 
                              pagination_key: Optional[str] = None) -> Dict[str, Any]:
        """List events on Polymarket with filtering."""
        params = {
            "event_slug": event_slug,
            "status": status,
            "include_markets": str(include_markets).lower() if include_markets is not None else None,
            "start_time": start_time,
            "end_time": end_time,
            "game_start_time": game_start_time,
            "limit": limit,
            "pagination_key": pagination_key
        }
        if tags:
            params["tags"] = tags
            
        return self._request("GET", "/polymarket/events", params=params)

    def get_polymarket_markets(self, market_slug: Optional[List[str]] = None, event_slug: Optional[List[str]] = None,
                               condition_id: Optional[List[str]] = None, token_id: Optional[List[str]] = None,
                               tags: Optional[List[str]] = None, search: Optional[str] = None,
                               status: Optional[str] = None, min_volume: Optional[float] = None,
                               limit: int = 10, pagination_key: Optional[str] = None,
                               start_time: Optional[int] = None, end_time: Optional[int] = None) -> Dict[str, Any]:
        """Find markets on Polymarket using various filters."""
        params = {
            "search": urllib.parse.quote(search) if search else None,
            "status": status,
            "min_volume": min_volume,
            "limit": limit,
            "pagination_key": pagination_key,
            "start_time": start_time,
            "end_time": end_time
        }
        
        # Add list parameters
        if market_slug: params["market_slug"] = market_slug
        if event_slug: params["event_slug"] = event_slug
        if condition_id: params["condition_id"] = condition_id
        if token_id: params["token_id"] = token_id
        if tags: params["tags"] = tags
            
        return self._request("GET", "/polymarket/markets", params=params)

    def get_polymarket_orders(self, market_slug: Optional[str] = None, condition_id: Optional[str] = None,
                              token_id: Optional[str] = None, start_time: Optional[int] = None,
                              end_time: Optional[int] = None, limit: int = 100,
                              pagination_key: Optional[str] = None, user: Optional[str] = None) -> Dict[str, Any]:
        """Fetches historical trade data (orders) on Polymarket."""
        params = {
            "market_slug": market_slug,
            "condition_id": condition_id,
            "token_id": token_id,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "pagination_key": pagination_key,
            "user": user
        }
        return self._request("GET", "/polymarket/orders", params=params)

    def get_polymarket_orderbooks(self, token_id: str, start_time: Optional[int] = None,
                                  end_time: Optional[int] = None, limit: int = 100,
                                  pagination_key: Optional[str] = None) -> Dict[str, Any]:
        """Fetches historical orderbook snapshots for a specific asset."""
        params = {
            "token_id": token_id,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "pagination_key": pagination_key
        }
        return self._request("GET", "/polymarket/orderbooks", params=params)

    def get_polymarket_activity(self, user: Optional[str] = None, start_time: Optional[int] = None,
                                end_time: Optional[int] = None, market_slug: Optional[str] = None,
                                condition_id: Optional[str] = None, limit: int = 100,
                                pagination_key: Optional[str] = None) -> Dict[str, Any]:
        """Fetches activity data including MERGES, SPLITS, and REDEEMS."""
        params = {
            "user": user,
            "start_time": start_time,
            "end_time": end_time,
            "market_slug": market_slug,
            "condition_id": condition_id,
            "limit": limit,
            "pagination_key": pagination_key
        }
        return self._request("GET", "/polymarket/activity", params=params)

    def get_polymarket_market_price(self, token_id: str, at_time: Optional[int] = None) -> Dict[str, Any]:
        """Fetches the current or historical market price for a market by token_id."""
        params = {"at_time": at_time}
        return self._request("GET", f"/polymarket/market-price/{token_id}", params=params)

    def get_polymarket_candlesticks(self, condition_id: str, start_time: int, end_time: int, interval: int = 1) -> Dict[str, Any]:
        """Fetches historical candlestick data for a market identified by condition_id."""
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "interval": interval
        }
        return self._request("GET", f"/polymarket/candlesticks/{condition_id}", params=params)

    def get_polymarket_positions(self, wallet_address: str, limit: int = 100, pagination_key: Optional[str] = None) -> Dict[str, Any]:
        """Fetches all Polymarket positions for a proxy wallet address."""
        params = {
            "limit": limit,
            "pagination_key": pagination_key
        }
        return self._request("GET", f"/polymarket/positions/wallet/{wallet_address}", params=params)

    def get_polymarket_wallet(self, eoa: Optional[str] = None, proxy: Optional[str] = None,
                              handle: Optional[str] = None, with_metrics: bool = False,
                              start_time: Optional[int] = None, end_time: Optional[int] = None) -> Dict[str, Any]:
        """Fetches wallet information."""
        params = {
            "eoa": eoa,
            "proxy": proxy,
            "handle": handle,
            "with_metrics": str(with_metrics).lower(),
            "start_time": start_time,
            "end_time": end_time
        }
        return self._request("GET", "/polymarket/wallet", params=params)

    def get_polymarket_wallet_pnl(self, wallet_address: str, granularity: str,
                                  start_time: Optional[int] = None, end_time: Optional[int] = None) -> Dict[str, Any]:
        """Fetches the realized profit and loss (PnL) for a specific wallet address."""
        params = {
            "granularity": granularity,
            "start_time": start_time,
            "end_time": end_time
        }
        return self._request("GET", f"/polymarket/wallet/pnl/{wallet_address}", params=params)

    # ==========================================
    # Kalshi Endpoints
    # ==========================================

    def get_kalshi_markets(self, market_ticker: Optional[List[str]] = None, event_ticker: Optional[List[str]] = None,
                           search: Optional[str] = None, status: Optional[str] = None,
                           min_volume: Optional[float] = None, limit: int = 10,
                           pagination_key: Optional[str] = None) -> Dict[str, Any]:
        """Find markets on Kalshi."""
        params = {
            "search": urllib.parse.quote(search) if search else None,
            "status": status,
            "min_volume": min_volume,
            "limit": limit,
            "pagination_key": pagination_key
        }
        if market_ticker: params["market_ticker"] = market_ticker
        if event_ticker: params["event_ticker"] = event_ticker
            
        return self._request("GET", "/kalshi/markets", params=params)

    def get_kalshi_trades(self, ticker: Optional[str] = None, start_time: Optional[int] = None,
                          end_time: Optional[int] = None, limit: int = 100,
                          pagination_key: Optional[str] = None) -> Dict[str, Any]:
        """Fetches historical trade data for Kalshi markets."""
        params = {
            "ticker": ticker,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "pagination_key": pagination_key
        }
        return self._request("GET", "/kalshi/trades", params=params)

    def get_kalshi_market_price(self, market_ticker: str, at_time: Optional[int] = None) -> Dict[str, Any]:
        """Fetches the current market price for a Kalshi market."""
        params = {"at_time": at_time}
        return self._request("GET", f"/kalshi/market-price/{market_ticker}", params=params)

    def get_kalshi_orderbooks(self, ticker: str, start_time: Optional[int] = None,
                              end_time: Optional[int] = None, limit: int = 100,
                              pagination_key: Optional[str] = None) -> Dict[str, Any]:
        """Fetches historical orderbook snapshots for a specific Kalshi market."""
        params = {
            "ticker": ticker,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "pagination_key": pagination_key
        }
        return self._request("GET", "/kalshi/orderbooks", params=params)

    # ==========================================
    # Matching Markets Endpoints
    # ==========================================

    def get_matching_sports(self, polymarket_market_slug: Optional[List[str]] = None,
                            kalshi_event_ticker: Optional[List[str]] = None) -> Dict[str, Any]:
        """Find equivalent markets across platforms for sports events."""
        params = {}
        if polymarket_market_slug: params["polymarket_market_slug"] = polymarket_market_slug
        if kalshi_event_ticker: params["kalshi_event_ticker"] = kalshi_event_ticker
        return self._request("GET", "/matching-markets/sports", params=params)

    def get_matching_sport_by_date(self, sport: str, date: str) -> Dict[str, Any]:
        """Find equivalent markets across platforms for sports events by sport and date."""
        params = {"date": date}
        return self._request("GET", f"/matching-markets/sports/{sport}", params=params)

    # ==========================================
    # Order Router
    # ==========================================
    
    def place_order(self, signed_order: Dict[str, Any], order_type: str, 
                    credentials: Dict[str, str], client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Places an order on Polymarket via the AIsa API proxy.
        Note: This is a direct REST API call.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "placeOrder",
            "id": client_order_id or "unique-request-id",
            "params": {
                "signedOrder": signed_order,
                "orderType": order_type,
                "credentials": credentials
            }
        }
        if client_order_id:
            payload["params"]["clientOrderId"] = client_order_id
            
        return self._request("POST", "/polymarket/placeOrder", json_data=payload)

# Example usage:
if __name__ == "__main__":
    client = PredictionMarketAPIClient(api_key="your_api_key_here")
    # print(client.get_polymarket_market_price("19701256321759583954581192053894521654935987478209343000964756587964612528044"))
