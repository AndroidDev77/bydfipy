"""
BYDFi API client implementation
"""

import time
import logging
from typing import Dict, List, Optional, Any, Union, Tuple, cast
import httpx
from urllib.parse import urlencode
from .exceptions import (
    BydfiAPIError,
    BydfiRequestError,
    BydfiValueError,
    BydfiAuthError,
    BydfiRateLimitError,
)
from .constants import (
    REST_API_URL,
    GET, POST, DELETE,
    PING, SERVER_TIME, EXCHANGE_INFO, TICKER, TICKER_24HR, TICKERS,
    ORDERBOOK, RECENT_TRADES, HISTORICAL_TRADES, KLINES,
    ACCOUNT_INFO, BALANCE, DEPOSIT_ADDRESS, DEPOSIT_HISTORY,
    WITHDRAW, WITHDRAW_HISTORY, CREATE_ORDER, CANCEL_ORDER,
    CANCEL_ALL_ORDERS, ORDER_STATUS, OPEN_ORDERS, ALL_ORDERS, MY_TRADES,
    DEFAULT_RATE_LIMIT,
)
from .utils import get_timestamp, generate_signature, create_query_string, handle_rate_limits
from .types import (
    TickerData, OrderBookData, TradeData, KlineData, AccountData, BalanceData,
    OrderData, OrderListParams, CreateOrderParams, OrderSide, OrderType, OrderStatus,
    TimeInForce
)


logger = logging.getLogger(__name__)


