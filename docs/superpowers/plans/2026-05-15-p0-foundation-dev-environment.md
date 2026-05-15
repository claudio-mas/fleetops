# P0 — Foundation & Dev Environment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Estabelecer o repositório monorepo com backend FastAPI + frontend React rodando juntos via Docker Compose, com banco Postgres/Redis, Alembic, suite de testes funcional (pytest + vitest), lint configurado, CI no GitHub Actions e documentação de setup — pronto para que P1 (Auth & Multi-tenant) comece imediatamente.

**Architecture:** Monorepo com pastas `backend/` (FastAPI + uv) e `frontend/` (React + Vite + TS). Desenvolvimento local 100% via `docker-compose up`. Postgres 16 e Redis 7 em containers. Alembic configurado para migrations async. Frontend faz proxy reverso para `/api` durante dev. Caddy adicionado em fase futura (P11).

**Tech Stack:**
- **Backend**: Python 3.12, FastAPI ≥0.115, SQLAlchemy 2.0 async, asyncpg, Alembic, Pydantic v2, uv (package manager), pytest + pytest-asyncio
- **Frontend**: React 18, Vite 6, TypeScript 5.7, TanStack Query 5, axios, Vitest, React Testing Library, TailwindCSS 3, shadcn/ui (init only)
- **Infra dev**: Docker + Docker Compose, Postgres 16, Redis 7
- **Quality**: ruff + mypy (Python), ESLint + Prettier (TS)
- **CI**: GitHub Actions

---

## File Structure Inventory

```
c:\Projeto\Access\
├── .github/workflows/
│   └── ci.yml                          # CI: lint + test backend & frontend
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI() instance, includes routers
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Settings via pydantic-settings
│   │   │   └── database.py             # AsyncEngine + sessionmaker + dep
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── deps.py                 # Reusable FastAPI dependencies
│   │       └── health.py               # GET /health, GET /ready
│   ├── alembic/
│   │   ├── env.py                      # Alembic env (async)
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial.py         # Initial empty migration (workflow check)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Shared fixtures (async client, db)
│   │   ├── test_health.py
│   │   └── test_database.py
│   ├── alembic.ini
│   ├── pyproject.toml                  # Deps + ruff + mypy + pytest config
│   ├── Dockerfile                      # Multi-stage build with uv
│   └── .python-version                 # "3.12"
├── frontend/
│   ├── src/
│   │   ├── main.tsx                    # ReactDOM root + providers
│   │   ├── App.tsx                     # Layout shell + routes
│   │   ├── index.css                   # Tailwind directives
│   │   ├── lib/
│   │   │   ├── api.ts                  # axios instance + interceptor stubs
│   │   │   └── queryClient.ts          # TanStack Query client config
│   │   ├── components/
│   │   │   └── ui/                     # shadcn/ui components (added by CLI)
│   │   └── pages/
│   │       └── HealthCheck.tsx         # Demo page calling /api/health
│   ├── tests/
│   │   ├── setup.ts                    # Vitest setup (jest-dom)
│   │   ├── App.test.tsx
│   │   └── HealthCheck.test.tsx
│   ├── public/
│   │   └── favicon.svg
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts                  # + dev proxy /api → backend
│   ├── vitest.config.ts                # + jsdom env
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── components.json                 # shadcn/ui config
│   ├── .eslintrc.cjs
│   ├── .prettierrc.json
│   ├── .prettierignore
│   └── Dockerfile                      # Multi-stage: build + nginx serve
├── docker-compose.yml                  # postgres + redis + api + frontend
├── docker-compose.override.yml.example # Dev overrides template
├── .env.example                        # All required env vars documented
├── .gitignore
├── .editorconfig
├── Makefile                            # dev/test/lint/migrate shortcuts
└── README.md                           # Setup & daily workflow
```

**Boundary discipline**: Tudo de backend isolado em `backend/`, tudo de frontend em `frontend/`. Configs de infra/dev na raiz. Dependência cruzada apenas via HTTP (proxy `/api`).

---

## Task 1: Repository structure, .gitignore and .editorconfig

**Files:**
- Create: `.gitignore`
- Create: `.editorconfig`
- Modify: `README.md` (overwrite minimal placeholder if exists)

- [ ] **Step 1: Create .gitignore at repo root**

Create `c:\Projeto\Access\.gitignore`:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
env/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
coverage.xml
htmlcov/

# Node
node_modules/
dist/
.vite/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.idea/
.vscode/
!.vscode/settings.json.example
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Env
.env
.env.local
.env.*.local
!.env.example

# Docker
docker-compose.override.yml

# Build outputs
backend/build/
frontend/build/
frontend/dist/

# Legacy artifacts (Access source materials, kept out of git for now)
ERD.accdb
levantamento_access.py
levantamento_access_*.xlsx
vba_*/
.qodo/
```

- [ ] **Step 2: Create .editorconfig**

Create `c:\Projeto\Access\.editorconfig`:

```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.py]
indent_size = 4

[Makefile]
indent_style = tab

[*.md]
trim_trailing_whitespace = false
```

- [ ] **Step 3: Verify git status shows untracked files**

Run: `git -C c:/Projeto/Access status --short`
Expected: lines starting with `??` for `.gitignore`, `.editorconfig`, plus the legacy files appear untracked but will not be staged.

- [ ] **Step 4: Commit**

```bash
git -C c:/Projeto/Access add .gitignore .editorconfig
git -C c:/Projeto/Access commit -m "chore: add .gitignore and .editorconfig"
```

---

## Task 2: Backend pyproject.toml and dependency install

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.python-version`
- Create: `backend/app/__init__.py`

