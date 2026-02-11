# MedBase API

Backend API for **MedBase** — a clinic management system designed for small medical clinics. Built with FastAPI, SQLAlchemy (async), and PostgreSQL.

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| FastAPI | Web framework |
| SQLAlchemy 2.0 (async) | ORM |
| PostgreSQL (Amazon RDS) | Database |
| Alembic | Database migrations |
| Pydantic | Request/response validation |
| JWT (python-jose) | Authentication |
| Docker + Conda | Containerization & environment |
| pytest + httpx | Testing |

---

## Project Structure

```
MedBase-API/
├── app/
│   ├── model/          # SQLAlchemy ORM models
│   ├── router/         # FastAPI route handlers
│   ├── schema/         # Pydantic schemas
│   ├── service/        # Business logic layer
│   └── utility/        # Config, database, auth, security, logging
├── alembic/            # Database migrations
├── docs/               # Documentation (synced from MedBase-Planner)
├── postman/            # Postman collection
├── scripts/            # Utility scripts (seed, etc.)
├── tests/              # Test suite
├── main.py             # Application entry point
├── docker-compose.yml  # Docker services
├── Dockerfile          # Container image
├── Makefile            # Common commands
├── environment.yml     # Conda environment
└── requirements.txt    # Python dependencies
```

---

## Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose
- A PostgreSQL database (Amazon RDS or any PostgreSQL instance)

---

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd MedBase-API
```

### 2. Create the `.env` file

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@your-rds-host:5432/medbase
TEST_DATABASE_URL=postgresql+asyncpg://user:password@your-rds-host:5432/medbase_test

# JWT Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Application
DEBUG=false
```

### 3. Build the Docker image

```bash
make build
```

### 4. Start the API

```bash
make up
```

The API will be available at **http://localhost:8000**.

### 5. Run database migrations

```bash
make migrate
```

### 6. Seed the admin user

```bash
make seed
```

This creates a default admin account:
- **Username**: `admin`
- **Password**: `admin123`

> Change the default password after first login.

---

## Usage

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Make Commands

| Command | Description |
|---------|-------------|
| `make build` | Build Docker image |
| `make up` | Start the API (detached) |
| `make up-logs` | Start the API (with logs) |
| `make down` | Stop the API |
| `make logs` | View API logs |
| `make shell` | Open a shell in the container |
| `make test` | Run tests |
| `make test-cov` | Run tests with coverage |
| `make migrate` | Run database migrations |
| `make migrate-create MSG="message"` | Create a new migration |
| `make migrate-down` | Downgrade one migration |
| `make db-reset` | Reset database (downgrade + upgrade) |
| `make seed` | Seed initial admin user |
| `make clean` | Remove containers and volumes |
| `make dev` | Run locally without Docker |
| `make lint` | Run linter |
| `make format` | Format code |

---

## Running Tests

Tests use a separate database (`TEST_DATABASE_URL`). Make sure the test database exists on your PostgreSQL server, then run:

```bash
make test
```

---

## Architecture

The project follows a **4-layer pattern**:

1. **Router** (`app/router/`) — HTTP endpoints, auth guards, validation
2. **Service** (`app/service/`) — Business logic
3. **Model** (`app/model/`) — SQLAlchemy ORM models
4. **Schema** (`app/schema/`) — Pydantic request/response schemas

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login and get JWT token |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/auth/me` | Get current user info |

### Users (Admin only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users` | List users (paginated, filterable) |
| GET | `/api/v1/users/{id}` | Get user by ID |
| POST | `/api/v1/users` | Create user |
| PUT | `/api/v1/users/{id}` | Update user |
| DELETE | `/api/v1/users/{id}` | Soft delete user |
