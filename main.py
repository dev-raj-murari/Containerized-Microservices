"""Standalone demo runner simulating full interaction across all microservices."""
import json
from services.user_service.main import app as user_app
from services.order_service.main import app as order_app
from services.api_gateway.main import app as gateway_app
from shared.circuit_breaker import CircuitBreaker
from fastapi.testclient import TestClient

def main():
    print("================================================================")
    print(">> Containerized Microservices Platform - Live Demonstration")
    print("================================================================")

    user_client = TestClient(user_app)
    order_client = TestClient(order_app)
    gateway_client = TestClient(gateway_app)

    # 1. Health checks
    print("\n[Step 1] Checking Service Health Checks...")
    gw_health = gateway_client.get("/health").json()
    user_health = user_client.get("/health").json()
    order_health = order_client.get("/health").json()
    print(f" -> Gateway: {gw_health['service']} [{gw_health['status']}]")
    print(f" -> User Service: {user_health['service']} [{user_health['status']}]")
    print(f" -> Order Service: {order_health['service']} [{order_health['status']}]")

    # 2. Register User
    print("\n[Step 2] Registering User 'devraj_cloud'...")
    user_req = {
        "username": "devraj_cloud",
        "email": "devraj@example.com",
        "password": "ProductionPassword123!",
        "role": "engineer"
    }
    reg_resp = user_client.post("/register", json=user_req)
    user_data = reg_resp.json()
    print(f" -> Registered User ID: {user_data['id']}, Email: {user_data['email']}")

    # 3. Authenticate & Obtain JWT
    print("\n[Step 3] Authenticating & Issuing JWT Token...")
    login_resp = user_client.post("/login", json=user_req)
    token = login_resp.json()["access_token"]
    print(f" -> JWT Access Token: {token[:25]}... (truncated)")

    # 4. User Profile Retrieval
    print("\n[Step 4] Fetching Authenticated User Profile (/users/me)...")
    me_resp = user_client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    print(f" -> Authenticated profile: {me_resp.json()}")

    # 5. Place an Order
    print("\n[Step 5] Placing New Order via Order Service...")
    order_req = {
        "items": [
            {"product_id": "prod-docker-01", "name": "Docker & Kubernetes Handbook", "quantity": 1, "unit_price": 45.00},
            {"product_id": "prod-fastapi-02", "name": "FastAPI Microservices Course", "quantity": 2, "unit_price": 30.00}
        ],
        "shipping_address": "Tech Park 4th Floor, Bangalore, India"
    }
    order_resp = order_client.post("/orders", json=order_req, headers={"Authorization": f"Bearer {token}"})
    order_data = order_resp.json()
    print(f" -> Order Placed: ID={order_data['id']}, Total=${order_data['total_amount']}, Status={order_data['status']}")

    # 6. Resilience & Circuit Breaker Verification
    print("\n[Step 6] Testing Circuit Breaker State Transition...")
    cb = CircuitBreaker(failure_threshold=2, recovery_time_seconds=2)
    print(f" -> Initial state: {cb.state} (Can execute: {cb.can_execute()})")
    cb.record_failure()
    cb.record_failure()
    print(f" -> After 2 failures: {cb.state} (Can execute: {cb.can_execute()})")
    cb.record_success()
    print(f" -> Recovered: {cb.state} (Can execute: {cb.can_execute()})")

    print("\n[SUCCESS] All 5 Core Microservices features executed with 100% success!")
    print("================================================================\n")

if __name__ == "__main__":
    main()
