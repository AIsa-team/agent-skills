import unittest
from unittest.mock import patch, MagicMock
import urllib.parse

from client import PredictionMarketAPIClient

class TestPredictionMarketAPIClient(unittest.TestCase):
    
    def setUp(self):
        self.api_key = "test_api_key_123"
        self.client = PredictionMarketAPIClient(api_key=self.api_key)
        self.client_no_auth = PredictionMarketAPIClient()

    def test_init_with_api_key(self):
        """Test client initialization with API key."""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.session.headers.get("Authorization"), f"Bearer {self.api_key}")

    def test_init_without_api_key(self):
        """Test client initialization without API key."""
        self.assertIsNone(self.client_no_auth.api_key)
        self.assertIsNone(self.client_no_auth.session.headers.get("Authorization"))

    @patch('client.requests.Session.request')
    def test_request_strips_none_params(self, mock_request):
        """Test that _request removes None values from params."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response

        self.client._request("GET", "/test", params={"a": 1, "b": None, "c": "test"})
        
        mock_request.assert_called_once_with(
            "GET", 
            "https://api.aisa.one/apis/v1/test", 
            params={"a": 1, "c": "test"}, 
            json=None
        )

    @patch('client.requests.Session.request')
    def test_request_raises_for_status(self, mock_request):
        """Test that _request raises an exception for HTTP errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_request.return_value = mock_response

        with self.assertRaises(Exception):
            self.client._request("GET", "/test")

    # ==========================================
    # Polymarket Endpoints Tests
    # ==========================================

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_polymarket_events(self, mock_request):
        """Test get_polymarket_events method."""
        self.client.get_polymarket_events(
            event_slug="test-event", 
            include_markets=True, 
            tags=["sports", "politics"]
        )
        mock_request.assert_called_once_with(
            "GET", 
            "/polymarket/events", 
            params={
                "event_slug": "test-event",
                "status": None,
                "include_markets": "true",
                "start_time": None,
                "end_time": None,
                "game_start_time": None,
                "limit": 10,
                "pagination_key": None,
                "tags": ["sports", "politics"]
            }
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_polymarket_markets(self, mock_request):
        """Test get_polymarket_markets method, including URL encoding of search."""
        self.client.get_polymarket_markets(
            search="bitcoin & crypto", 
            market_slug=["slug1", "slug2"]
        )
        mock_request.assert_called_once_with(
            "GET", 
            "/polymarket/markets", 
            params={
                "search": urllib.parse.quote("bitcoin & crypto"),
                "status": None,
                "min_volume": None,
                "limit": 10,
                "pagination_key": None,
                "start_time": None,
                "end_time": None,
                "market_slug": ["slug1", "slug2"]
            }
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_polymarket_orders(self, mock_request):
        """Test get_polymarket_orders method."""
        self.client.get_polymarket_orders(token_id="token123", limit=50)
        mock_request.assert_called_once_with(
            "GET", 
            "/polymarket/orders", 
            params={
                "market_slug": None,
                "condition_id": None,
                "token_id": "token123",
                "start_time": None,
                "end_time": None,
                "limit": 50,
                "pagination_key": None,
                "user": None
            }
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_polymarket_orderbooks(self, mock_request):
        """Test get_polymarket_orderbooks method."""
        self.client.get_polymarket_orderbooks(token_id="token123")
        mock_request.assert_called_once_with(
            "GET", 
            "/polymarket/orderbooks", 
            params={
                "token_id": "token123",
                "start_time": None,
                "end_time": None,
                "limit": 100,
                "pagination_key": None
            }
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_polymarket_activity(self, mock_request):
        """Test get_polymarket_activity method."""
        self.client.get_polymarket_activity(user="user123")
        mock_request.assert_called_once_with(
            "GET", 
            "/polymarket/activity", 
            params={
                "user": "user123",
                "start_time": None,
                "end_time": None,
                "market_slug": None,
                "condition_id": None,
                "limit": 100,
                "pagination_key": None
            }
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_polymarket_market_price(self, mock_request):
        """Test get_polymarket_market_price method."""
        self.client.get_polymarket_market_price(token_id="token123", at_time=123456789)
        mock_request.assert_called_once_with(
            "GET", 
            "/polymarket/market-price/token123", 
            params={"at_time": 123456789}
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_polymarket_candlesticks(self, mock_request):
        """Test get_polymarket_candlesticks method."""
        self.client.get_polymarket_candlesticks(condition_id="cond123", start_time=100, end_time=200)
        mock_request.assert_called_once_with(
            "GET", 
            "/polymarket/candlesticks/cond123", 
            params={
                "start_time": 100,
                "end_time": 200,
                "interval": 1
            }
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_polymarket_positions(self, mock_request):
        """Test get_polymarket_positions method."""
        self.client.get_polymarket_positions(wallet_address="0xABC")
        mock_request.assert_called_once_with(
            "GET", 
            "/polymarket/positions/wallet/0xABC", 
            params={
                "limit": 100,
                "pagination_key": None
            }
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_polymarket_wallet(self, mock_request):
        """Test get_polymarket_wallet method."""
        self.client.get_polymarket_wallet(eoa="0xDEF", with_metrics=True)
        mock_request.assert_called_once_with(
            "GET", 
            "/polymarket/wallet", 
            params={
                "eoa": "0xDEF",
                "proxy": None,
                "handle": None,
                "with_metrics": "true",
                "start_time": None,
                "end_time": None
            }
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_polymarket_wallet_pnl(self, mock_request):
        """Test get_polymarket_wallet_pnl method."""
        self.client.get_polymarket_wallet_pnl(wallet_address="0xABC", granularity="day")
        mock_request.assert_called_once_with(
            "GET", 
            "/polymarket/wallet/pnl/0xABC", 
            params={
                "granularity": "day",
                "start_time": None,
                "end_time": None
            }
        )

    # ==========================================
    # Kalshi Endpoints Tests
    # ==========================================

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_kalshi_markets(self, mock_request):
        """Test get_kalshi_markets method."""
        self.client.get_kalshi_markets(search="election", market_ticker=["TICK1"])
        mock_request.assert_called_once_with(
            "GET", 
            "/kalshi/markets", 
            params={
                "search": urllib.parse.quote("election"),
                "status": None,
                "min_volume": None,
                "limit": 10,
                "pagination_key": None,
                "market_ticker": ["TICK1"]
            }
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_kalshi_trades(self, mock_request):
        """Test get_kalshi_trades method."""
        self.client.get_kalshi_trades(ticker="TICK1")
        mock_request.assert_called_once_with(
            "GET", 
            "/kalshi/trades", 
            params={
                "ticker": "TICK1",
                "start_time": None,
                "end_time": None,
                "limit": 100,
                "pagination_key": None
            }
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_kalshi_market_price(self, mock_request):
        """Test get_kalshi_market_price method."""
        self.client.get_kalshi_market_price(market_ticker="TICK1")
        mock_request.assert_called_once_with(
            "GET", 
            "/kalshi/market-price/TICK1", 
            params={"at_time": None}
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_kalshi_orderbooks(self, mock_request):
        """Test get_kalshi_orderbooks method."""
        self.client.get_kalshi_orderbooks(ticker="TICK1")
        mock_request.assert_called_once_with(
            "GET", 
            "/kalshi/orderbooks", 
            params={
                "ticker": "TICK1",
                "start_time": None,
                "end_time": None,
                "limit": 100,
                "pagination_key": None
            }
        )

    # ==========================================
    # Matching Markets Endpoints Tests
    # ==========================================

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_matching_sports(self, mock_request):
        """Test get_matching_sports method."""
        self.client.get_matching_sports(polymarket_market_slug=["slug1"])
        mock_request.assert_called_once_with(
            "GET", 
            "/matching-markets/sports", 
            params={"polymarket_market_slug": ["slug1"]}
        )

    @patch('client.PredictionMarketAPIClient._request')
    def test_get_matching_sport_by_date(self, mock_request):
        """Test get_matching_sport_by_date method."""
        self.client.get_matching_sport_by_date(sport="nfl", date="2024-01-01")
        mock_request.assert_called_once_with(
            "GET", 
            "/matching-markets/sports/nfl", 
            params={"date": "2024-01-01"}
        )

    # ==========================================
    # Order Router Tests
    # ==========================================

    @patch('client.PredictionMarketAPIClient._request')
    def test_place_order(self, mock_request):
        """Test place_order method."""
        signed_order = {"price": 0.5, "size": 10}
        credentials = {"key": "val"}
        self.client.place_order(
            signed_order=signed_order, 
            order_type="LIMIT", 
            credentials=credentials, 
            client_order_id="my-id-123"
        )
        mock_request.assert_called_once_with(
            "POST", 
            "/polymarket/placeOrder", 
            json_data={
                "jsonrpc": "2.0",
                "method": "placeOrder",
                "id": "my-id-123",
                "params": {
                    "signedOrder": signed_order,
                    "orderType": "LIMIT",
                    "credentials": credentials,
                    "clientOrderId": "my-id-123"
                }
            }
        )

if __name__ == '__main__':
    unittest.main()
