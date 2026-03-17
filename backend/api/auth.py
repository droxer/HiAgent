"""Authentication and rate limiting dependencies for the API layer."""

from __future__ import annotations

import time as _time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.settings import get_settings

_security = HTTPBearer(auto_error=False)


async def _verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> None:
    """Verify API key if one is configured. No-op when API_KEY is empty."""
    settings = get_settings()
    if not settings.API_KEY:
        return
    if credentials is None or credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class _RateLimiter:
    """Simple in-memory sliding-window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> bool:
        now = _time.monotonic()
        window_start = now - self._window
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        if len(self._requests[key]) >= self._max:
            return False
        self._requests[key].append(now)
        return True


_rate_limiter = _RateLimiter(max_requests=get_settings().RATE_LIMIT_PER_MINUTE)


async def _check_rate_limit(request: Request) -> None:
    """Enforce per-IP rate limiting (disabled in development)."""
    settings = get_settings()
    if settings.ENVIRONMENT == "development":
        return
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


common_dependencies = [Depends(_verify_api_key), Depends(_check_rate_limit)]
