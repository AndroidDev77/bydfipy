"""
Constants for the BYDFi API client
"""

# API Base URLs
REST_API_URL = "https://api.bydfi.com"
WEBSOCKET_API_URL = "wss://stream.bydfi.com/ws"

# API Endpoints
# Public
PING = "/api/v1/ping"
SERVER_TIME = "/api/v1/time"
EXCHANGE_INFO = "/api/v1/exchangeInfo"
TICKER = "/api/v1/ticker"
TICKER_24HR = "/api/v1/ticker/24hr"
TICKERS = "/api/v1/tickers"
ORDERBOOK = "/api/v1/depth"
RECENT_TRADES = "/api/v1/trades"
HISTORICAL_TRADES = "/api/v1/historicalTrades"
KLINES = "/api/v1/klines"

# Private - Account
ACCOUNT_INFO = "/api/v1/account"
BALANCE = "/api/v1/balance"
DEPOSIT_ADDRESS = "/api/v1/capital/deposit/address"
DEPOSIT_HISTORY = "/api/v1/capital/deposit/history"
WITHDRAW = "/api/v1/capital/withdraw"
WITHDRAW_HISTORY = "/api/v1/capital/withdraw/history"

# Private - Orders
CREATE_ORDER = "/api/v1/order"
CANCEL_ORDER = "/api/v1/order"
CANCEL_ALL_ORDERS = "/api/v1/openOrders"
ORDER_STATUS = "/api/v1/order"
OPEN_ORDERS = "/api/v1/openOrders"
ALL_ORDERS = "/api/v1/allOrders"
MY_TRADES = "/api/v1/myTrades"

# HTTP Methods
GET = "GET"
POST = "POST"
PUT = "PUT"
DELETE = "DELETE"

# WebSocket Channels
WS_TICKER = "ticker"
WS_TICKER_24HR = "ticker.24h"
WS_ORDERBOOK = "orderbook"
WS_TRADES = "trades"
WS_KLINES = "klines"

# Order Types
ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_MARKET = "MARKET"
ORDER_TYPE_STOP_LOSS = "STOP_LOSS"
ORDER_TYPE_STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
ORDER_TYPE_TAKE_PROFIT = "TAKE_PROFIT"
ORDER_TYPE_TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"

# Order Sides
SIDE_BUY = "BUY"
SIDE_SELL = "SELL"

# Time In Force
TIME_IN_FORCE_GTC = "GTC"  # Good Till Cancel
TIME_IN_FORCE_IOC = "IOC"  # Immediate Or Cancel
TIME_IN_FORCE_FOK = "FOK"  # Fill Or Kill

# Order Status
ORDER_STATUS_NEW = "NEW"
ORDER_STATUS_PARTIALLY_FILLED = "PARTIALLY_FILLED"
ORDER_STATUS_FILLED = "FILLED"
ORDER_STATUS_CANCELED = "CANCELED"
ORDER_STATUS_PENDING_CANCEL = "PENDING_CANCEL"
ORDER_STATUS_REJECTED = "REJECTED"
ORDER_STATUS_EXPIRED = "EXPIRED"

# Rate Limits
DEFAULT_RATE_LIMIT = 1200  # requests per minute