- [ ] **Step 1: Verify uv is installed**

Run: `uv --version`
Expected: prints `uv 0.5.x` or newer. If absent, install with `irm https://astral.sh/uv/install.ps1 | iex` (PowerShell) and re-run.

- [ ] **Step 2: Create backend/.python-version**

Create `c:\Projeto\Access\backend\.python-version`:

```
3.12
```

- [ ] **Step 3: Create backend/pyproject.toml**

Create `c:\Projeto\Access\backend\pyproject.toml`:

```toml
[project]
name = "fleetops-backend"
version = "0.1.0"
description = "FleetOps SaaS backend (FastAPI + PostgreSQL multi-tenant)"
requires-python = ">=3.12,<3.13"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "python-multipart>=0.0.20",
]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.28.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
    "types-python-dateutil",
]

[tool.uv]
package = false

[tool.ruff]
line-length = 100
target-version = "py312"
extend-exclude = ["alembic/versions"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM", "TID"]
ignore = ["E501"]  # line length handled by formatter

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
exclude = ["alembic/versions/"]

[[tool.mypy.overrides]]
module = ["alembic.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-ra --strict-markers --cov=app --cov-report=term-missing"
```

- [ ] **Step 4: Create backend/app/__init__.py (empty)**

Create `c:\Projeto\Access\backend\app\__init__.py` with no content (empty file).

- [ ] **Step 5: Run uv sync to install deps**

Run from `c:\Projeto\Access\backend`: `uv sync`
Expected: creates `.venv/`, installs all deps including dev group, prints `Resolved N packages` and `Installed N packages`.

- [ ] **Step 6: Verify backend can be imported**

Run from `c:\Projeto\Access\backend`: `uv run python -c "import app; print('OK')"`
Expected: prints `OK`.

- [ ] **Step 7: Commit**

```bash
git -C c:/Projeto/Access add backend/pyproject.toml backend/.python-version backend/app/__init__.py backend/uv.lock
git -C c:/Projeto/Access commit -m "feat(backend): bootstrap FastAPI project with uv + pyproject.toml"
```

---

## Task 3: Backend config + Settings

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test for Settings**

Create `c:\Projeto\Access\backend\tests\__init__.py` (empty file).

Create `c:\Projeto\Access\backend\tests\conftest.py`:

```python
import os

# Ensure tests run with predictable env
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ENVIRONMENT", "test")
```

Create `c:\Projeto\Access\backend\tests\test_config.py`:

```python
from app.core.config import Settings


def test_settings_loads_from_env() -> None:
    s = Settings()
    assert s.environment == "test"
    assert s.database_url.startswith("postgresql+asyncpg://")
    assert s.redis_url.startswith("redis://")
    assert len(s.secret_key) >= 16


def test_settings_defaults_log_level_to_info() -> None:
    s = Settings()
    assert s.log_level == "INFO"
```

- [ ] **Step 2: Run test to verify it fails**

Run from `c:\Projeto\Access\backend`: `uv run pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core'`.

- [ ] **Step 3: Implement core/config.py**

Create `c:\Projeto\Access\backend\app\core\__init__.py` (empty file).

Create `c:\Projeto\Access\backend\app\core\config.py`:

```python
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["dev", "test", "staging", "production"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: str = Field(..., min_length=1)
    redis_url: str = Field(..., min_length=1)
    secret_key: str = Field(..., min_length=16)


settings = Settings()  # type: ignore[call-arg]
```

- [ ] **Step 4: Run test to verify it passes**

Run from `c:\Projeto\Access\backend`: `uv run pytest tests/test_config.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git -C c:/Projeto/Access add backend/app/core backend/tests
git -C c:/Projeto/Access commit -m "feat(backend): add Settings via pydantic-settings + tests"
```

---

## Task 4: FastAPI app skeleton with /health endpoint (TDD)

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/health.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Write the failing test**

Create `c:\Projeto\Access\backend\app\api\__init__.py` (empty file).

Create `c:\Projeto\Access\backend\tests\test_health.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_returns_ok() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_root_returns_redirect_to_docs() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"
```

- [ ] **Step 2: Run test to verify it fails**

Run from `c:\Projeto\Access\backend`: `uv run pytest tests/test_health.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.main'`.

- [ ] **Step 3: Implement health router**

Create `c:\Projeto\Access\backend\app\api\health.py`:

```python
from fastapi import APIRouter

router = APIRouter(tags=["meta"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Implement main.py with router included**

Create `c:\Projeto\Access\backend\app\main.py`:

```python
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.health import router as health_router
from app.core.config import settings

app = FastAPI(
    title="FleetOps API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health_router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs", status_code=307)


@app.on_event("startup")
async def on_startup() -> None:
    print(f"FleetOps API starting in environment={settings.environment}")
```

- [ ] **Step 5: Run tests to verify they pass**

Run from `c:\Projeto\Access\backend`: `uv run pytest tests/test_health.py -v`
Expected: 2 passed.

- [ ] **Step 6: Smoke-test the API manually**

Run from `c:\Projeto\Access\backend`: `uv run fastapi dev app/main.py --port 8000`
In another terminal: `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`

Stop the server (Ctrl+C).

- [ ] **Step 7: Commit**

```bash
git -C c:/Projeto/Access add backend/app/main.py backend/app/api backend/tests/test_health.py
git -C c:/Projeto/Access commit -m "feat(backend): add /health endpoint with TDD"
```

---

## Task 5: PostgreSQL + Redis docker-compose

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `docker-compose.override.yml.example`

- [ ] **Step 1: Create .env.example**

Create `c:\Projeto\Access\.env.example`:

```dotenv
# ─── App ──────────────────────────────────────────
ENVIRONMENT=dev
LOG_LEVEL=INFO
SECRET_KEY=change-me-to-a-random-32+-char-string

