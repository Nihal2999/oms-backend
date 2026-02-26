# OMS - Order Management System

A production-ready REST API backend built with **FastAPI**, **PostgreSQL**, and **Redis**. Features JWT authentication, role-based access control, pagination, Redis caching, and cloud deployment with GitLab CI/CD.

---

## 🚀 Live Demo

**Swagger API URL:** https://oms-backend-i4kj.onrender.com/api

**GitHub URL:** https://github.com/Nihal2999/oms-backend

> Note: Hosted on Render free tier — first request may take ~50 seconds to wake up.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL 15 |
| Caching | Redis (Upstash) |
| Authentication | JWT (access + refresh tokens) |
| ORM | SQLAlchemy |
| Validation | Pydantic v2 |
| Containerization | Docker + Docker Compose |
| CI/CD | GitLab CI/CD |
| Deployment | Render |
| Linting | Ruff |

---

## 📁 Project Structure

```
oms/
├── app/
│   ├── api/v1/
│   │   ├── orders.py            # Order endpoints
│   │   ├── products.py          # Product endpoints
│   │   └── users.py             # User endpoints
│   ├── core/
│   │   ├── background_tasks.py  # Async background logging
│   │   ├── config.py            # Environment config
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── logger.py            # Logging setup
│   │   ├── redis_cache.py       # Redis caching utility
│   │   └── security.py          # JWT auth + password hashing
│   ├── db/
│   │   └── database.py          # DB engine + session
│   ├── models/
│   │   ├── order_model.py
│   │   ├── product_model.py
│   │   └── user_model.py
│   ├── repository/
│   │   ├── order_repo.py        # DB queries for orders
│   │   ├── product_repo.py      # DB queries for products
│   │   └── user_repo.py         # DB queries for users
│   ├── schemas/
│   │   ├── order_schema.py
│   │   ├── pagination.py        # Generic paginated response
│   │   ├── product_schema.py
│   │   └── user_schema.py
│   ├── services/
│   │   ├── order_service.py     # Order business logic
│   │   ├── product_service.py   # Product business logic
│   │   └── user_service.py      # User business logic
│   └── main.py
├── tests/
│   └── test_app.py
├── .env.local                   # Local dev environment variables
├── .env.docker                  # Docker environment variables
├── .gitlab-ci.yml               # GitLab CI/CD pipeline
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🏗️ Architecture

```
Request → Router → Service → Repository → PostgreSQL
                ↕                ↕
           Background         Redis Cache
             Tasks            (Products)
```

Clean layered architecture:
- **Router** — HTTP handling, request/response validation
- **Service** — business logic, orchestration
- **Repository** — database queries only
- **Models** — SQLAlchemy ORM models
- **Schemas** — Pydantic request/response schemas

---

## 📋 API Endpoints

### Users
| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/v1/users/register` | Public | Register new user |
| POST | `/api/v1/users/login` | Public | Login, returns JWT tokens |
| POST | `/api/v1/users/refresh` | Public | Refresh access token |
| POST | `/api/v1/users/logout` | Auth | Logout, invalidates refresh token |
| GET | `/api/v1/users/` | Admin | Get all users (paginated) |
| GET | `/api/v1/users/me` | Auth | Get current user |
| GET | `/api/v1/users/{user_id}` | Auth | Get user by ID |
| PUT | `/api/v1/users/{user_id}` | Auth | Update user |
| PUT | `/api/v1/users/{user_id}/role` | Admin | Toggle user role (user ↔ admin) |
| DELETE | `/api/v1/users/{user_id}` | Admin | Delete user |

### Products
| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/v1/products/` | Admin | Create product |
| GET | `/api/v1/products/` | Public | Get all products (paginated + search) |
| GET | `/api/v1/products/{product_id}` | Public | Get product by ID |
| PUT | `/api/v1/products/{product_id}` | Admin | Update product |
| DELETE | `/api/v1/products/{product_id}` | Admin | Soft delete product |
| PUT | `/api/v1/products/{product_id}/restore` | Admin | Restore deleted product |

### Orders
| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/v1/orders/` | Auth | Create order |
| GET | `/api/v1/orders/` | Admin | Get all orders (paginated) |
| GET | `/api/v1/orders/me` | Auth | Get my orders (paginated) |
| PUT | `/api/v1/orders/{order_id}` | Admin | Update order status |
| PUT | `/api/v1/orders/{order_id}/cancel` | Auth | Cancel order |

