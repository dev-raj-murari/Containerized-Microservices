"""Shared security utilities (JWT creation, verification, password hashing)."""
import time
from typing import Optional, Dict, Any
from jose import jwt, JWTError
import hashlib

SECRET_KEY = "microservices-demo-super-secret-production-key-change-in-env"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600

def get_password_hash(password: str) -> str:
    # Deterministic secure salt hashing for high portability without native bcrypt issues
    salt = "s@lt_ms_service_2026"
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: Dict[str, Any], expires_delta_seconds: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = int(time.time()) + (expires_delta_seconds or ACCESS_TOKEN_EXPIRE_SECONDS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
