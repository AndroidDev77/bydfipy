"""
Example usage of the BYDFiPy WebSocket client
"""

import os
import asyncio
from bydfipy import BydfiWebSocketClient

# Set your API key and secret here
API_KEY = os.environ.get("BYDFI_API_KEY", "")
API_SECRET = os.environ.get("BYDFI_API_SECRET", "")

# Example for public WebSocket streams
async def public_websocket_demo():
    print("\n=== Public WebSocket Demo ===\n")
    
    # Initialize WebSocket client
    ws_client = BydfiWebSocketClient()
    
    # Connect to WebSocket
    await ws_client.connect()
    
    # Subscribe to ticker for BTC-USDT
    print("Subscribing to BTC-USDT ticker...")
    await ws_client.subscribe_ticker("BTC-USDT")
    
    # Subscribe to trades for ETH-USDT
    print("Subscribing to ETH-USDT trades...")
    await ws_client.subscribe_trades("ETH-USDT")
    
    # Subscribe to 5-level orderbook for BTC-USDT
    print("Subscribing to BTC-USDT orderbook...")
    await ws_client.subscribe_orderbook("BTC-USDT", "5")
    
    # Listen for and print messages for 30 seconds
    print("Listening for messages (30 seconds)...")
    try:
        message_count = 0
        start_time = asyncio.get_event_loop().time()
        
        async for message in ws_client.messages():
            message_count += 1
            print(f"Received message {message_count}: {message['type']} - {message['stream']}")
            
            # Print first few messages with full data
            if message_count <= 5:
                print(f"Message data: {message['data']}")
            
            # Exit after 30 seconds
            if asyncio.get_event_loop().time() - start_time > 30:
                break
                
    finally:
        # Close connection
        await ws_client.close()
        print("WebSocket connection closed")


# Example for private WebSocket streams
async def private_websocket_demo():
    if not API_KEY or not API_SECRET:
        print("\n=== Private WebSocket Demo Skipped (No API Keys) ===\n")
        return
        
    print("\n=== Private WebSocket Demo ===\n")
    
    # Initialize WebSocket client with authentication
    ws_client = BydfiWebSocketClient(api_key=API_KEY, api_secret=API_SECRET)
    
    # Connect to WebSocket
    await ws_client.connect()
    
    # Subscribe to user account updates
    print("Subscribing to user account updates...")
    await ws_client.subscribe_user_data()
    
    # Listen for and print messages for 30 seconds
    print("Listening for messages (30 seconds)...")
    try:
        message_count = 0
        start_time = asyncio.get_event_loop().time()
        
        async for message in ws_client.messages():
            message_count += 1
            print(f"Received message {message_count}: {message['type']} - {message['stream']}")
            print(f"Message data: {message['data']}")
            
            # Exit after 30 seconds
            if asyncio.get_event_loop().time() - start_time > 30:
                break
                
    finally:
        # Close connection
        await ws_client.close()
        print("WebSocket connection closed")


async def main():
    # Run public WebSocket demo
    await public_websocket_demo()
    
    # Run private WebSocket demo (will be skipped if no API keys provided)
    await private_websocket_demo()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())