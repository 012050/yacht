"""
??: Rate limiting, ?? ??, CSRF ??
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status

limiter = Limiter(key_func=get_remote_address)


def handle_rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="?? ?? ?????. ?? ? ?? ?????.",
    )