# ─── PostgreSQL ───────────────────────────────────
POSTGRES_USER=fleetops
POSTGRES_PASSWORD=fleetops_dev_password
POSTGRES_DB=fleetops
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://fleetops:fleetops_dev_password@postgres:5432/fleetops

# ─── Redis ────────────────────────────────────────
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# ─── Frontend (Vite) ──────────────────────────────
VITE_API_BASE_URL=/api
```

- [ ] **Step 2: Create docker-compose.yml**

Create `c:\Projeto\Access\docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: fleetops-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: fleetops-redis
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  postgres_data:
  redis_data:
```

- [ ] **Step 3: Create override template**

Create `c:\Projeto\Access\docker-compose.override.yml.example`:

```yaml
# Copy to docker-compose.override.yml for personal local overrides.
# This file is gitignored.
services:
  postgres:
    ports:
      - "5433:5432"  # Use 5433 if 5432 is in use locally
```

- [ ] **Step 4: Copy .env.example to .env**

Run: `Copy-Item c:\Projeto\Access\.env.example c:\Projeto\Access\.env`

(`.env` is gitignored — must exist locally for compose to read.)

- [ ] **Step 5: Bring up postgres + redis**

Run from `c:\Projeto\Access`: `docker compose up -d postgres redis`
Expected: both containers report `Started`.

- [ ] **Step 6: Verify health of both**

Run: `docker compose ps`
Expected: both services show `(healthy)` in the STATUS column. Wait up to 30s if needed.

Run: `docker compose exec postgres psql -U fleetops -d fleetops -c "SELECT 1;"`
Expected: returns `1` row with value 1.

Run: `docker compose exec redis redis-cli ping`
Expected: prints `PONG`.

- [ ] **Step 7: Commit**

```bash
git -C c:/Projeto/Access add docker-compose.yml docker-compose.override.yml.example .env.example
git -C c:/Projeto/Access commit -m "feat(infra): docker-compose with postgres + redis for dev"
```

---

## Task 6: Async database connection module + integration test

**Files:**
- Create: `backend/app/core/database.py`
- Create: `backend/tests/test_database.py`

- [ ] **Step 1: Write the failing integration test**

Create `c:\Projeto\Access\backend\tests\test_database.py`:

```python
import os

import pytest
from sqlalchemy import text

# Switch to local-host URL since tests run on host, not in container
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://fleetops:fleetops_dev_password@localhost:5432/fleetops"
)

from app.core.database import engine, get_session  # noqa: E402


@pytest.mark.asyncio
async def test_engine_can_execute_select_one() -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1 AS value"))
        row = result.one()
        assert row.value == 1


@pytest.mark.asyncio
async def test_get_session_yields_async_session() -> None:
    gen = get_session()
    session = await gen.__anext__()
    try:
        result = await session.execute(text("SELECT 'hello' AS greeting"))
        assert result.scalar_one() == "hello"
    finally:
        await gen.aclose()
```

- [ ] **Step 2: Run the test to verify it fails**

Run from `c:\Projeto\Access\backend`: `uv run pytest tests/test_database.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.database'`.

- [ ] **Step 3: Implement database.py**

Create `c:\Projeto\Access\backend\app\core\database.py`:

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=10,
)

SessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionFactory() as session:
        yield session
```

- [ ] **Step 4: Ensure postgres is up**

Run from `c:\Projeto\Access`: `docker compose ps postgres`
Expected: postgres shows `(healthy)`. If not, run `docker compose up -d postgres` and wait.

- [ ] **Step 5: Run the test to verify it passes**

Run from `c:\Projeto\Access\backend`: `uv run pytest tests/test_database.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git -C c:/Projeto/Access add backend/app/core/database.py backend/tests/test_database.py
git -C c:/Projeto/Access commit -m "feat(backend): async SQLAlchemy engine + session dependency"
```

---

## Task 7: Alembic configured for async + first empty migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/0001_initial.py`

- [ ] **Step 1: Initialize Alembic**

Run from `c:\Projeto\Access\backend`: `uv run alembic init -t async alembic`
Expected: creates `alembic/`, `alembic.ini`. Confirms async template.

- [ ] **Step 2: Replace alembic.ini with project-specific config**

Overwrite `c:\Projeto\Access\backend\alembic.ini` (keep file but replace contents):

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARNING
handlers = console
qualname =

[logger_sqlalchemy]
level = WARNING
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 3: Replace alembic/env.py to read URL from Settings**

Overwrite `c:\Projeto\Access\backend\alembic\env.py`:

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None  # No models yet — set in P1


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Create first empty migration manually**

Create `c:\Projeto\Access\backend\alembic\versions\0001_initial.py`:

```python
"""initial empty migration (verifies workflow)

Revision ID: 0001
Revises:
Create Date: 2026-05-15

"""
from collections.abc import Sequence

from alembic import op  # noqa: F401

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
```

- [ ] **Step 5: Set DATABASE_URL for local execution**

Before running alembic, set the env var pointing to localhost (alembic runs on host, not container):

PowerShell: `$env:DATABASE_URL="postgresql+asyncpg://fleetops:fleetops_dev_password@localhost:5432/fleetops"`

- [ ] **Step 6: Run migration to verify workflow works**

Run from `c:\Projeto\Access\backend`: `uv run alembic upgrade head`
Expected: prints `Running upgrade  -> 0001, initial empty migration` and exits 0.

- [ ] **Step 7: Verify alembic_version table exists**

