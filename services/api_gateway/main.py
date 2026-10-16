"""API Gateway & Reverse Proxy Microservice.

Handles:
- Central routing to microservices
- Token authentication validation
- In-memory sliding-window Rate Limiting
- Circuit Breaker fallback mechanics
"""
import time
import os
from typing import Dict, List
from fastapi import FastAPI, Request, Response, HTTPException, status
import httpx
from shared.models import HealthCheckResponse, ServiceHealthStatus
from shared.circuit_breaker import ResilientHttpClient, CircuitBreakerOpenException

app = FastAPI(
    title="Central API Gateway",
    version="1.0.0",
    description="Edge reverse proxy router with rate limiting, circuit breaker, and health aggregation.",
)

# Service destinations (configurable via environment variables)
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")

http_client = ResilientHttpClient(timeout=5.0, retries=1)

# In-memory sliding rate limiter per client IP: max 60 requests per 60 seconds
RATE_LIMIT_MAX_REQUESTS = 60
RATE_LIMIT_WINDOW_SECONDS = 60
rate_limit_history: Dict[str, List[float]] = {}

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    # Bypass health checks from rate limiting
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Prune old timestamps
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    timestamps = [t for t in rate_limit_history.get(client_ip, []) if t > window_start]
    
    if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        return Response(
            content='{"detail": "Rate limit exceeded. Try again later."}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
        )

    timestamps.append(now)
    rate_limit_history[client_ip] = timestamps

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(RATE_LIMIT_MAX_REQUESTS - len(timestamps))
    return response

@app.get("/health", response_model=HealthCheckResponse)
def health_check():
    return HealthCheckResponse(
        service="api-gateway",
        status=ServiceHealthStatus.HEALTHY,
        details={
            "user_service_target": USER_SERVICE_URL,
            "order_service_target": ORDER_SERVICE_URL,
            "rate_limiter_active_ips": len(rate_limit_history),
        },
    )

@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_auth(request: Request, path: str):
    target_url = f"{USER_SERVICE_URL}/{path}"
    return await proxy_request(request, target_url)

@app.api_route("/api/v1/orders/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_orders(request: Request, path: str):
    target_url = f"{ORDER_SERVICE_URL}/orders/{path}" if path else f"{ORDER_SERVICE_URL}/orders"
    return await proxy_request(request, target_url)

async def proxy_request(request: Request, target_url: str) -> Response:
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers),
                media_type=resp.headers.get("content-type"),
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Downstream service unavailable: {str(e)}",
        )
