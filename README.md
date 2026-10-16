# Containerized Microservices Platform 🚀

[![CI/CD Pipeline](https://github.com/dev-raj-murari/containerized-microservices/actions/workflows/ci.yml/badge.svg)](https://github.com/dev-raj-murari/containerized-microservices/actions)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)
![Pytest](https://img.shields.io/badge/pytest-passed-brightgreen.svg)

Production-grade, resilient, containerized Python microservices architecture built with **FastAPI**, **Docker**, **JWT Security**, **Rate Limiting**, **Circuit Breaker resilience**, and **Pytest**.

---

## 🏗️ Architecture Overview

```
                      +-------------------+
                      |   Client/Browser  |
                      +---------+---------+
                                |
                                v
               +---------------------------------+
               |   Central API Gateway (:8000)   |
               |  - Sliding-Window Rate Limiter  |
               |  - Reverse Proxy Routing        |
               |  - Circuit Breaker Protection   |
               +--------+---------------+--------+
                        |               |
         +--------------+               +---------------+
         v                                              v
+-------------------------------+             +----------------------------------+
|   User & Auth Service (:8001) |             |    Order Processing Service      |
|  - JWT Bearer Authentication  |             |             (:8002)              |
|  - Salted Password Hashing    |             |  - Checkout State Machine        |
|  - Profile & Role Management  |             |  - JWT-Secured Cart Validation   |
+-------------------------------+             +----------------------------------+
```

---

## 🌟 Top 20 Production Features Roadmap

### **Day 1: Initial Release (Implemented & Tested 100% ✅)**
1. **API Gateway & Central Reverse Proxy**: Intelligent reverse proxy dispatching traffic to downstream microservices with path forwarding.
2. **Stateless JWT Authentication & Salted Security**: End-to-end token issuance, verification, and salted password hashing.
3. **Resilient Circuit Breaker**: State-machine (Closed -> Open -> Half-Open) preventing downstream cascading failures under high latency.
4. **Sliding-Window IP Rate Limiter**: Gateway-level DDoS and throttle protection with dynamic `X-RateLimit-*` response headers.
5. **Comprehensive Pytest Suite & Health Checks**: Automated unit and integration testing covering all services, security, and lifecycle checks.

---

### **Day 2: Planned Release**
6. **Centralized Structured JSON Logging**: Correlation ID propagation across HTTP headers (`X-Correlation-ID`) across all microservices.
7. **Database-per-Service Persistence**: Async SQLAlchemy / SQLModel integration with migration scripts.
8. **Automated Docker Multi-Stage Builds**: Ultra-lean production container builds with Alpine/Slim bases.
9. **Centralized Configuration Management**: Pydantic `BaseSettings` reading environment variables and `.env` configs.
10. **Global Exception & Error Handling**: Standardized RFC-7807 error format across all services.

---

### **Day 3: Planned Release**
11. **Event-Driven Asynchronous Messaging**: Event broker publisher/consumer pattern (RabbitMQ / Redis pub-sub) for order created events.
12. **Prometheus Metrics Exporter**: `/metrics` scrapable endpoint on all microservices for Grafana visualization.
13. **Distributed Request Tracing**: OpenTelemetry trace context propagation.
14. **Service Discovery & Registry**: Dynamic service registration and health polling mechanism.
15. **Role-Based Access Control (RBAC)**: Fine-grained granular authorization decorators (`admin`, `operator`, `user`).

---

### **Day 4: Planned Release**
16. **Distributed Cache Integration**: High-speed Redis caching for hot user profiles and catalog data.
17. **Idempotency Key Middleware**: Guarantee safe order payment retries using unique `Idempotency-Key` headers.
18. **Dead Letter Queue (DLQ) & Retry Policy**: Automated message recovery for failed async background tasks.
19. **Kubernetes Helm Manifests**: Production deployment charts (Deployments, Services, ConfigMaps, Ingress).
20. **Security Hardening & Vault Secret Management**: Automated OWASP container scanning and secret isolation.

---

## 🚀 Quickstart & Local Verification

### 1. Run the Pytest Test Suite
```bash
# Set Python path and run pytest
pytest -v
```

### 2. Run the Live Architecture Demonstration
```bash
python main.py
```

### 3. Run with Docker Compose
```bash
docker-compose up --build
```

Access endpoints:
* **API Gateway**: `http://localhost:8000/docs`
* **User Service**: `http://localhost:8001/docs`
* **Order Service**: `http://localhost:8002/docs`