Run from `c:\Projeto\Access`: `docker compose exec postgres psql -U fleetops -d fleetops -c "SELECT version_num FROM alembic_version;"`
Expected: returns `0001`.

- [ ] **Step 8: Commit**

```bash
git -C c:/Projeto/Access add backend/alembic.ini backend/alembic
git -C c:/Projeto/Access commit -m "feat(backend): alembic configured for async + first migration"
```

---

## Task 8: Backend Dockerfile + integrate to docker-compose

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`
- Modify: `docker-compose.yml` (add `api` service)

- [ ] **Step 1: Create backend/.dockerignore**

Create `c:\Projeto\Access\backend\.dockerignore`:

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/
tests/
.env
.env.*
Dockerfile
.dockerignore
```

- [ ] **Step 2: Create backend/Dockerfile (multi-stage with uv)**

Create `c:\Projeto\Access\backend\Dockerfile`:

```dockerfile
# ───────────────── Builder ─────────────────
FROM ghcr.io/astral-sh/uv:0.5-python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ───────────────── Runtime ─────────────────
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

RUN groupadd -r app && useradd -r -g app -s /sbin/nologin app

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER app

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Append api service to docker-compose.yml**

Edit `c:\Projeto\Access\docker-compose.yml` — add the `api` service inside `services:` between `redis` and `volumes:`:

```yaml
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: fleetops-api
    environment:
      ENVIRONMENT: ${ENVIRONMENT:-dev}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      SECRET_KEY: ${SECRET_KEY}
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend/app:/app/app:ro
      - ./backend/alembic:/app/alembic:ro
```

- [ ] **Step 4: Build and start api**

Run from `c:\Projeto\Access`: `docker compose up -d --build api`
Expected: build completes, container starts.

- [ ] **Step 5: Verify api is healthy**

Wait 15 seconds, then run: `docker compose ps api`
Expected: STATUS shows `(healthy)`.

Run: `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`

- [ ] **Step 6: Run alembic from inside container to verify**

Run: `docker compose exec api alembic current`
Expected: prints `0001 (head)`.

- [ ] **Step 7: Commit**

```bash
git -C c:/Projeto/Access add backend/Dockerfile backend/.dockerignore docker-compose.yml
git -C c:/Projeto/Access commit -m "feat(infra): backend Dockerfile + api service in compose"
```

---

## Task 9: Frontend skeleton — Vite + React + TypeScript

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/.gitignore` (frontend-specific node_modules guard)

- [ ] **Step 1: Create frontend/package.json**

Create `c:\Projeto\Access\frontend\package.json`:

```json
{
  "name": "fleetops-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview --host",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\""
  },
  "dependencies": {
    "@tanstack/react-query": "^5.59.0",
    "axios": "^1.7.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.0",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@typescript-eslint/eslint-plugin": "^8.15.0",
    "@typescript-eslint/parser": "^8.15.0",
    "@vitejs/plugin-react": "^4.3.0",
    "eslint": "^8.57.0",
    "eslint-plugin-react-hooks": "^5.0.0",
    "eslint-plugin-react-refresh": "^0.4.0",
    "jsdom": "^25.0.0",
    "prettier": "^3.4.0",
    "typescript": "^5.7.0",
    "vite": "^6.0.0",
    "vitest": "^2.1.0"
  }
}
```

- [ ] **Step 2: Create tsconfig files**

Create `c:\Projeto\Access\frontend\tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src", "tests"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

Create `c:\Projeto\Access\frontend\tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "noEmit": true
  },
  "include": ["vite.config.ts", "vitest.config.ts"]
}
```

- [ ] **Step 3: Create vite.config.ts with proxy to backend**

Create `c:\Projeto\Access\frontend\vite.config.ts`:

```typescript
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
```

- [ ] **Step 4: Create index.html and src skeleton**

Create `c:\Projeto\Access\frontend\index.html`:

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>FleetOps</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `c:\Projeto\Access\frontend\src\main.tsx`:

```typescript
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Create `c:\Projeto\Access\frontend\src\App.tsx`:

```typescript
export default function App(): JSX.Element {
  return (
    <div>
      <h1>FleetOps</h1>
      <p>Foundation skeleton ready.</p>
    </div>
  );
}
```

- [ ] **Step 5: Install npm dependencies**

Run from `c:\Projeto\Access\frontend`: `npm install`
Expected: creates `node_modules/`, prints `added N packages`.

- [ ] **Step 6: Verify build works**

Run from `c:\Projeto\Access\frontend`: `npm run build`
Expected: `dist/` is created with built assets, no errors.

- [ ] **Step 7: Verify dev server starts**

Run from `c:\Projeto\Access\frontend`: `npm run dev`
Expected: prints `Local: http://localhost:5173`. Open browser and confirm "FleetOps" headline appears. Stop with Ctrl+C.

- [ ] **Step 8: Commit**

```bash
git -C c:/Projeto/Access add frontend/package.json frontend/tsconfig.json frontend/tsconfig.node.json frontend/vite.config.ts frontend/index.html frontend/src frontend/package-lock.json
git -C c:/Projeto/Access commit -m "feat(frontend): bootstrap Vite + React + TS skeleton"
```

---

## Task 10: Vitest config + first test (TDD)

**Files:**
- Create: `frontend/vitest.config.ts`
- Create: `frontend/tests/setup.ts`
- Create: `frontend/tests/App.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `c:\Projeto\Access\frontend\tests\App.test.tsx`:

```typescript
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "../src/App";

