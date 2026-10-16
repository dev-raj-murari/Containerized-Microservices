"""Order & Checkout Service."""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.models import (
    OrderCreateRequest,
    OrderResponse,
    HealthCheckResponse,
    ServiceHealthStatus,
)
from shared.security import decode_access_token

app = FastAPI(
    title="Order Processing Service",
    version="1.0.0",
    description="Microservice responsible for managing user orders and cart checkout state.",
)

orders_db: Dict[str, dict] = {}
security = HTTPBearer(auto_error=False)

def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required for order operations",
        )
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return payload["sub"]

@app.get("/health", response_model=HealthCheckResponse)
def health_check():
    return HealthCheckResponse(
        service="order-service",
        status=ServiceHealthStatus.HEALTHY,
        details={"total_orders": len(orders_db)},
    )

@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreateRequest, user_id: str = Depends(get_current_user_id)):
    if not order_data.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item",
        )
    
    order_id = str(uuid.uuid4())
    total_amount = sum(item.quantity * item.unit_price for item in order_data.items)
    
    record = {
        "id": order_id,
        "user_id": user_id,
        "items": [item.model_dump() for item in order_data.items],
        "total_amount": round(total_amount, 2),
        "status": "CONFIRMED",
        "shipping_address": order_data.shipping_address,
        "created_at": datetime.now(timezone.utc),
    }
    orders_db[order_id] = record
    return OrderResponse(**record)

@app.get("/orders", response_model=List[OrderResponse])
def list_user_orders(user_id: str = Depends(get_current_user_id)):
    user_orders = [o for o in orders_db.values() if o["user_id"] == user_id]
    return [OrderResponse(**o) for o in user_orders]

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order_by_id(order_id: str, user_id: str = Depends(get_current_user_id)):
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    order = orders_db[order_id]
    if order["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to access this order",
        )
    return OrderResponse(**order)