class BydfiClient:
    """
    BYDFi API Client
    
    This client provides access to both public and private endpoints
    of the BYDFi cryptocurrency exchange API.
    
    Args:
        api_key: BYDFi API key for authenticated endpoints
        api_secret: BYDFi API secret for authenticated endpoints
        base_url: API base URL (default: https://api.bydfi.com)
        timeout: Request timeout in seconds (default: 10)
        proxies: Optional HTTP proxies
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: str = REST_API_URL,
        timeout: int = 10,
        proxies: Optional[Dict[str, str]] = None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Initialize HTTP client
        client_kwargs = {
            "timeout": timeout,
            "follow_redirects": True
        }
        
        # Add proxies if provided (httpx API changed in newer versions)
        if proxies:
            client_kwargs["proxies"] = proxies
            
        self.session = httpx.Client(**client_kwargs)
        
        # Rate limit tracking
        self.rate_limit_used = 0
        self.rate_limit_total = DEFAULT_RATE_LIMIT
        self.rate_limit_reset_time = 0
        
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle API response and handle errors
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed JSON response
            
        Raises:
            BydfiRequestError: If there was a network error
            BydfiAPIError: If the API returned an error
            BydfiAuthError: If there was an authentication error
            BydfiRateLimitError: If the rate limit was exceeded
        """
        # Update rate limit info
        if "X-MBX-USED-WEIGHT-1M" in response.headers:
            self.rate_limit_used, self.rate_limit_total = handle_rate_limits(response.headers)
        
        # Check for HTTP errors
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Handle API errors
            error_data = {}
            try:
                error_data = response.json()
            except ValueError:
                pass
            
            error_code = error_data.get("code", 0)
            error_msg = error_data.get("msg", str(e))
            status_code = response.status_code
            
            # Handle specific error types
            if status_code == 401:
                raise BydfiAuthError(error_code, error_msg, error_data, status_code)
            elif status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise BydfiRateLimitError(error_code, error_msg, error_data, status_code, retry_after)
            else:
                raise BydfiAPIError(error_code, error_msg, error_data, status_code)
        except httpx.RequestError as e:
            # Handle network-related errors
            raise BydfiRequestError(f"Request error: {str(e)}")
            
        # Parse and return JSON response
        try:
            return response.json()
        except ValueError:
            raise BydfiRequestError("Invalid JSON response")
            
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        is_signed: bool = False,
    ) -> Dict[str, Any]:
        """
        Make an API request
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: URL parameters
            data: POST data
            is_signed: Whether the request requires authentication
            
        Returns:
            API response as dict
            
        Raises:
            BydfiValueError: If authentication is required but not provided
            BydfiRequestError: If there was a network error
            BydfiAPIError: If the API returned an error
        """
        # Prepare parameters
        request_params = params or {}
        
        # Add timestamp for signed requests
        if is_signed:
            # Check if API keys are available
            if not self.api_key or not self.api_secret:
                raise BydfiValueError("API key and secret required for authenticated endpoints")
                
            # Add timestamp parameter
            request_params["timestamp"] = get_timestamp()
            
            # Create signature
            query_string = create_query_string(request_params)
            signature = generate_signature(self.api_secret, query_string)
            request_params["signature"] = signature
        
        # Prepare headers
        headers = {}
        if self.api_key and is_signed:
            headers["X-MBX-APIKEY"] = self.api_key
            
        # Prepare URL and make request
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == GET:
                response = self.session.get(url, params=request_params, headers=headers)
            elif method == POST:
                response = self.session.post(url, params=request_params, data=data, headers=headers)
            elif method == DELETE:
                response = self.session.delete(url, params=request_params, headers=headers)
            else:
                raise BydfiValueError(f"Invalid HTTP method: {method}")
                
            return self._handle_response(response)
            
        except httpx.RequestError as e:
            raise BydfiRequestError(f"Request failed: {str(e)}")

    # Public API Endpoints
    
    def ping(self) -> Dict[str, Any]:
        """
        Test connectivity to the API
        
        Returns:
            Empty dict on success
        """
        return self._request(GET, PING)
        
    def get_server_time(self) -> Dict[str, int]:
        """
        Get server time
        
        Returns:
            Dict containing server time in milliseconds
        """
        return self._request(GET, SERVER_TIME)
        
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information including trading rules and symbol information
        
        Returns:
            Exchange information
        """
        return self._request(GET, EXCHANGE_INFO)
        
    def get_ticker(self, symbol: str) -> TickerData:
        """
        Get price ticker for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            
        Returns:
            Ticker information
        """
        params = {"symbol": symbol}
        return cast(TickerData, self._request(GET, TICKER, params=params))
    
    def get_ticker_24hr(self, symbol: str) -> TickerData:
        """
        Get 24hr price change statistics for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            
        Returns:
            24hr ticker information
        """
        params = {"symbol": symbol}
        return cast(TickerData, self._request(GET, TICKER_24HR, params=params))
    
    def get_all_tickers(self) -> List[TickerData]:
        """
        Get price ticker for all symbols
        
        Returns:
            List of ticker information for all symbols
        """
        return cast(List[TickerData], self._request(GET, TICKERS))
    
    def get_orderbook(self, symbol: str, limit: Optional[int] = None) -> OrderBookData:
        """
        Get orderbook for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            limit: Number of bids/asks to return (default: 100, max: 1000)
            
        Returns:
            Orderbook data
        """
        params = {"symbol": symbol}
        if limit:
            params["limit"] = limit
        return cast(OrderBookData, self._request(GET, ORDERBOOK, params=params))
    
    def get_recent_trades(self, symbol: str, limit: Optional[int] = None) -> List[TradeData]:
        """
        Get recent trades for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            limit: Number of trades to return (default: 500, max: 1000)
            
        Returns:
            List of recent trades
        """
        params = {"symbol": symbol}
        if limit:
            params["limit"] = limit
        return cast(List[TradeData], self._request(GET, RECENT_TRADES, params=params))
    
    def get_historical_trades(
        self, 
        symbol: str, 
        limit: Optional[int] = None,
        from_id: Optional[int] = None
    ) -> List[TradeData]:
        """
        Get historical trades for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            limit: Number of trades to return (default: 500, max: 1000)
            from_id: TradeId to fetch from
            
        Returns:
            List of historical trades
        """
        params: Dict[str, Any] = {"symbol": symbol}
        if limit:
            params["limit"] = limit
        if from_id:
            params["fromId"] = from_id
        return cast(List[TradeData], self._request(GET, HISTORICAL_TRADES, params=params))
    
    def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[KlineData]:
        """
        Get candlestick data for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Number of candles to return (default: 500, max: 1000)
            
        Returns:
            List of candlesticks
        """
        params: Dict[str, Any] = {"symbol": symbol, "interval": interval}
        
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if limit:
            params["limit"] = limit
            
        klines_data = self._request(GET, KLINES, params=params)
        
        # Convert the raw kline data to proper format
        formatted_klines = []
        for kline in klines_data:
            formatted_klines.append({
                "openTime": kline[0],
                "open": kline[1],
                "high": kline[2],
                "low": kline[3],
                "close": kline[4],
                "volume": kline[5],
                "closeTime": kline[6],
                "quoteVolume": kline[7],
                "trades": kline[8],
                "takerBuyBaseVolume": kline[9],
                "takerBuyQuoteVolume": kline[10],
            })
            
        return cast(List[KlineData], formatted_klines)
        
    # Private API Endpoints
    
    def get_account_info(self) -> AccountData:
        """
        Get account information
        
        Returns:
            Account information
        """
        return cast(AccountData, self._request(GET, ACCOUNT_INFO, is_signed=True))
    
    def get_account_balance(self) -> List[BalanceData]:
        """
        Get account balance
        
        Returns:
            List of account balances
        """
        return cast(List[BalanceData], self._request(GET, BALANCE, is_signed=True))
    
    def get_deposit_address(self, coin: str, network: Optional[str] = None) -> Dict[str, Any]:
        """
        Get deposit address for a coin
        
        Args:
            coin: Coin name (e.g., "BTC")
            network: Blockchain network (optional)
            
        Returns:
            Deposit address information
        """
        params: Dict[str, Any] = {"coin": coin}
        if network:
            params["network"] = network
        return self._request(GET, DEPOSIT_ADDRESS, params=params, is_signed=True)
    
    def get_deposit_history(
        self,
        coin: Optional[str] = None,
        status: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get deposit history
        
        Args:
            coin: Coin name (e.g., "BTC")
            status: Deposit status (0: pending, 1: success, 2: credited but cannot withdraw)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Number of records to return
            
        Returns:
            Deposit history
        """
        params: Dict[str, Any] = {}
        
        if coin:
            params["coin"] = coin
        if status is not None:
            params["status"] = status
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if limit:
            params["limit"] = limit
            
        return self._request(GET, DEPOSIT_HISTORY, params=params, is_signed=True)
    
    def withdraw(
        self,
        coin: str,
        address: str,
        amount: Union[str, float],
        tag: Optional[str] = None,
        network: Optional[str] = None,
        memo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Withdraw crypto
        
        Args:
            coin: Coin name (e.g., "BTC")
            address: Withdrawal address
            amount: Withdrawal amount
            tag: Tag/memo/payment_id for coins like XRP, XMR, etc.
            network: Blockchain network
            memo: Additional memo for the transaction
            
        Returns:
            Withdrawal result
        """
        params: Dict[str, Any] = {
            "coin": coin,
            "address": address,
            "amount": str(amount),
        }
        
        if tag:
            params["tag"] = tag
        if network:
            params["network"] = network
        if memo:
            params["memo"] = memo
            
        return self._request(POST, WITHDRAW, params=params, is_signed=True)
    
    def get_withdraw_history(
        self,
        coin: Optional[str] = None,
        status: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get withdrawal history
        
        Args:
            coin: Coin name (e.g., "BTC")
            status: Withdrawal status (0: email sent, 1: canceled, 2: awaiting approval, 
                   3: rejected, 4: processing, 5: failure, 6: completed)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Number of records to return
            
        Returns:
            Withdrawal history
        """
        params: Dict[str, Any] = {}
        
        if coin:
            params["coin"] = coin
        if status is not None:
            params["status"] = status
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if limit:
            params["limit"] = limit
            
        return self._request(GET, WITHDRAW_HISTORY, params=params, is_signed=True)
    
    def create_order(self, **params: Any) -> OrderData:
        """
        Create a new order
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            side: Order side (BUY or SELL)
            type: Order type (LIMIT, MARKET, etc.)
            timeInForce: Time in force (GTC, IOC, FOK)
            quantity: Order quantity
            quoteOrderQty: Quote order quantity (for MARKET orders)
            price: Order price
            newClientOrderId: A unique client order ID
            stopPrice: Stop price
            icebergQty: Iceberg quantity
            
        Returns:
            Order information
        """
        # Validate required parameters
        required_params = ["symbol", "side", "type"]
        for param in required_params:
            if param not in params:
                raise BydfiValueError(f"Missing required parameter: {param}")
                
        # Validate order type specific parameters
        order_type = params.get("type")
        if order_type == "LIMIT":
            if "timeInForce" not in params:
                params["timeInForce"] = "GTC"
            if "price" not in params or "quantity" not in params:
                raise BydfiValueError("LIMIT orders require 'price' and 'quantity' parameters")
        elif order_type == "MARKET":
            if "quantity" not in params and "quoteOrderQty" not in params:
                raise BydfiValueError("MARKET orders require either 'quantity' or 'quoteOrderQty' parameters")
                
        return cast(OrderData, self._request(POST, CREATE_ORDER, params=params, is_signed=True))
    
    def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel an existing order
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            order_id: Order ID
            client_order_id: Client order ID
            
        Returns:
            Canceled order information
        """
        params: Dict[str, Any] = {"symbol": symbol}
        
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["clientOrderId"] = client_order_id
        else:
            raise BydfiValueError("Either order_id or client_order_id must be provided")
            
        return self._request(DELETE, CANCEL_ORDER, params=params, is_signed=True)
    
    def cancel_all_orders(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Cancel all open orders for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            
        Returns:
            List of canceled orders
        """
        params = {"symbol": symbol}
        return cast(List[Dict[str, Any]], self._request(DELETE, CANCEL_ALL_ORDERS, params=params, is_signed=True))
    
    def get_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> OrderData:
        """
        Get order status
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            order_id: Order ID
            client_order_id: Client order ID
            
        Returns:
            Order information
        """
        params: Dict[str, Any] = {"symbol": symbol}
        
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["clientOrderId"] = client_order_id
        else:
            raise BydfiValueError("Either order_id or client_order_id must be provided")
            
        return cast(OrderData, self._request(GET, ORDER_STATUS, params=params, is_signed=True))
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderData]:
        """
        Get open orders
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            
        Returns:
            List of open orders
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            
        return cast(List[OrderData], self._request(GET, OPEN_ORDERS, params=params, is_signed=True))
    
    def get_all_orders(self, **params: Any) -> List[OrderData]:
        """
        Get all orders (active, canceled or filled)
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT") (required)
            orderId: Order ID to get orders from
            startTime: Start time in milliseconds
            endTime: End time in milliseconds
            limit: Number of orders to return (default: 500, max: 1000)
            
        Returns:
            List of orders
        """
        # Validate required parameters
        if "symbol" not in params:
            raise BydfiValueError("Missing required parameter: symbol")
            
        return cast(List[OrderData], self._request(GET, ALL_ORDERS, params=params, is_signed=True))
    
    def get_my_trades(self, **params: Any) -> List[Dict[str, Any]]:
        """
        Get user's trade history
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT") (required)
            orderId: Order ID to get trades for
            startTime: Start time in milliseconds
            endTime: End time in milliseconds
            fromId: TradeId to fetch from
            limit: Number of trades to return (default: 500, max: 1000)
            
        Returns:
            List of trades
        """
        # Validate required parameters
        if "symbol" not in params:
            raise BydfiValueError("Missing required parameter: symbol")
            
        return cast(List[Dict[str, Any]], self._request(GET, MY_TRADES, params=params, is_signed=True))