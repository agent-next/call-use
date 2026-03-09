"""In-memory sliding window rate limiter."""

import time


class RateLimiter:
    """Sliding window rate limiter. Tracks calls per API key."""

    def __init__(self, max_calls: int = 10, window_seconds: int = 3600):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._calls: dict[str, list[float]] = {}

    def check(self, api_key: str) -> bool:
        """Return True if allowed, False if rate limited.
        Removes expired entries from window."""
        now = time.time()
        cutoff = now - self.window_seconds

        if api_key not in self._calls:
            self._calls[api_key] = []

        # Remove expired
        self._calls[api_key] = [t for t in self._calls[api_key] if t > cutoff]

        if len(self._calls[api_key]) >= self.max_calls:
            return False

        self._calls[api_key].append(now)
        return True
