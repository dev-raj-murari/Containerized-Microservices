"""Pytest suite verifying all microservices, security, and edge gateway."""
import pytest
from fastapi.testclient import TestClient

from services.user_service.main import app as user_app
from services.order_service.main import app as order_app
from services.api_gateway.main import app as gateway_app
from shared.security import create_access_token, decode_access_token, verify_password, get_password_hash
from shared.circuit_breaker import CircuitBreaker

user_client = TestClient(user_app)
order_client = TestClient(order_app)
gateway_client = TestClient(gateway_app)

def test_user_service_health():
    response = user_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "user-service"

def test_order_service_health():
    response = order_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "order-service"

def test_api_gateway_health():
    response = gateway_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "api-gateway"

def test_password_hashing_and_verification():
    raw_pwd = "SuperSecretPassword123!"
    hashed = get_password_hash(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_generation_and_decoding():
    payload = {"sub": "usr-12345", "role": "admin", "email": "test@example.com"}
    token = create_access_token(payload, expires_delta_seconds=300)
    assert isinstance(token, str)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "usr-12345"
    assert decoded["role"] == "admin"
    assert decoded["email"] == "test@example.com"

def test_user_registration_and_login_flow():
    user_payload = {
        "username": "alice_dev",
        "email": "alice@example.com",
        "password": "PasswordAlice999!",
        "role": "user"
    }
    
    # 1. Register User
    reg_res = user_client.post("/register", json=user_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["username"] == "alice_dev"
    assert user_data["email"] == "alice@example.com"
    user_id = user_data["id"]

    # 2. Duplicate registration protection
    dup_res = user_client.post("/register", json=user_payload)
    assert dup_res.status_code == 400

    # 3. Login
    login_res = user_client.post("/login", json=user_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 4. Fetch authenticated profile
    profile_res = user_client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert profile_res.status_code == 200
    assert profile_res.json()["id"] == user_id

def test_order_creation_with_valid_and_invalid_tokens():
    # Attempt unauthenticated order creation
    order_payload = {
        "items": [
            {"product_id": "prod-1", "name": "Cloud Microservices Guide", "quantity": 2, "unit_price": 29.99}
        ],
        "shipping_address": "456 Tech Boulevard, San Francisco, CA"
    }
    unauth_res = order_client.post("/orders", json=order_payload)
    assert unauth_res.status_code == 401

    # Issue token and create order
    token = create_access_token({"sub": "user-cust-99"})
    auth_res = order_client.post(
        "/orders",
        json=order_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert auth_res.status_code == 201
    order_data = auth_res.json()
    assert order_data["user_id"] == "user-cust-99"
    assert order_data["total_amount"] == 59.98
    assert order_data["status"] == "CONFIRMED"
    order_id = order_data["id"]

    # Retrieve created order
    get_res = order_client.get(
        f"/orders/{order_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == order_id

def test_circuit_breaker_state_transitions():
    cb = CircuitBreaker(failure_threshold=2, recovery_time_seconds=1)
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True

    # Record first failure
    cb.record_failure()
    assert cb.state == "CLOSED"

    # Record second failure (reaches threshold)
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.can_execute() is False

    # Reset
    cb.record_success()
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True
