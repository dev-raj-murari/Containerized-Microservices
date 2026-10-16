"""Shared schemas, utilities, and security primitives across microservices."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
import uuid

class ServiceHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheckResponse(BaseModel):
    service: str
    status: ServiceHealthStatus
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Optional[Dict[str, Any]] = None

class TokenPayload(BaseModel):
    sub: str
    role: str = "user"
    exp: Optional[int] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6)
    role: str = "user"

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: datetime
    is_active: bool = True

class OrderItem(BaseModel):
    product_id: str
    name: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)

class OrderCreateRequest(BaseModel):
    items: List[OrderItem]
    shipping_address: str

class OrderResponse(BaseModel):
    id: str
    user_id: str
    items: List[OrderItem]
    total_amount: float
    status: str
    shipping_address: str
    created_at: datetime