describe("App", () => {
  it("renders the FleetOps headline", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: /FleetOps/i })).toBeInTheDocument();
  });

  it("shows the foundation skeleton message", () => {
    render(<App />);
    expect(screen.getByText(/Foundation skeleton ready/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails (no vitest config yet)**

Run from `c:\Projeto\Access\frontend`: `npm test`
Expected: FAIL with config error or "Cannot find module '@testing-library/jest-dom/matchers'" until setup is added.

- [ ] **Step 3: Create vitest.config.ts**

Create `c:\Projeto\Access\frontend\vitest.config.ts`:

```typescript
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    css: false,
  },
});
```

- [ ] **Step 4: Create tests/setup.ts**

Create `c:\Projeto\Access\frontend\tests\setup.ts`:

```typescript
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});
```

- [ ] **Step 5: Run the test to verify it passes**

Run from `c:\Projeto\Access\frontend`: `npm test`
Expected: 2 tests passed in `tests/App.test.tsx`.

- [ ] **Step 6: Commit**

```bash
git -C c:/Projeto/Access add frontend/vitest.config.ts frontend/tests
git -C c:/Projeto/Access commit -m "feat(frontend): vitest configured + smoke tests for App"
```

---

## Task 11: TailwindCSS + base styling

**Files:**
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/index.css`
- Modify: `frontend/src/main.tsx` (import index.css)
- Modify: `frontend/package.json` (add tailwind deps)

- [ ] **Step 1: Add tailwind deps to package.json**

Edit `c:\Projeto\Access\frontend\package.json` — add to `devDependencies`:

```json
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0"
```

(Insert alphabetically; ensure trailing commas remain valid.)

Run: `npm install` from `c:\Projeto\Access\frontend`.

- [ ] **Step 2: Create tailwind.config.ts**

Create `c:\Projeto\Access\frontend\tailwind.config.ts`:

```typescript
import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
} satisfies Config;
```

- [ ] **Step 3: Create postcss.config.js**

Create `c:\Projeto\Access\frontend\postcss.config.js`:

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 4: Create src/index.css with Tailwind directives**

Create `c:\Projeto\Access\frontend\src\index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html,
body,
#root {
  height: 100%;
}

body {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  margin: 0;
}
```

- [ ] **Step 5: Import index.css in main.tsx**

Edit `c:\Projeto\Access\frontend\src\main.tsx` — replace contents:

```typescript
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 6: Apply Tailwind classes in App.tsx (verify it works)**

Edit `c:\Projeto\Access\frontend\src\App.tsx` — replace contents:

```typescript
export default function App(): JSX.Element {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-slate-900">FleetOps</h1>
        <p className="mt-2 text-slate-600">Foundation skeleton ready.</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 7: Run tests to confirm nothing broke**

Run from `c:\Projeto\Access\frontend`: `npm test`
Expected: 2 tests still pass (Tailwind classes don't change semantic content).

- [ ] **Step 8: Verify in browser**

Run: `npm run dev` and open `http://localhost:5173`.
Expected: centered headline with Tailwind styling (gray background, large bold text).

- [ ] **Step 9: Commit**

```bash
git -C c:/Projeto/Access add frontend/package.json frontend/package-lock.json frontend/tailwind.config.ts frontend/postcss.config.js frontend/src/index.css frontend/src/main.tsx frontend/src/App.tsx
git -C c:/Projeto/Access commit -m "feat(frontend): add TailwindCSS + restyle App"
```

---

## Task 12: TanStack Query + axios client + HealthCheck page (frontend ↔ backend integration)

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/queryClient.ts`
- Create: `frontend/src/pages/HealthCheck.tsx`
- Create: `frontend/tests/HealthCheck.test.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Write the failing test for HealthCheck page**

Create `c:\Projeto\Access\frontend\tests\HealthCheck.test.tsx`:

```typescript
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../src/lib/api";
import HealthCheck from "../src/pages/HealthCheck";

function wrap(children: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("HealthCheck", () => {
  beforeEach(() => {
    vi.spyOn(api, "get").mockResolvedValue({
      data: { status: "ok" },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {} as never,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("displays the backend status when fetch succeeds", async () => {
    render(wrap(<HealthCheck />));
    await waitFor(() => {
      expect(screen.getByText(/backend status: ok/i)).toBeInTheDocument();
    });
  });

  it("calls /health endpoint", async () => {
    render(wrap(<HealthCheck />));
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/health");
    });
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run from `c:\Projeto\Access\frontend`: `npm test -- HealthCheck`
Expected: FAIL with module-not-found errors.

- [ ] **Step 3: Implement src/lib/api.ts**

Create `c:\Projeto\Access\frontend\src\lib\api.ts`:

```typescript
import axios, { type AxiosInstance } from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 10_000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
);
```

- [ ] **Step 4: Implement src/lib/queryClient.ts**

Create `c:\Projeto\Access\frontend\src\lib\queryClient.ts`:

```typescript
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

- [ ] **Step 5: Implement HealthCheck page**

Create `c:\Projeto\Access\frontend\src\pages\HealthCheck.tsx`:

```typescript
import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";

interface HealthResponse {
  status: string;
}

export default function HealthCheck(): JSX.Element {
  const { data, isPending, isError, error } = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await api.get<HealthResponse>("/health");
      return res.data;
    },
  });

  if (isPending) return <p>Checking backend…</p>;
  if (isError) return <p className="text-red-600">Error: {(error as Error).message}</p>;

  return <p>Backend status: {data.status}</p>;
}
```

- [ ] **Step 6: Wire QueryClientProvider in main.tsx**

Replace `c:\Projeto\Access\frontend\src\main.tsx`:

```typescript
import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./index.css";
import { queryClient } from "./lib/queryClient";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
```

- [ ] **Step 7: Mount HealthCheck inside App.tsx**

Replace `c:\Projeto\Access\frontend\src\App.tsx`:

```typescript
import HealthCheck from "./pages/HealthCheck";

export default function App(): JSX.Element {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-slate-900">FleetOps</h1>
        <p className="text-slate-600">Foundation skeleton ready.</p>
        <div className="text-slate-700 text-sm">
          <HealthCheck />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 8: Adjust App.test.tsx because rendering App now requires QueryClient**

Replace `c:\Projeto\Access\frontend\tests\App.test.tsx`:

```typescript
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "../src/App";

function renderApp() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  );
}

