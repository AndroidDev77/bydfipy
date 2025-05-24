"""
Example usage of the BYDFiPy REST API client
"""

import os
import time
import json
from bydfipy import BydfiClient

# Set your API key and secret here
API_KEY = os.environ.get("BYDFI_API_KEY", "")
API_SECRET = os.environ.get("BYDFI_API_SECRET", "")

# Demo for public endpoints
def public_endpoints_demo():
    print("\n=== Public Endpoints Demo ===\n")
    
    # Initialize client (no auth required for public endpoints)
    client = BydfiClient()
    
    # Test connectivity
    ping_response = client.ping()
    print(f"Ping: {ping_response}")
    
    # Get server time
    time_response = client.get_server_time()
    print(f"Server time: {time_response}")
    
    # Get exchange information
    exchange_info = client.get_exchange_info()
    print(f"Exchange info (symbols count): {len(exchange_info.get('symbols', []))}")
    
    # Get ticker for BTC-USDT
    ticker = client.get_ticker(symbol="BTC-USDT")
    print(f"BTC-USDT ticker: {ticker}")
    
    # Get 24hr ticker for BTC-USDT
    ticker_24hr = client.get_ticker_24hr(symbol="BTC-USDT")
    print(f"BTC-USDT 24hr ticker: {ticker_24hr}")
    
    # Get orderbook for BTC-USDT
    orderbook = client.get_orderbook(symbol="BTC-USDT", limit=5)
    print(f"BTC-USDT orderbook: {orderbook}")
    
    # Get recent trades for BTC-USDT
    trades = client.get_recent_trades(symbol="BTC-USDT", limit=5)
    print(f"BTC-USDT recent trades: {trades}")
    
    # Get klines/candlestick data for BTC-USDT
    klines = client.get_klines(
        symbol="BTC-USDT", 
        interval="1h",
        limit=5
    )
    print(f"BTC-USDT 1h klines: {klines}")


# Demo for private/authenticated endpoints
def private_endpoints_demo():
    if not API_KEY or not API_SECRET:
        print("\n=== Private Endpoints Demo Skipped (No API Keys) ===\n")
        return
        
    print("\n=== Private Endpoints Demo ===\n")
    
    # Initialize client with authentication
    client = BydfiClient(api_key=API_KEY, api_secret=API_SECRET)
    
    # Get account information
    account_info = client.get_account_info()
    print(f"Account info: {account_info}")
    
    # Get account balance
    balances = client.get_account_balance()
    print(f"Account balances: {balances}")
    
    # Get open orders
    open_orders = client.get_open_orders(symbol="BTC-USDT")
    print(f"Open orders for BTC-USDT: {open_orders}")
    
    # Place a test limit order
    # Note: This is commented out to avoid actually placing orders
    # Uncomment to test if you want to place real orders
    """
    order = client.create_order(
        symbol="BTC-USDT",
        side="BUY",
        type="LIMIT",
        timeInForce="GTC",
        quantity=0.001,
        price=20000.0
    )
    print(f"Placed order: {order}")
    
    # Cancel the order
    canceled_order = client.cancel_order(
        symbol="BTC-USDT",
        order_id=order["orderId"]
    )
    print(f"Canceled order: {canceled_order}")
    """
    
    # Get order history
    orders = client.get_all_orders(
        symbol="BTC-USDT",
        limit=5
    )
    print(f"Order history for BTC-USDT: {orders}")
    
    # Get trade history
    trades = client.get_my_trades(
        symbol="BTC-USDT",
        limit=5
    )
    print(f"Trade history for BTC-USDT: {trades}")


if __name__ == "__main__":
    # Run public endpoints demo
    public_endpoints_demo()
    
    # Run private endpoints demo (will be skipped if no API keys provided)
    private_endpoints_demo()