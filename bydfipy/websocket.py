"""
BYDFi API WebSocket client implementation
"""

import json
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator, Set, Tuple, cast
import websockets
import hmac
import hashlib
from .exceptions import (
    BydfiAPIError,
    BydfiRequestError,
    BydfiValueError,
    BydfiAuthError,
)
from .constants import (
    WEBSOCKET_API_URL,
    WS_TICKER,
    WS_TICKER_24HR,
    WS_ORDERBOOK,
    WS_TRADES,
    WS_KLINES,
)
from .utils import get_timestamp, generate_signature
from .types import WSMessage


logger = logging.getLogger(__name__)


class BydfiWebSocketClient:
    """
    BYDFi WebSocket Client
    
    This client provides access to real-time data through the BYDFi WebSocket API.
    
    Args:
        api_key: BYDFi API key for authenticated endpoints
        api_secret: BYDFi API secret for authenticated endpoints
        base_url: WebSocket base URL
        ping_interval: Interval for sending ping messages (seconds)
        ping_timeout: Timeout for ping responses (seconds)
        reconnect_delay: Delay before reconnecting after disconnect (seconds)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: str = WEBSOCKET_API_URL,
        ping_interval: int = 30,
        ping_timeout: int = 10,
        reconnect_delay: int = 5,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.reconnect_delay = reconnect_delay
        
        # WebSocket connection
        self.ws = None
        self.subscribed_streams: Set[str] = set()
        self.authenticated = False
        
        # Message queue for user consumption
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
        # Connection management
        self.running = False
        self.reconnect_task = None
        self.listener_task = None
        self.ping_task = None
        self.last_ping_time = 0
        self.last_pong_time = 0
        
    async def connect(self) -> None:
        """
        Connect to the WebSocket API
        """
        if self.ws and self.ws.open:
            return
            
        logger.info(f"Connecting to {self.base_url}")
        
        try:
            self.ws = await websockets.connect(self.base_url)
            self.running = True
            
            # Start listener and pinger tasks
            self.listener_task = asyncio.create_task(self._listener())
            self.ping_task = asyncio.create_task(self._pinger())
            
            # Re-subscribe to previously subscribed streams after reconnect
            if self.subscribed_streams:
                for stream in self.subscribed_streams:
                    await self._send({"method": "SUBSCRIBE", "params": [stream]})
                    
                # Re-authenticate if needed
                if self.authenticated and self.api_key and self.api_secret:
                    await self._authenticate()
                    
            logger.info("Connected to WebSocket")
            
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.ws = None
            self.running = False
            
            # Attempt to reconnect
            if not self.reconnect_task or self.reconnect_task.done():
                self.reconnect_task = asyncio.create_task(self._reconnect())
    
    async def _reconnect(self) -> None:
        """
        Handle reconnection to WebSocket API
        """
        logger.info(f"Attempting to reconnect in {self.reconnect_delay} seconds")
        await asyncio.sleep(self.reconnect_delay)
        await self.connect()
                
    async def _listener(self) -> None:
        """
        Listen for messages from WebSocket API
        """
        if not self.ws:
            return
            
        try:
            async for message in self.ws:
                try:
                    # Parse message
                    data = json.loads(message)
                    
                    # Handle different message types
                    if "error" in data:
                        error_msg = data.get("error", {}).get("msg", "Unknown error")
                        error_code = data.get("error", {}).get("code", 0)
                        logger.error(f"WebSocket error: [{error_code}] {error_msg}")
                        
                        # Don't add errors to the queue, but could be changed if needed
                        continue
                        
                    # Handle pong messages
                    if "result" in data and data.get("id") == "ping":
                        self.last_pong_time = time.time()
                        continue
                        
                    # Handle regular data messages
                    if "stream" in data:
                        # Process message and add to queue
                        processed_msg = self._process_message(data)
                        await self.message_queue.put(processed_msg)
                        
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse message: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.running = False
            
            # Clean up tasks
            if self.ping_task:
                self.ping_task.cancel()
                
            # Attempt to reconnect
            if not self.reconnect_task or self.reconnect_task.done():
                self.reconnect_task = asyncio.create_task(self._reconnect())
                
        except Exception as e:
            logger.error(f"WebSocket listener error: {e}")
            self.running = False
            
            # Clean up tasks
            if self.ping_task:
                self.ping_task.cancel()
                
            # Attempt to reconnect
            if not self.reconnect_task or self.reconnect_task.done():
                self.reconnect_task = asyncio.create_task(self._reconnect())
    
    async def _pinger(self) -> None:
        """
        Send periodic ping messages to keep connection alive
        """
        while self.running and self.ws and self.ws.open:
            try:
                # Send ping
                await self._send({"method": "ping", "id": "ping"})
                self.last_ping_time = time.time()
                
                # Wait for ping interval
                await asyncio.sleep(self.ping_interval)
                
                # Check if we got a pong response
                if self.last_ping_time > self.last_pong_time and \
                   time.time() - self.last_ping_time > self.ping_timeout:
                    logger.warning("Ping timeout, reconnecting")
                    await self.close()
                    
                    # Attempt to reconnect
                    if not self.reconnect_task or self.reconnect_task.done():
                        self.reconnect_task = asyncio.create_task(self._reconnect())
                    
            except Exception as e:
                logger.error(f"Error in ping loop: {e}")
                await asyncio.sleep(self.ping_interval)
    
    async def _send(self, data: Dict[str, Any]) -> None:
        """
        Send message to WebSocket API
        
        Args:
            data: Message data to send
        """
        if not self.ws or not self.ws.open:
            logger.warning("WebSocket not connected, reconnecting")
            await self.connect()
            
        if self.ws and self.ws.open:
            message = json.dumps(data)
            await self.ws.send(message)
            
    def _process_message(self, message: Dict[str, Any]) -> WSMessage:
        """
        Process WebSocket message
        
        Args:
            message: Raw WebSocket message
            
        Returns:
            Processed WebSocket message
        """
        stream = message.get("stream", "")
        data = message.get("data", {})
        timestamp = get_timestamp()
        
        # Determine message type from stream name
        msg_type = ""
        if "ticker" in stream:
            if "24h" in stream:
                msg_type = WS_TICKER_24HR
            else:
                msg_type = WS_TICKER
        elif "orderbook" in stream:
            msg_type = WS_ORDERBOOK
        elif "trades" in stream:
            msg_type = WS_TRADES
        elif "kline" in stream:
            msg_type = WS_KLINES
        elif "account" in stream:
            msg_type = "account"
        elif "order" in stream:
            msg_type = "order"
        
        return {
            "type": msg_type,
            "stream": stream,
            "data": data,
            "time": timestamp
        }
    
    async def _authenticate(self) -> None:
        """
        Authenticate WebSocket connection for private streams
        """
        if not self.api_key or not self.api_secret:
            raise BydfiValueError("API key and secret required for authentication")
            
        timestamp = get_timestamp()
        params = f"timestamp={timestamp}"
        signature = generate_signature(self.api_secret, params)
        
        auth_msg = {
            "method": "AUTH",
            "params": {
                "apiKey": self.api_key,
                "timestamp": timestamp,
                "signature": signature
            }
        }
        
        await self._send(auth_msg)
        self.authenticated = True
        
    async def subscribe(self, streams: List[str]) -> None:
        """
        Subscribe to WebSocket streams
        
        Args:
            streams: List of stream names to subscribe to
        """
        if not streams:
            return
            
        # Connect if not already connected
        if not self.ws or not self.ws.open:
            await self.connect()
            
        # Subscribe to streams
        subscribe_msg = {"method": "SUBSCRIBE", "params": streams}
        await self._send(subscribe_msg)
        
        # Add to subscribed streams set
        for stream in streams:
            self.subscribed_streams.add(stream)
            
    async def unsubscribe(self, streams: List[str]) -> None:
        """
        Unsubscribe from WebSocket streams
        
        Args:
            streams: List of stream names to unsubscribe from
        """
        if not streams:
            return
            
        # Connect if not already connected
        if not self.ws or not self.ws.open:
            return
            
        # Unsubscribe from streams
        unsubscribe_msg = {"method": "UNSUBSCRIBE", "params": streams}
        await self._send(unsubscribe_msg)
        
        # Remove from subscribed streams set
        for stream in streams:
            if stream in self.subscribed_streams:
                self.subscribed_streams.remove(stream)
                
    async def close(self) -> None:
        """
        Close WebSocket connection
        """
        self.running = False
        
        # Cancel tasks
        if self.listener_task and not self.listener_task.done():
            self.listener_task.cancel()
            
        if self.ping_task and not self.ping_task.done():
            self.ping_task.cancel()
            
        # Close WebSocket connection
        if self.ws and self.ws.open:
            await self.ws.close()
            
        # Clear subscriptions
        self.subscribed_streams.clear()
        self.authenticated = False
            
    async def messages(self) -> AsyncGenerator[WSMessage, None]:
        """
        Get messages from WebSocket API
        
        Yields:
            WebSocket messages as they arrive
        """
        while True:
            # Connect if not already connected
            if not self.ws or not self.ws.open:
                await self.connect()
                
            # Get message from queue
            try:
                message = await self.message_queue.get()
                yield message
                self.message_queue.task_done()
            except Exception as e:
                logger.error(f"Error getting message: {e}")
                await asyncio.sleep(0.1)
    
    # Convenience methods for subscribing to specific channels
    
    async def subscribe_ticker(self, symbol: str) -> None:
        """
        Subscribe to ticker updates for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
        """
        stream = f"{symbol.lower()}@ticker"
        await self.subscribe([stream])
        
    async def subscribe_ticker_24hr(self, symbol: str) -> None:
        """
        Subscribe to 24hr ticker updates for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
        """
        stream = f"{symbol.lower()}@ticker.24h"
        await self.subscribe([stream])
        
    async def subscribe_orderbook(self, symbol: str, depth: str = "10") -> None:
        """
        Subscribe to orderbook updates for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            depth: Orderbook depth ("5", "10", "20", "50", "100", "500", "1000")
        """
        stream = f"{symbol.lower()}@orderbook.{depth}"
        await self.subscribe([stream])
        
    async def subscribe_trades(self, symbol: str) -> None:
        """
        Subscribe to trade updates for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
        """
        stream = f"{symbol.lower()}@trades"
        await self.subscribe([stream])
        
    async def subscribe_klines(self, symbol: str, interval: str) -> None:
        """
        Subscribe to kline updates for a symbol and interval
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-USDT")
            interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
        """
        stream = f"{symbol.lower()}@kline_{interval}"
        await self.subscribe([stream])
        
    async def subscribe_user_data(self) -> None:
        """
        Subscribe to user data updates (requires authentication)
        """
        # Authenticate first if not already
        if not self.authenticated:
            await self._authenticate()
            
        # Subscribe to user data streams
        await self.subscribe(["account", "order"])