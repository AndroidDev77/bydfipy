"""
Tests for BYDFi API client
"""

import unittest
from unittest.mock import patch, MagicMock
import httpx

from bydfipy import BydfiClient
from bydfipy.exceptions import BydfiAPIError, BydfiValueError


class TestBydfiClient(unittest.TestCase):
    """Test cases for BydfiClient"""

    def setUp(self):
        self.client = BydfiClient()
        
    @patch('bydfipy.client.BydfiClient._request')
    def test_ping(self, mock_request):
        """Test ping endpoint"""
        mock_request.return_value = {}
        response = self.client.ping()
        
        mock_request.assert_called_once_with('GET', '/api/v1/ping')
        self.assertEqual(response, {})
        
    @patch('bydfipy.client.BydfiClient._request')
    def test_get_server_time(self, mock_request):
        """Test server time endpoint"""
        mock_request.return_value = {"serverTime": 1618047376123}
        response = self.client.get_server_time()
        
        mock_request.assert_called_once_with('GET', '/api/v1/time')
        self.assertEqual(response, {"serverTime": 1618047376123})
        
    @patch('bydfipy.client.BydfiClient._request')
    def test_get_ticker(self, mock_request):
        """Test ticker endpoint"""
        mock_data = {
            "symbol": "BTC-USDT",
            "priceChange": "-100.00000000",
            "priceChangePercent": "-0.500",
            "lastPrice": "19900.00000000",
            "lastQty": "0.00100000",
            "open": "20000.00000000",
            "high": "20100.00000000",
            "low": "19800.00000000",
            "volume": "100.00000000",
            "quoteVolume": "2000000.00000000",
            "openTime": 1618047376123,
            "closeTime": 1618133776123
        }
        mock_request.return_value = mock_data
        
        response = self.client.get_ticker(symbol="BTC-USDT")
        
        mock_request.assert_called_once_with('GET', '/api/v1/ticker', params={"symbol": "BTC-USDT"})
        self.assertEqual(response, mock_data)
        
    @patch('bydfipy.client.BydfiClient._request')
    def test_get_orderbook(self, mock_request):
        """Test orderbook endpoint"""
        mock_data = {
            "lastUpdateId": 12345,
            "bids": [
                {"price": "19800.00000000", "quantity": "0.10000000"},
                {"price": "19700.00000000", "quantity": "0.20000000"}
            ],
            "asks": [
                {"price": "19900.00000000", "quantity": "0.05000000"},
                {"price": "20000.00000000", "quantity": "0.10000000"}
            ]
        }
        mock_request.return_value = mock_data
        
        response = self.client.get_orderbook(symbol="BTC-USDT", limit=10)
        
        mock_request.assert_called_once_with('GET', '/api/v1/depth', 
                                           params={"symbol": "BTC-USDT", "limit": 10})
        self.assertEqual(response, mock_data)
        
    def test_create_order_missing_params(self):
        """Test create order with missing parameters"""
        with self.assertRaises(BydfiValueError):
            self.client.create_order(symbol="BTC-USDT", side="BUY")
            
    @patch('bydfipy.client.BydfiClient._request')
    def test_create_order(self, mock_request):
        """Test create order endpoint"""
        mock_data = {
            "symbol": "BTC-USDT",
            "orderId": 12345,
            "clientOrderId": "my_order_id",
            "transactTime": 1618047376123,
            "price": "19800.00000000",
            "origQty": "0.10000000",
            "executedQty": "0.00000000",
            "status": "NEW",
            "timeInForce": "GTC",
            "type": "LIMIT",
            "side": "BUY",
            "updateTime": 1618047376123,
            "isWorking": True
        }
        mock_request.return_value = mock_data
        
        # Set API key and secret for authenticated requests
        self.client.api_key = "test_key"
        self.client.api_secret = "test_secret"
        
        response = self.client.create_order(
            symbol="BTC-USDT",
            side="BUY",
            type="LIMIT",
            timeInForce="GTC",
            quantity=0.1,
            price=19800
        )
        
        mock_request.assert_called_once()
        self.assertEqual(response, mock_data)
        
    @patch('httpx.Client.get')
    def test_handle_api_error(self, mock_get):
        """Test API error handling"""
        # Mock an API error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "code": -1121,
            "msg": "Invalid symbol"
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response
        
        with self.assertRaises(BydfiAPIError) as context:
            self.client._request("GET", "/api/v1/ticker", params={"symbol": "INVALID-PAIR"})
            
        self.assertEqual(context.exception.code, -1121)
        self.assertEqual(context.exception.message, "Invalid symbol")
        

if __name__ == '__main__':
    unittest.main()