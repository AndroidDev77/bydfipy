# BYDFiPy

A Python client library for the BYDFi cryptocurrency exchange API.

## Installation

```bash
pip install https://github.com/AndroidDev77/bydfipy/archive/refs/heads/main.zip
```

## Features

- Complete implementation of the BYDFi REST API
- WebSocket API support for real-time data
- Typed method signatures
- Robust error handling
- Rate limit management

## Usage

### REST API

```python
from bydfipy import BydfiClient

# Public endpoints (no authentication required)
client = BydfiClient()

# Get ticker information
ticker = client.get_ticker(symbol="BTC-USDT")
print(ticker)

# Get orderbook
orderbook = client.get_orderbook(symbol="BTC-USDT", limit=10)
print(orderbook)

# Authenticated endpoints
api_key = "your_api_key"
api_secret = "your_api_secret"
client = BydfiClient(api_key=api_key, api_secret=api_secret)

# Get account information
account_info = client.get_account_info()
print(account_info)

# Place an order
order = client.create_order(
    symbol="BTC-USDT",
    side="BUY",
    order_type="LIMIT",
    quantity=0.001,
    price=30000
)
print(order)
```

### WebSocket API

```python
import asyncio
from bydfipy import BydfiWebSocketClient

async def main():
    # Public WebSocket
    ws_client = BydfiWebSocketClient()
    
    # Subscribe to ticker channel
    await ws_client.subscribe_ticker("BTC-USDT")
    
    # Receive messages
    async for message in ws_client.messages():
        print(message)
        
    # Authenticated WebSocket (for user data)
    api_key = "your_api_key"
    api_secret = "your_api_secret"
    ws_client = BydfiWebSocketClient(api_key=api_key, api_secret=api_secret)
    
    # Subscribe to user account updates
    await ws_client.subscribe_user_data()

if __name__ == "__main__":
    asyncio.run(main())
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
