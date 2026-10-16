"""User Authentication & Profile Service."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.models import (
    UserRegisterRequest,
    UserResponse,
    TokenResponse,
    HealthCheckResponse,
    ServiceHealthStatus,
)
from shared.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)

app = FastAPI(
    title="User Authentication Service",
    version="1.0.0",
    description="Microservice responsible for user registrations, authentication, and JWT identity management.",
)

# In-memory storage for repository pattern demonstration
users_db: Dict[str, dict] = {}
users_by_email: Dict[str, str] = {}

security = HTTPBearer(auto_error=False)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload["sub"]
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return users_db[user_id]

@app.get("/health", response_model=HealthCheckResponse)
def health_check():
    return HealthCheckResponse(
        service="user-service",
        status=ServiceHealthStatus.HEALTHY,
        details={"total_users": len(users_db)},
    )

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegisterRequest):
    if user_data.email in users_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )
    user_id = str(uuid.uuid4())
    record = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": get_password_hash(user_data.password),
        "role": user_data.role,
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
    }
    users_db[user_id] = record
    users_by_email[user_data.email] = user_id
    return UserResponse(
        id=record["id"],
        username=record["username"],
        email=record["email"],
        role=record["role"],
        created_at=record["created_at"],
        is_active=record["is_active"],
    )

@app.post("/login", response_model=TokenResponse)
def login(user_data: UserRegisterRequest):
    user_id = users_by_email.get(user_data.email)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    record = users_db[user_id]
    if not verify_password(user_data.password, record["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token({"sub": user_id, "role": record["role"], "email": record["email"]})
    return TokenResponse(access_token=token)

@app.get("/users/me", response_model=UserResponse)
def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"],
        created_at=user["created_at"],
        is_active=user["is_active"],
    )

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: str):
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    record = users_db[user_id]
    return UserResponse(
        id=record["id"],
        username=record["username"],
        email=record["email"],
        role=record["role"],
        created_at=record["created_at"],
        is_active=record["is_active"],
    )
