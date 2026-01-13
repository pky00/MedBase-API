# MedBase-API Makefile
# Run `make help` to see available commands

.PHONY: help install run run-prod db-up db-down docker-build docker-up docker-down docker-logs docker-clean migrate migrate-create format test

# Default target
help:
	@echo "MedBase-API - Available Commands"
	@echo ""
	@echo "Local Development:"
	@echo "  make install        - Install dependencies (conda)"
	@echo "  make run            - Run API locally (uses local .env)"
	@echo "  make run-prod       - Run API locally connected to production DB"
	@echo "  make format         - Format code with Black"
	@echo "  make test           - Run pytest tests"
	@echo "  make db-up          - Start local PostgreSQL container only"
	@echo "  make db-down        - Stop local PostgreSQL container"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-up      - Start all services (API + PostgreSQL)"
	@echo "  make docker-down    - Stop all services"
	@echo "  make docker-logs    - View container logs"
	@echo "  make docker-clean   - Remove all containers, images, and volumes"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create new migration (usage: make migrate-create msg='migration name')"

# ==================== Local Development ====================

# Install dependencies using conda
install:
	conda env create -f environment.yaml || conda env update -f environment.yaml

# Run API locally (uses .env file, auto-starts db if not running)
run:
	@docker-compose ps db | grep -q "running" || (echo "Starting database..." && docker-compose up -d db && echo "Waiting for database to be ready..." && sleep 3)
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Format code with Black
format:
	black app/ tests/

# Run tests (outputs to tests/test_results.log)
test:
	pytest -v --tb=short 2>&1 | tee tests/test_results.log
	@echo ""
	@echo "Test results saved to: tests/test_results.log"

# Run API locally connected to production database
# Requires PROD_DATABASE_URL in .env.prod or as environment variable
run-prod:
	@if [ -f .env.prod ]; then \
		export $$(cat .env.prod | xargs) && uvicorn app.main:app --host localhost --port 8000; \
	else \
		echo "Error: .env.prod file not found. Create it with PROD_DATABASE_URL."; \
		exit 1; \
	fi

# Start only the PostgreSQL container for local development
db-up:
	docker-compose up -d db
	@echo "PostgreSQL is running on localhost:5432"
	@echo "Connection: postgresql+asyncpg://postgres:postgres@localhost:5432/medbase_clinic"

# Stop the PostgreSQL container
db-down:
	docker-compose stop db

# ==================== Docker ====================

# Build Docker image
docker-build:
	docker-compose build

# Start all services
docker-up:
	docker-compose up -d
	@echo ""
	@echo "Services started!"
	@echo "  API:      http://localhost:8000"
	@echo "  Docs:     http://localhost:8000/docs"
	@echo "  Database: localhost:5432"

# Stop all services
docker-down:
	docker-compose down

# View logs
docker-logs:
	docker-compose logs -f

# Clean up everything (containers, images, volumes)
docker-clean:
	docker-compose down -v --rmi all --remove-orphans
	@echo "Cleaned up all containers, images, and volumes"

# ==================== Database Migrations ====================

# Run migrations
migrate:
	alembic upgrade head

# Create a new migration
# Usage: make migrate-create msg="add users table"
migrate-create:
	@if [ -z "$(msg)" ]; then \
		echo "Error: Please provide a migration message"; \
		echo "Usage: make migrate-create msg='your migration message'"; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(msg)"

