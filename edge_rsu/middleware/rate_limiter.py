"""
SmartV2X-CP Ultra — Rate Limiter Middleware
=============================================
Token-bucket rate limiting per client IP.
"""

import time
import logging
from collections import defaultdict
from typing import Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Per-IP token-bucket rate limiter.

    Each IP gets `max_requests` tokens that refill at 1 per (1/rate) seconds.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: float = 1.0):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        # {ip: (tokens_remaining, last_refill_time)}
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (max_requests, time.time())
        )

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        tokens, last_time = self._buckets[client_ip]
        now = time.time()

        # Refill tokens
        elapsed = now - last_time
        tokens = min(self.max_requests, tokens + elapsed * (self.max_requests / self.window))

        if tokens < 1:
            logger.warning("Rate limit exceeded for %s", client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."},
            )

        tokens -= 1
        self._buckets[client_ip] = (tokens, now)

        response = await call_next(request)
        return response
