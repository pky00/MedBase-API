# MedBase-API

A FastAPI backend for a free clinic management system.

## Features

- Patient management
- Doctor management  
- Appointments scheduling
- Prescriptions (medicine & medical devices)
- Inventory management (medicines, medical devices, equipment)
- Donation tracking
- Document management (including external lab results)

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Auth**: JWT (python-jose)
- **Validation**: Pydantic v2

## Quick Start

### Using Make Commands

Run `make help` to see all available commands:

```bash
make help
```

### Option A: Docker (Recommended)

```bash
# Start everything (API + PostgreSQL)
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down

# Clean up everything (containers, images, volumes)
make docker-clean
```

### Option B: Local Development

```bash
# 1. Install dependencies (conda)
make install
conda activate medbase-api

# 2. Set up environment variables
cp env.example .env

# 3. Start PostgreSQL container
make db-up

# 4. Run migrations
make migrate

# 5. Start the API
make run
```

## Default Admin User

After running migrations, a default admin user is created:

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin` |
| Email | `admin@medbase.local` |

**⚠️ Change the password immediately in production!**

### Connect to Production Database

```bash
# 1. Create production env file
cp env.prod.example .env.prod
# Edit .env.prod with your production DATABASE_URL

# 2. Run locally against production DB
make run-prod
```

## Make Commands Reference

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies (conda) |
| `make run` | Run API locally (uses `.env`) |
| `make run-prod` | Run API with production DB (uses `.env.prod`) |
| `make db-up` | Start local PostgreSQL container |
| `make db-down` | Stop local PostgreSQL container |
| `make docker-build` | Build Docker image |
| `make docker-up` | Start all services (API + DB) |
| `make docker-down` | Stop all services |
| `make docker-logs` | View container logs |
| `make docker-clean` | Remove all containers, images, volumes |
| `make migrate` | Run database migrations |
| `make migrate-create msg="..."` | Create new migration |

## API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login and get JWT token

### Users
- `POST /api/v1/users/` - Create new user (requires auth)
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update current user profile
- `POST /api/v1/users/me/change-password` - Change password
- `GET /api/v1/users/` - List all users
- `GET /api/v1/users/{id}` - Get user by ID
- `PATCH /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

## Project Structure

```
MedBase-API/
├── app/
│   ├── main.py           # FastAPI application
│   ├── config.py         # Settings/configuration
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── routers/          # API routes (controllers)
│   ├── services/         # Business logic & DB operations
│   └── utils/            # Database, auth, security
├── alembic/              # Database migrations
├── sql scripts/          # Raw SQL scripts
├── Makefile              # Development commands
├── Dockerfile            # Docker image
├── docker-compose.yml    # Docker services
├── requirements.txt      # Pip dependencies (Docker)
├── environment.yaml      # Conda environment (local)
├── env.example           # Local env template
└── env.prod.example      # Production env template
```

## Environment Files

| File | Purpose |
|------|---------|
| `.env` | Local development settings |
| `.env.prod` | Production database connection |
| `env.example` | Template for `.env` |
| `env.prod.example` | Template for `.env.prod` |

## License

Private - All rights reserved
