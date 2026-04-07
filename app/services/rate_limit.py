"""In-memory per-IP rate limiter (sliding window)."""

import time

RATE_LIMIT_MESSAGE = "Zu viele Anfragen, bitte später erneut versuchen."


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def check(self, ip: str) -> bool:
        """Registriert Request. True = erlaubt, False = Limit überschritten."""
        now = time.time()
        recent = [
            t for t in self._requests.get(ip, []) if now - t < self.window_seconds
        ]
        if len(recent) >= self.max_requests:
            self._requests[ip] = recent
            return False
        recent.append(now)
        self._requests[ip] = recent
        return True

    def reset(self) -> None:
        """Verwirft den gesamten Zustand (für Tests)."""
        self._requests.clear()


# Module-level singletons
bestellung_limiter = RateLimiter(max_requests=10, window_seconds=60)
login_limiter = RateLimiter(max_requests=5, window_seconds=60)