describe("App", () => {
  it("renders the FleetOps headline", () => {
    renderApp();
    expect(screen.getByRole("heading", { name: /FleetOps/i })).toBeInTheDocument();
  });

  it("shows the foundation skeleton message", () => {
    renderApp();
    expect(screen.getByText(/Foundation skeleton ready/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 9: Run all frontend tests to verify they pass**

Run from `c:\Projeto\Access\frontend`: `npm test`
Expected: 4 tests passed (2 App + 2 HealthCheck).

- [ ] **Step 10: End-to-end smoke test (frontend ↔ backend)**

Ensure backend container is running: `docker compose up -d api`.
Run from `c:\Projeto\Access\frontend`: `npm run dev`.
Open `http://localhost:5173`.
Expected: page shows "Backend status: ok" (proxied through Vite to backend at `:8000`).

Stop dev server with Ctrl+C.

- [ ] **Step 11: Commit**

```bash
git -C c:/Projeto/Access add frontend/src/lib frontend/src/pages frontend/src/App.tsx frontend/src/main.tsx frontend/tests
git -C c:/Projeto/Access commit -m "feat(frontend): TanStack Query + axios + HealthCheck page integrated with backend"
```

---

## Task 13: Frontend Dockerfile + add to docker-compose

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/.dockerignore`
- Create: `frontend/nginx.conf`
- Modify: `docker-compose.yml` (add `frontend` service)

- [ ] **Step 1: Create .dockerignore**

Create `c:\Projeto\Access\frontend\.dockerignore`:

```
node_modules/
dist/
.vite/
coverage/
.eslintcache
Dockerfile
.dockerignore
```

- [ ] **Step 2: Create nginx.conf for serving the SPA**

Create `c:\Projeto\Access\frontend\nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://api:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

- [ ] **Step 3: Create Dockerfile**

Create `c:\Projeto\Access\frontend\Dockerfile`:

```dockerfile
# ───────────────── Builder ─────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ───────────────── Runtime ─────────────────
FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1
```

- [ ] **Step 4: Append frontend service to docker-compose.yml**

Edit `c:\Projeto\Access\docker-compose.yml` — add inside `services:`, after `api`:

```yaml
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: fleetops-frontend
    ports:
      - "8080:80"
    depends_on:
      api:
        condition: service_healthy
```

- [ ] **Step 5: Build + start frontend**

Run from `c:\Projeto\Access`: `docker compose up -d --build frontend`
Expected: build finishes (may take 1–2 min), container starts.

- [ ] **Step 6: Verify in browser**

Open `http://localhost:8080`.
Expected: same UI as dev mode, "Backend status: ok" appears (nginx proxies `/api/` to backend container).

- [ ] **Step 7: Commit**

```bash
git -C c:/Projeto/Access add frontend/Dockerfile frontend/.dockerignore frontend/nginx.conf docker-compose.yml
git -C c:/Projeto/Access commit -m "feat(infra): frontend Dockerfile + nginx + compose integration"
```

---

## Task 14: ESLint + Prettier for frontend

**Files:**
- Create: `frontend/.eslintrc.cjs`
- Create: `frontend/.eslintignore`
- Create: `frontend/.prettierrc.json`
- Create: `frontend/.prettierignore`

- [ ] **Step 1: Create .prettierrc.json**

Create `c:\Projeto\Access\frontend\.prettierrc.json`:

```json
{
  "semi": true,
  "singleQuote": false,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

- [ ] **Step 2: Create .prettierignore**

Create `c:\Projeto\Access\frontend\.prettierignore`:

```
dist/
node_modules/
coverage/
.vite/
package-lock.json
```

- [ ] **Step 3: Create .eslintrc.cjs**

Create `c:\Projeto\Access\frontend\.eslintrc.cjs`:

```javascript
module.exports = {
  root: true,
  env: { browser: true, es2022: true, node: true },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
  ],
  ignorePatterns: ["dist", ".eslintrc.cjs", "node_modules"],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    ecmaFeatures: { jsx: true },
  },
  plugins: ["react-refresh", "@typescript-eslint"],
  rules: {
    "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
  },
};
```

- [ ] **Step 4: Create .eslintignore**

Create `c:\Projeto\Access\frontend\.eslintignore`:

```
dist/
node_modules/
coverage/
.vite/
```

- [ ] **Step 5: Run lint to check it works**

Run from `c:\Projeto\Access\frontend`: `npm run lint`
Expected: zero errors. Fix any reported issue inline before committing.

- [ ] **Step 6: Run formatter**

Run from `c:\Projeto\Access\frontend`: `npm run format`
Expected: prettier reformats files; should be a no-op if code already conforms.

- [ ] **Step 7: Commit**

```bash
git -C c:/Projeto/Access add frontend/.eslintrc.cjs frontend/.eslintignore frontend/.prettierrc.json frontend/.prettierignore
git -C c:/Projeto/Access commit -m "chore(frontend): configure eslint + prettier"
```

---

## Task 15: Lint validation for backend (ruff + mypy)

**Files:**
- (No new files — config already in `pyproject.toml`)

- [ ] **Step 1: Run ruff check**

Run from `c:\Projeto\Access\backend`: `uv run ruff check .`
Expected: `All checks passed!`. Fix any reported issue inline.

- [ ] **Step 2: Run ruff format check**

Run from `c:\Projeto\Access\backend`: `uv run ruff format --check .`
Expected: `N files already formatted`. If not, run `uv run ruff format .` and commit changes.

- [ ] **Step 3: Run mypy strict**

Run from `c:\Projeto\Access\backend`: `uv run mypy app`
Expected: `Success: no issues found in N source files`.

- [ ] **Step 4: Run full test suite to confirm everything still works**

Ensure postgres is running: `docker compose up -d postgres`.
Run from `c:\Projeto\Access\backend`: `uv run pytest -v`
Expected: all tests pass (test_config + test_health + test_database).

- [ ] **Step 5: Commit any auto-format changes (if any)**

```bash
git -C c:/Projeto/Access add backend
git -C c:/Projeto/Access diff --cached --quiet || git -C c:/Projeto/Access commit -m "chore(backend): ruff format pass"
```

---

## Task 16: Makefile for common dev tasks

**Files:**
- Create: `Makefile`

- [ ] **Step 1: Create Makefile at repo root**

Create `c:\Projeto\Access\Makefile`:

```makefile
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
```

- [ ] **Step 2: Verify make targets work (basic ones)**

If `make` is not installed on Windows, this is informational — most contributors run on WSL/Linux/Mac. On Windows native, contributors run the underlying commands directly.

Run (from any shell that has `make`): `make help`
Expected: prints the list of targets.

- [ ] **Step 3: Commit**

```bash
git -C c:/Projeto/Access add Makefile
git -C c:/Projeto/Access commit -m "chore: add Makefile with dev/test/lint/migrate targets"
```

---

## Task 17: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create CI workflow**

Create `c:\Projeto\Access\.github\workflows\ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    name: Backend (lint + test)
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: fleetops
          POSTGRES_PASSWORD: fleetops_dev_password
          POSTGRES_DB: fleetops
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U fleetops -d fleetops"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 10
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    env:
      ENVIRONMENT: test
      SECRET_KEY: ci-secret-key-not-for-production-please
      DATABASE_URL: postgresql+asyncpg://fleetops:fleetops_dev_password@localhost:5432/fleetops
      REDIS_URL: redis://localhost:6379/0
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "0.5.x"
      - name: Set up Python
        run: uv python install 3.12
      - name: Install dependencies
        working-directory: backend
        run: uv sync --frozen
      - name: Lint (ruff)
        working-directory: backend
        run: |
          uv run ruff check .
          uv run ruff format --check .
      - name: Type check (mypy)
        working-directory: backend
        run: uv run mypy app
      - name: Apply migrations
        working-directory: backend
        run: uv run alembic upgrade head
      - name: Run tests
        working-directory: backend
        run: uv run pytest -v

  frontend:
    name: Frontend (lint + test + build)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json
      - name: Install dependencies
        working-directory: frontend
        run: npm ci
      - name: Lint
        working-directory: frontend
        run: npm run lint
      - name: Test
        working-directory: frontend
        run: npm test
      - name: Build
        working-directory: frontend
        run: npm run build
```

- [ ] **Step 2: Validate YAML syntax locally**

Run: `docker run --rm -v c:/Projeto/Access/.github:/workdir mikefarah/yq:latest 'eval' /workdir/workflows/ci.yml`
Expected: prints the parsed YAML without errors. (Skip if docker pull is undesirable; YAML is short.)

- [ ] **Step 3: Commit**

```bash
git -C c:/Projeto/Access add .github/workflows/ci.yml
git -C c:/Projeto/Access commit -m "ci: GitHub Actions for backend + frontend lint/test/build"
```

---

## Task 18: README documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README.md**

Create `c:\Projeto\Access\README.md`:

````markdown
# FleetOps

SaaS B2B de gestão de manutenção de frota e equipamentos.

> Migração técnica do sistema legado em Microsoft Access (`ERD.accdb`) para uma plataforma web multi-tenant moderna.
> Documento de requisitos completo: [PRD](docs/superpowers/specs/2026-05-15-migracao-access-saas-design.md).

## Stack

- **Backend**: Python 3.12 + FastAPI + SQLAlchemy 2.0 async + PostgreSQL 16
- **Frontend**: React 18 + Vite + TypeScript + TailwindCSS
- **Infra dev**: Docker Compose (postgres + redis + api + frontend)
- **Pacotes**: `uv` (Python), `npm` (Node)

## Pré-requisitos

- Docker Desktop ≥ 4.x (com Docker Compose v2)
- `uv` ≥ 0.5 — `irm https://astral.sh/uv/install.ps1 | iex` (Windows) ou `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Node.js ≥ 20 (recomendado via `nvm`)
- Git ≥ 2.40

## Setup inicial

```powershell
# 1. Clonar o repositório
git clone <repo-url> Access
cd Access

# 2. Copiar variáveis de ambiente
Copy-Item .env.example .env
# Editar .env e trocar SECRET_KEY por uma string aleatória

# 3. Subir infra de dependências (postgres + redis)
docker compose up -d postgres redis

# 4. Instalar deps do backend
cd backend
uv sync
uv run alembic upgrade head
cd ..

# 5. Instalar deps do frontend
cd frontend
npm install
cd ..
```

## Workflow diário

### Subir tudo via Docker

```bash
docker compose up -d
# api → http://localhost:8000
# frontend (build de produção) → http://localhost:8080
# docs API → http://localhost:8000/docs
```

### Modo desenvolvimento (hot reload no frontend)

```bash
# Terminal 1: backend + deps em containers
docker compose up -d postgres redis api

# Terminal 2: frontend em dev mode (hot reload)
cd frontend
npm run dev
# → http://localhost:5173 (proxy /api → backend)
```

### Modo desenvolvimento full local (sem container do backend)

```bash
# Terminal 1: dependências
docker compose up -d postgres redis

# Terminal 2: backend em dev mode
cd backend
$env:DATABASE_URL="postgresql+asyncpg://fleetops:fleetops_dev_password@localhost:5432/fleetops"
$env:REDIS_URL="redis://localhost:6379/0"
$env:SECRET_KEY="any-local-secret-32-chars-or-more"
$env:ENVIRONMENT="dev"
uv run fastapi dev app/main.py --port 8000

# Terminal 3: frontend
cd frontend
npm run dev
```

## Testes

```bash
# Backend
cd backend
uv run pytest -v

# Frontend
cd frontend
npm test

# Tudo
make test  # se tiver make
```

## Lint e formatação

```bash
# Backend
cd backend
uv run ruff check .
uv run ruff format .
uv run mypy app

# Frontend
cd frontend
npm run lint
npm run format
```

## Migrations (Alembic)

```bash
# Aplicar todas pendentes
docker compose exec api alembic upgrade head
# ou: cd backend && uv run alembic upgrade head

# Criar nova migration (P1+ depois que houver modelos)
docker compose exec api alembic revision --autogenerate -m "descrição"

# Voltar uma versão
docker compose exec api alembic downgrade -1
```

## Estrutura do repo

```
backend/        # FastAPI app, models, alembic, tests
frontend/       # React app, components, tests
docker-compose.yml
.github/workflows/ci.yml
docs/superpowers/
  specs/        # PRDs (design specs)
  plans/        # Implementation plans
.env.example
Makefile
```

## Documentos

- [PRD — Migração Access → SaaS](docs/superpowers/specs/2026-05-15-migracao-access-saas-design.md)
- [Plano P0 — Foundation & Dev Environment](docs/superpowers/plans/2026-05-15-p0-foundation-dev-environment.md)

## Próximos passos

Próximo plano de implementação: **P1 — Multi-tenant Auth & RBAC** (a ser escrito após conclusão do P0).
````

- [ ] **Step 2: Verify README renders**

Open in any markdown viewer (VS Code preview, GitHub if pushed) and verify formatting.

- [ ] **Step 3: Commit**

```bash
git -C c:/Projeto/Access add README.md
git -C c:/Projeto/Access commit -m "docs: README with setup, workflow and structure"
```

---

## Task 19: Final integration smoke test (clean slate)

This task is purely verification — no code changes. Confirms a fresh dev can clone the repo and get everything running.

**Files:**
- (none — verification only)

- [ ] **Step 1: Bring everything down**

Run from `c:\Projeto\Access`: `docker compose down -v`
Expected: containers and named volumes removed.

- [ ] **Step 2: Bring everything back up from scratch**

Run: `docker compose up -d --build`
Expected: postgres → redis → api (waits for postgres healthy) → frontend (waits for api healthy). All services report `(healthy)` within ~60s.

- [ ] **Step 3: Apply migrations**

Run: `docker compose exec api alembic upgrade head`
Expected: prints `Running upgrade  -> 0001`.

- [ ] **Step 4: Verify backend**

Run: `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`

Run: `curl http://localhost:8000/docs -o /dev/null -w "%{http_code}\n"`
Expected: `200`.

- [ ] **Step 5: Verify frontend**

Open `http://localhost:8080` in browser.
Expected: "FleetOps" headline + "Backend status: ok".

- [ ] **Step 6: Verify lint + tests still green from scratch**

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest -v
cd ../frontend && npm run lint && npm test && npm run build
```

Expected: all green.

- [ ] **Step 7: Final tag (optional)**

```bash
git -C c:/Projeto/Access tag -a p0-complete -m "P0 — Foundation & Dev Environment complete"
```

---

## Self-Review Checklist (executed by plan author)

- ✅ **Spec coverage**: Cobre toda a Seção 2 do PRD relativa à fundação técnica (stack, deploy local, lint, CI). Não cobre auth/multi-tenant/RBAC (escopo do P1) nem produção em VPS (escopo do P11).
- ✅ **No placeholders**: Todos os arquivos contêm conteúdo executável real, sem TBD/TODO/"add appropriate X".
- ✅ **Type consistency**: `Settings` campos (database_url, redis_url, secret_key, environment, log_level) usados consistentemente em config.py, database.py, env.py, ci.yml e .env.example. Nome `app.api.health.router` referenciado em main.py confere. `queryClient` exportado de queryClient.ts e importado em main.tsx confere.
- ✅ **Bite-sized**: Cada step é uma única ação verificável (~2-5 min).
- ✅ **Code blocks completos**: Todos os comandos com path absoluto Windows ou referência clara ao cwd; toda mudança de código mostra o conteúdo final (não diff parcial).
- ✅ **TDD onde aplicável**: Tasks 4 (health), 6 (database), 10 (App), 12 (HealthCheck) seguem test-first. Infra (Docker, Alembic, lint) usa verificação operacional, que é o equivalente apropriado.
- ✅ **Frequent commits**: Cada task termina em commit; total ~19 commits no P0.
- ✅ **Independência funcional**: Ao fim, há software rodando, testável, deployável localmente — pré-requisito para qualquer plano subsequente.

---

**Fim do plano P0.**
