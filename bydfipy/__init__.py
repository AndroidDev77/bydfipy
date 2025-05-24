"""
BYDFiPy - Python client for the BYDFi cryptocurrency exchange API
"""

from .client import BydfiClient
from .websocket import BydfiWebSocketClient
from .exceptions import (
    BydfiError,
    BydfiAPIError,
    BydfiRequestError,
    BydfiValueError,
    BydfiAuthError,
    BydfiRateLimitError,
)

__all__ = [
    "BydfiClient",
    "BydfiWebSocketClient",
    "BydfiError",
    "BydfiAPIError",
    "BydfiRequestError",
    "BydfiValueError",
    "BydfiAuthError",
    "BydfiRateLimitError",
]

__version__ = "0.1.0"