---

## ✨ Key Features

### 🔐 Authentication & Authorization
- JWT access tokens (60 min expiry) + refresh tokens (7 days)
- Refresh token stored in DB — logout invalidates it server-side immediately
- Role-based access control (admin / user)
- Password hashing with bcrypt

### 📄 Pagination
All list endpoints support pagination:
```
GET /api/v1/products/?page=1&limit=10&search=laptop
GET /api/v1/orders/?page=1&limit=10
GET /api/v1/users/?page=1&limit=10
```

Response format:
```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "limit": 10,
  "total_pages": 10
}
```

### ⚡ Redis Caching
Product endpoints cached in Redis (Upstash):
- `GET /products/` — cached per page/limit/search combination
- `GET /products/{id}` — cached per product ID
- Cache auto-invalidated on create/update/delete/restore
- TTL: 5 minutes
- Graceful fallback to DB if Redis is unavailable

### 🗂️ Soft Delete
Products support soft delete — deleted products are hidden from all listings but recoverable by admin via the restore endpoint.

### 🔄 Background Tasks
Non-blocking post-request logging using FastAPI BackgroundTasks:
- User registration events
- Order creation events
- Order status update events

### 🗃️ Database Indexing
Indexed columns for optimized query performance:
- `users.email` — fast login lookups
- `products.name` — search queries
- `products.is_deleted` — filtered on every product query
- `orders.user_id` — get my orders
- `orders.product_id` — order-product joins
- `orders.status` — status filtering

---

## 🔄 GitLab CI/CD Pipeline

```
Push to main / Merge Request
         ↓
    ┌────────┐
    │  lint  │  Ruff linting (MR + main)
    └────────┘
         ↓
    ┌────────┐
    │  test  │  pytest (main only)
    └────────┘
         ↓
    ┌────────┐
    │ build  │  Docker build + push to GitLab Container Registry (main only)
    └────────┘
```

**Stages:**
- **lint** — Ruff code linting on merge requests and main branches
- **test** — Run pytest test suite on main
- **build** — Build Docker image and push to GitLab Container Registry

---

## 🚀 Running Locally

### Prerequisites
- Docker Desktop
- Python 3.11+

### 1. Clone the repository
```bash
git clone https://gitlab.com/your-username/oms.git
cd oms
```

### 2. Set up environment
Create `.env.local`:
```env
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/oms
ALLOWED_ORIGINS=*
REDIS_URL=redis://localhost:6379
```

### 3. Start the database and Redis
```bash
docker compose up db redis -d
```

### 4. Install dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Run the server
```bash
uvicorn app.main:app --reload --port 8000
```

API available at: http://localhost:8000/api

---

## 🐳 Running with Docker

```bash
# Full stack (db + backend + redis)
docker compose up --build

# DB and Redis only (for local dev)
docker compose up db redis -d
```

---

## 🌍 Environment Variables

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | JWT signing secret | `supersecretkey` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | `60` |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://user:pass@host:5432/db` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `*` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |

---

## 🧪 Testing

```bash
pytest tests/ python -m pytest -v
```

---

## 📦 Deployment

**Platform:** Render

**Services:**
- Backend — Render Web Service (Docker)
- Database — Render PostgreSQL
- Cache — Upstash Redis (free tier)

**Deploy flow:**
```
git push origin main
        ↓
GitLab CI/CD (lint → test → build → push to registry)
        ↓
Render auto-deploys on push to main
```

---

## 📊 Database Schema

```
users
├── id (PK)
├── name
├── email (unique, indexed)
├── hashed_password
├── role (admin/user)
└── refresh_token

products
├── id (PK)
├── name (indexed)
├── description
├── price
├── stock
└── is_deleted (indexed)

orders
├── id (PK)
├── user_id (FK → users, indexed)
├── product_id (FK → products, indexed)
├── quantity
└── status (pending/shipped/delivered/cancelled, indexed)
```