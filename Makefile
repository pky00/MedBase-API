.PHONY: help build up down logs shell test migrate migrate-create db-reset clean

# Default target
help:
	@echo "MedBase API - Available commands:"
	@echo ""
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - View logs"
	@echo "  make shell          - Open shell in API container"
	@echo "  make test           - Run tests"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create new migration (MSG=message)"
	@echo "  make db-reset       - Reset database (drop all and migrate)"
	@echo "  make seed           - Seed initial admin user"
	@echo "  make clean          - Remove containers and volumes"
	@echo ""

# Build Docker images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d

# Start services with logs
up-logs:
	docker-compose up

# Stop services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f api

# Open shell in API container
shell:
	docker-compose exec api conda run -n medbase bash

# Run tests
test:
	docker-compose exec -e PYTHONUNBUFFERED=1 api conda run --no-capture-output -n medbase pytest -v -s

# Run a single test and keep data in DB for inspection
# Usage: make test-one TEST=tests/endpoint/test_users.py::TestCreateUser::test_create_user_success
test-one:
	docker-compose exec -e PYTHONUNBUFFERED=1 -e KEEP_DB=1 api conda run --no-capture-output -n medbase pytest -v -s $(TEST)

# Run tests with coverage
test-cov:
	docker-compose exec -e PYTHONUNBUFFERED=1 api conda run --no-capture-output -n medbase pytest -v -s --cov=app --cov-report=html

# Run database migrations
migrate:
	docker-compose exec api conda run -n medbase alembic upgrade head

# Create new migration
migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG is required. Usage: make migrate-create MSG=\"your message\""; \
		exit 1; \
	fi
	docker-compose exec api conda run -n medbase alembic revision --autogenerate -m "$(MSG)"

# Downgrade one migration
migrate-down:
	docker-compose exec api conda run -n medbase alembic downgrade -1

# Reset database
db-reset:
	docker-compose exec api conda run -n medbase alembic downgrade base
	docker-compose exec api conda run -n medbase alembic upgrade head

# Seed initial admin user
seed:
	docker-compose exec api conda run -n medbase python scripts/seed.py

# Remove containers and volumes
clean:
	docker-compose down -v --remove-orphans

# Local development without Docker
dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run linting
lint:
	docker-compose exec api conda run -n medbase ruff check .

# Format code
format:
	docker-compose exec api conda run -n medbase ruff format .
