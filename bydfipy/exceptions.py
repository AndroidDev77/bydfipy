"""
Exceptions for the BYDFi API client
"""
from typing import Optional, Dict, Any, Union


class BydfiError(Exception):
    """Base exception for BYDFi API"""
    pass


class BydfiValueError(BydfiError, ValueError):
    """Invalid parameter value error"""
    pass


class BydfiRequestError(BydfiError):
    """Request error (connection issues, timeout, etc.)"""
    pass


class BydfiAPIError(BydfiError):
    """API returned an error"""

    def __init__(
        self,
        code: int,
        message: str,
        response: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ):
        self.code = code
        self.message = message
        self.response = response or {}
        self.status_code = status_code
        super().__init__(f"API error {code}: {message}")


class BydfiAuthError(BydfiAPIError):
    """Authentication error"""
    pass


class BydfiRateLimitError(BydfiAPIError):
    """Rate limit exceeded error"""
    
    def __init__(
        self, 
        code: int, 
        message: str, 
        response: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        retry_after: Optional[int] = None
    ):
        self.retry_after = retry_after
        super().__init__(code, message, response, status_code)