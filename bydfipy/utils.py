"""
Utility functions for the BYDFi API client
"""

import time
import hmac
import hashlib
import urllib.parse
from typing import Dict, Any, Optional, Union, List, Tuple


def get_timestamp() -> int:
    """Get current timestamp in milliseconds"""
    return int(time.time() * 1000)


def generate_signature(secret_key: str, query_string: str) -> str:
    """
    Generate HMAC SHA256 signature for API request
    
    Args:
        secret_key: API secret key
        query_string: Request query string
        
    Returns:
        Signature as hexadecimal string
    """
    return hmac.new(
        secret_key.encode("utf-8"), 
        query_string.encode("utf-8"), 
        hashlib.sha256
    ).hexdigest()


def create_query_string(params: Dict[str, Any]) -> str:
    """
    Create URL encoded query string from parameters
    
    Args:
        params: Request parameters
        
    Returns:
        URL encoded query string
    """
    # Filter out None values
    filtered_params = {k: v for k, v in params.items() if v is not None}
    # Convert dict to query string
    return urllib.parse.urlencode(filtered_params)


def handle_rate_limits(headers: Dict[str, str]) -> Tuple[int, int]:
    """
    Extract rate limit info from response headers
    
    Args:
        headers: Response headers
    
    Returns:
        Tuple of (limit_used, limit_total)
    """
    limit_used = int(headers.get("X-MBX-USED-WEIGHT-1M", 0))
    limit_total = int(headers.get("X-MBX-LIMIT-WEIGHT-1M", 1200))
    return limit_used, limit_total