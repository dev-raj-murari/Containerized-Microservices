"""Shared resilient HTTP client with timeouts, retry logic, and circuit breaker."""
import time
import httpx
from typing import Optional, Dict, Any

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_time_seconds: int = 10):
        self.failure_threshold = failure_threshold
        self.recovery_time_seconds = recovery_time_seconds
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_time_seconds:
                self.state = "HALF-OPEN"
                return True
            return False
        return True

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class ResilientHttpClient:
    def __init__(self, timeout: float = 5.0, retries: int = 2):
        self.timeout = timeout
        self.retries = retries
        self.breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(self, host: str) -> CircuitBreaker:
        if host not in self.breakers:
            self.breakers[host] = CircuitBreaker()
        return self.breakers[host]

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        host = url.split("/")[2] if "://" in url else "default"
        breaker = self.get_breaker(host)
        if not breaker.can_execute():
            raise CircuitBreakerOpenException(f"Circuit open for {host}. Requests temporarily blocked.")

        last_err = None
        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code >= 500:
                        breaker.record_failure()
                    else:
                        breaker.record_success()
                    return resp
            except Exception as e:
                last_err = e
                breaker.record_failure()
                if attempt == self.retries:
                    raise last_err
        raise last_err or Exception("Failed to perform request")
