.PHONY: help up down restart logs ps build \
        test test-backend test-frontend \
        lint lint-backend lint-frontend \
        format format-backend format-frontend \
        migrate migration shell-api shell-db

help:
	@echo "FleetOps — Make targets"
	@echo "  up                Bring up all services (postgres, redis, api, frontend)"
	@echo "  down              Stop and remove all containers"
	@echo "  restart           Restart all services"
	@echo "  logs              Tail logs from all services"
	@echo "  ps                List service status"
	@echo "  build             Rebuild all images"
	@echo ""
	@echo "  test              Run backend + frontend tests"
	@echo "  test-backend      Run backend tests only"
	@echo "  test-frontend     Run frontend tests only"
	@echo ""
	@echo "  lint              Run lint on backend + frontend"
	@echo "  format            Auto-format backend + frontend"
	@echo ""
	@echo "  migrate           Apply alembic migrations to head"
	@echo "  migration name=X  Create new alembic migration"
	@echo ""
	@echo "  shell-api         Shell into the api container"
	@echo "  shell-db          psql into the postgres container"

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

build:
	docker compose build

test: test-backend test-frontend

test-backend:
	cd backend && uv run pytest -v

test-frontend:
	cd frontend && npm test

lint: lint-backend lint-frontend

lint-backend:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app

lint-frontend:
	cd frontend && npm run lint

format: format-backend format-frontend

format-backend:
	cd backend && uv run ruff format . && uv run ruff check --fix .

format-frontend:
	cd frontend && npm run format

migrate:
	docker compose exec api alembic upgrade head

migration:
	@if [ -z "$(name)" ]; then echo "Usage: make migration name=<description>"; exit 1; fi
	docker compose exec api alembic revision --autogenerate -m "$(name)"

shell-api:
	docker compose exec api /bin/bash

shell-db:
	docker compose exec postgres psql -U fleetops -d fleetops
