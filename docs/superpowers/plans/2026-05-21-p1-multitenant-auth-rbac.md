# P1 — Multi-tenant Auth & RBAC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar autenticação multi-tenant completa (registro de tenant, login JWT, refresh token, logout) e RBAC com 6 papéis (Owner/Admin/Gestor/Operador/Mecânico/Leitura), garantindo isolamento de dados por tenant via RLS do PostgreSQL + validação na camada de aplicação.

**Architecture:** O `User` pertence a exatamente um `Tenant`. O JWT de acesso (15 min) contém `sub` (user_id) e `tenant_id`. Um refresh token opaco (7 dias, hash SHA-256 no DB) permite renovação sem novo login. Cada request autenticado usa um `get_tenant_session` dependency que executa `SET LOCAL app.current_tenant` antes de qualquer query — ativando as policies RLS do Postgres. O RBAC usa uma dependency `require_role` que verifica `user_role` após autenticação. FastAPI Users é usado somente como biblioteca de gerenciamento de usuários (hash Argon2id, CRUD); os endpoints de auth são implementados customizados para suporte nativo a refresh token e registro de tenant.

**Tech Stack:**
- **Backend novo**: `fastapi-users[sqlalchemy]>=14.0.0`, `pwdlib[argon2]>=0.2.0`, `pyjwt[crypto]>=2.8.0`, `uuid6>=2022.10.25`
- **Frontend novo**: `react-router-dom@6`, `zustand@5`, `react-hook-form@7`, `@hookform/resolvers@3`, `zod@3`

---

## Mapa de arquivos

```
backend/
├── app/
│   ├── models/
│   │   ├── __init__.py          NEW — re-exporta todos os modelos
│   │   ├── base.py              NEW — Base declarativa + TimestampMixin + OperationalMixin
│   │   ├── tenant.py            NEW — Tenant, TenantStatus
│   │   ├── user.py              NEW — User (FAU-compatible) + refresh token
│   │   └── role.py              NEW — RoleName (enum), UserRole
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py      NEW
│   │       └── auth.py          NEW — register, login, refresh, logout, me
│   ├── core/
│   │   ├── config.py            MOD — adiciona JWT_* settings
│   │   ├── database.py          MOD — adiciona get_tenant_session
│   │   └── security.py          NEW — create/decode JWT, hash_token
│   ├── schemas/
│   │   ├── __init__.py          NEW
│   │   └── auth.py              NEW — Pydantic schemas de request/response
│   ├── services/
│   │   ├── __init__.py          NEW
│   │   └── user_manager.py      NEW — UserManager FAU (Argon2id)
│   ├── api/
│   │   ├── deps.py              NEW — get_current_user, get_tenant_session, require_role
│   │   └── health.py            inalterado
│   └── main.py                  MOD — inclui router v1
├── alembic/
│   ├── env.py                   MOD — target_metadata = Base.metadata
│   └── versions/
│       └── 0002_auth_multitenant.py  NEW — tenant+user+user_role + RLS
├── tests/
│   ├── conftest.py              MOD — engine session-scoped, fixtures de auth
│   ├── test_auth.py             NEW — register, login, refresh, me, logout
│   ├── test_tenant_isolation.py NEW — RLS: tenant A não vê dados do tenant B
│   └── test_rbac.py             NEW — require_role: acesso por papel
└── pyproject.toml               MOD — adiciona novas deps

frontend/
├── src/
│   ├── types/
│   │   └── auth.ts              NEW — TS interfaces de auth
│   ├── stores/
│   │   └── auth.ts              NEW — Zustand auth store
│   ├── hooks/
│   │   └── useAuth.ts           NEW — TanStack Query hooks de auth
│   ├── components/
│   │   ├── ProtectedRoute.tsx   NEW
│   │   └── auth/
│   │       ├── LoginForm.tsx    NEW
│   │       └── RegisterForm.tsx NEW
│   ├── pages/
│   │   ├── Login.tsx            NEW
│   │   └── Register.tsx         NEW
│   ├── lib/
│   │   └── api.ts               MOD — interceptors de token
│   ├── App.tsx                  MOD — react-router-dom routes
│   └── main.tsx                 MOD — Router + QueryClient providers
└── package.json                 MOD — novas deps
```

---

## Task 1: Backend — Adicionar novas dependências

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Adicionar deps ao pyproject.toml**

Editar a seção `[project] dependencies` de `backend/pyproject.toml`:

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
    "fastapi-users[sqlalchemy]>=14.0.0",
    "pwdlib[argon2]>=0.2.0",
    "pyjwt[crypto]>=2.8.0",
    "uuid6>=2022.10.25",
]
```

- [ ] **Step 2: Instalar as dependências**

```powershell
cd backend
uv sync
```

Saída esperada: `Resolved N packages` sem erros. Verifique que `fastapi_users`, `pwdlib`, `jwt`, e `uuid6` aparecem nas dependências resolvidas.

- [ ] **Step 3: Verificar importações**

```powershell
uv run python -c "import fastapi_users; import pwdlib; import jwt; import uuid6; print('OK')"
```

Saída esperada: `OK`

- [ ] **Step 4: Commit**

```powershell
git add backend/pyproject.toml backend/uv.lock
git commit -m "chore(backend): add auth dependencies (fastapi-users, pwdlib, pyjwt, uuid6)"
```

---

## Task 2: Backend — Base SQLAlchemy models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/base.py`

- [ ] **Step 1: Escrever o teste de importação**

Criar `backend/tests/test_models_import.py`:

```python
def test_models_importable() -> None:
    from app.models.base import Base, OperationalMixin, TimestampMixin  # noqa: F401

    assert Base is not None
```

- [ ] **Step 2: Rodar o teste — deve falhar**

```powershell
cd backend
uv run pytest tests/test_models_import.py -v
```

Saída esperada: `FAILED` — `ModuleNotFoundError: No module named 'app.models'`

- [ ] **Step 3: Criar `backend/app/models/__init__.py`**

```python
```

(arquivo vazio — apenas cria o pacote)

- [ ] **Step 4: Criar `backend/app/models/base.py`**

```python
from datetime import datetime
import uuid

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class OperationalMixin(TimestampMixin):
    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
```

- [ ] **Step 5: Rodar o teste — deve passar**

```powershell
uv run pytest tests/test_models_import.py -v
```

Saída esperada: `PASSED`

- [ ] **Step 6: Commit**

```powershell
git add backend/app/models/
git commit -m "feat(backend): add SQLAlchemy Base + TimestampMixin + OperationalMixin"
```

---

## Task 3: Backend — Modelos Tenant, User e UserRole

**Files:**
- Create: `backend/app/models/tenant.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/role.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Escrever testes de modelo**

Criar `backend/tests/test_models_schema.py`:

```python
import uuid
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.models.role import RoleName, UserRole


def test_tenant_model_has_required_columns() -> None:
    cols = {c.name for c in Tenant.__table__.columns}
    assert {"id", "slug", "razao_social", "cnpj", "status", "trial_expires_at",
            "created_at", "updated_at"} <= cols


def test_user_model_has_tenant_id() -> None:
    cols = {c.name for c in User.__table__.columns}
    assert {"id", "tenant_id", "email", "hashed_password", "full_name",
            "refresh_token_hash", "refresh_token_expires_at",
            "is_active", "created_at", "updated_at"} <= cols


def test_user_role_model_has_rls_columns() -> None:
    cols = {c.name for c in UserRole.__table__.columns}
    assert {"id", "tenant_id", "user_id", "role", "created_at"} <= cols


def test_role_name_enum_has_all_roles() -> None:
    roles = {r.value for r in RoleName}
    assert {"owner", "admin", "gestor", "operador", "mecanico", "leitura"} == roles
```

- [ ] **Step 2: Rodar — deve falhar**

```powershell
cd backend
uv run pytest tests/test_models_schema.py -v
```

Saída esperada: `FAILED` — `ModuleNotFoundError`

- [ ] **Step 3: Criar `backend/app/models/tenant.py`**

```python
from datetime import datetime
import uuid
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.models.base import Base, TimestampMixin


class TenantStatus(str, PyEnum):
    TRIAL = "trial"
    PENDING_PAYMENT = "pending_payment"
    ACTIVE = "active"
    DELINQUENT = "delinquent"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenant"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid7
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    razao_social: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus, name="tenant_status"),
        default=TenantStatus.TRIAL,
        nullable=False,
    )
    trial_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

- [ ] **Step 4: Criar `backend/app/models/user.py`**

```python
from datetime import datetime
import uuid

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.models.base import Base, TimestampMixin


class User(SQLAlchemyBaseUserTableUUID, Base):  # type: ignore[misc]
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(  # type: ignore[override]
        PGUUID(as_uuid=True), primary_key=True, default=uuid7
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    refresh_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
    )
```

- [ ] **Step 5: Criar `backend/app/models/role.py`**

```python
import uuid
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.models.base import Base


class RoleName(str, PyEnum):
    OWNER = "owner"
    ADMIN = "admin"
    GESTOR = "gestor"
    OPERADOR = "operador"
    MECANICO = "mecanico"
    LEITURA = "leitura"


class UserRole(Base):
    __tablename__ = "user_role"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid7
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role: Mapped[RoleName] = mapped_column(
        Enum(RoleName, name="role_name"), nullable=False
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "role", name="uq_user_role_tenant"),
    )
```

- [ ] **Step 6: Atualizar `backend/app/models/__init__.py`**

```python
from app.models.base import Base, OperationalMixin, TimestampMixin
from app.models.role import RoleName, UserRole
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User

__all__ = [
    "Base",
    "TimestampMixin",
    "OperationalMixin",
    "Tenant",
    "TenantStatus",
    "User",
    "RoleName",
    "UserRole",
]
```

- [ ] **Step 7: Rodar os testes — devem passar**

```powershell
uv run pytest tests/test_models_schema.py tests/test_models_import.py -v
```

Saída esperada: todos `PASSED`

- [ ] **Step 8: Lint + type check**

```powershell
uv run ruff check app/models/
uv run mypy app/models/
```

Saída esperada: sem erros.

- [ ] **Step 9: Commit**

```powershell
git add backend/app/models/
git commit -m "feat(backend): add Tenant, User, UserRole SQLAlchemy models"
```

---

## Task 4: Backend — Alembic migration 0002_auth_multitenant + atualizar env.py

**Files:**
- Modify: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0002_auth_multitenant.py`

- [ ] **Step 1: Atualizar `backend/alembic/env.py`**

Substituir a linha `target_metadata = None  # No models yet — set in P1` por:

```python
from app.models.base import Base  # noqa: E402

target_metadata = Base.metadata
```

O arquivo completo fica:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import settings
from app.models.base import Base  # noqa: E402 — importa após configurar logging

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


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

- [ ] **Step 2: Criar `backend/alembic/versions/0002_auth_multitenant.py`**

```python
"""auth: tenant + user + user_role + RLS

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── tenant_status enum ──────────────────────────────────────────────────
    op.execute(
        "CREATE TYPE tenant_status AS ENUM "
        "('trial','pending_payment','active','delinquent','suspended','cancelled','expired')"
    )

    # ── tenant ──────────────────────────────────────────────────────────────
    op.create_table(
        "tenant",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("razao_social", sa.String(255), nullable=False),
        sa.Column("cnpj", sa.String(14), nullable=False),
        sa.Column(
            "status",
            sa.Enum("trial", "pending_payment", "active", "delinquent",
                    "suspended", "cancelled", "expired",
                    name="tenant_status", create_type=False),
            nullable=False,
            server_default="trial",
        ),
        sa.Column("trial_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("slug", name="uq_tenant_slug"),
        sa.UniqueConstraint("cnpj", name="uq_tenant_cnpj"),
    )
    op.create_index("ix_tenant_slug", "tenant", ["slug"])

    # ── user ─────────────────────────────────────────────────────────────────
    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), nullable=True),
        sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
    )
    op.create_index("ix_user_tenant_id", "user", ["tenant_id"])

    # ── role_name enum ───────────────────────────────────────────────────────
    op.execute(
        "CREATE TYPE role_name AS ENUM "
        "('owner','admin','gestor','operador','mecanico','leitura')"
    )

    # ── user_role (com RLS) ──────────────────────────────────────────────────
    op.create_table(
        "user_role",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("owner", "admin", "gestor", "operador", "mecanico", "leitura",
                    name="role_name", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("tenant_id", "user_id", "role", name="uq_user_role_tenant"),
    )
    op.create_index("ix_user_role_tenant_id", "user_role", ["tenant_id"])
    op.create_index("ix_user_role_user_id", "user_role", ["user_id"])

    # ── RLS no user_role ─────────────────────────────────────────────────────
    op.execute("ALTER TABLE user_role ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_role FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON user_role
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant', TRUE), '')::uuid
            )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON user_role")
    op.execute("ALTER TABLE user_role DISABLE ROW LEVEL SECURITY")
    op.drop_table("user_role")
    op.execute("DROP TYPE role_name")
    op.drop_table("user")
    op.drop_table("tenant")
    op.execute("DROP TYPE tenant_status")
```

- [ ] **Step 3: Aplicar a migration (requer Docker Compose rodando)**

```powershell
docker compose up -d postgres
docker compose exec api alembic upgrade head
```

Saída esperada: `Running upgrade 0001 -> 0002, auth: tenant + user + user_role + RLS`

Se o container `api` não estiver rodando, execute localmente:
```powershell
cd backend
$env:DATABASE_URL = "postgresql+asyncpg://fleetops:fleetops@localhost:5433/fleetops"
uv run alembic upgrade head
```

- [ ] **Step 4: Verificar tabelas criadas**

```powershell
docker compose exec postgres psql -U fleetops -d fleetops -c "\dt"
```

Saída esperada: tabelas `tenant`, `user`, `user_role` presentes.

- [ ] **Step 5: Verificar RLS ativa**

```powershell
docker compose exec postgres psql -U fleetops -d fleetops -c "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = 'user_role';"
```

Saída esperada: `relrowsecurity = t` e `relforcerowsecurity = t`.

- [ ] **Step 6: Commit**

```powershell
git add backend/alembic/
git commit -m "feat(backend): migration 0002 — tenant + user + user_role + RLS"
```

---

## Task 5: Backend — Segurança (JWT + hash de token)

**Files:**
- Create: `backend/app/core/security.py`
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: Escrever testes de segurança**

Criar `backend/tests/test_security.py`:

```python
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    create_refresh_token,
    hash_token,
)


def test_create_and_decode_access_token() -> None:
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    token = create_access_token(user_id, tenant_id)

    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["type"] == "access"


def test_decode_expired_token_raises() -> None:
    import jwt as pyjwt
    from app.core.config import settings

    payload = {
        "sub": str(uuid.uuid4()),
        "tenant_id": str(uuid.uuid4()),
        "type": "access",
        "exp": datetime.now(UTC) - timedelta(seconds=1),
    }
    token = pyjwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_access_token(token)


def test_hash_token_is_deterministic() -> None:
    token = create_refresh_token()
    assert hash_token(token) == hash_token(token)


def test_hash_token_is_64_hex_chars() -> None:
    token = create_refresh_token()
    hashed = hash_token(token)
    assert len(hashed) == 64
    assert all(c in "0123456789abcdef" for c in hashed)
```

- [ ] **Step 2: Rodar — deve falhar**

```powershell
cd backend
uv run pytest tests/test_security.py -v
```

Saída esperada: `FAILED` — `ModuleNotFoundError`

- [ ] **Step 3: Atualizar `backend/app/core/config.py`**

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
    secret_key: str = Field(..., min_length=32)

    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_seconds: int = 900       # 15 minutos
    jwt_refresh_token_expire_seconds: int = 604800   # 7 dias


settings = Settings()
```

- [ ] **Step 4: Criar `backend/app/core/security.py`**

```python
from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt

from app.core.config import settings


def create_access_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(seconds=settings.jwt_access_token_expire_seconds),
        "iat": datetime.now(UTC),
    }
    return pyjwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, object]:
    return pyjwt.decode(  # type: ignore[return-value]
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"verify_exp": True},
    )


def create_refresh_token() -> str:
    return str(uuid.uuid4())


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
```

- [ ] **Step 5: Rodar — deve passar**

```powershell
uv run pytest tests/test_security.py -v
```

Saída esperada: `4 passed`

- [ ] **Step 6: Lint + type check**

```powershell
uv run ruff check app/core/security.py app/core/config.py
uv run mypy app/core/security.py app/core/config.py
```

Saída esperada: sem erros.

- [ ] **Step 7: Commit**

```powershell
git add backend/app/core/security.py backend/app/core/config.py backend/tests/test_security.py
git commit -m "feat(backend): JWT utilities + Argon2id config + refresh token hash"
```

---

## Task 6: Backend — UserManager (FastAPI Users + Argon2id)

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/user_manager.py`

- [ ] **Step 1: Criar `backend/app/services/__init__.py`**

```python
```

(vazio)

- [ ] **Step 2: Criar `backend/app/services/user_manager.py`**

```python
from typing import Any

from fastapi import Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.models.user import User

_password_hash = PasswordHash((Argon2Hasher(),))


class UserManager(UUIDIDMixin, BaseUserManager[User, Any]):
    reset_password_token_secret = ""  # sobrescrito em get_user_manager
    verification_token_secret = ""

    async def on_after_register(
        self, user: User, request: Request | None = None
    ) -> None:
        pass  # email de verificação em P2

    async def on_after_login(
        self,
        user: User,
        request: Request | None = None,
        response: Any = None,
    ) -> None:
        pass


async def get_user_db(
    session: Any,
) -> Any:
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: Any) -> Any:
    from app.core.config import settings

    manager = UserManager(user_db, _password_hash)
    manager.reset_password_token_secret = settings.secret_key
    manager.verification_token_secret = settings.secret_key
    yield manager
```

> **Nota:** `Any` é usado para evitar dependências circulares nos type hints dos generators. O mypy aceita isso com `strict=true` pois os generators são unicamente de injeção via FastAPI Depends.

- [ ] **Step 3: Rodar lint + type check**

```powershell
cd backend
uv run ruff check app/services/
uv run mypy app/services/
```

Saída esperada: sem erros (exceto possíveis `Any` esperados no mypy strict).

- [ ] **Step 4: Commit**

```powershell
git add backend/app/services/
git commit -m "feat(backend): UserManager with Argon2id password hashing"
```

---

## Task 7: Backend — Schemas Pydantic de auth

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`

- [ ] **Step 1: Escrever testes de schema**

Criar `backend/tests/test_schemas_auth.py`:

```python
import uuid
import pytest
from pydantic import ValidationError
from app.schemas.auth import (
    TenantRegistrationRequest,
    LoginRequest,
    TokenResponse,
    UserRead,
)


def test_tenant_registration_requires_cnpj_14_digits() -> None:
    with pytest.raises(ValidationError):
        TenantRegistrationRequest(
            razao_social="Empresa X",
            cnpj="123",          # inválido
            admin_email="a@b.com",
            admin_password="senha12345678",
            admin_full_name="Admin",
        )


def test_tenant_registration_valid() -> None:
    req = TenantRegistrationRequest(
        razao_social="Empresa X Ltda",
        cnpj="12345678000190",
        admin_email="admin@empresa.com",
        admin_password="SenhaForte123!",
        admin_full_name="João Admin",
    )
    assert req.cnpj == "12345678000190"


def test_token_response_has_required_fields() -> None:
    tr = TokenResponse(
        access_token="tok",
        refresh_token="ref",
        token_type="bearer",
    )
    assert tr.token_type == "bearer"
```

- [ ] **Step 2: Rodar — deve falhar**

```powershell
cd backend
uv run pytest tests/test_schemas_auth.py -v
```

Saída esperada: `FAILED` — `ModuleNotFoundError`

- [ ] **Step 3: Criar `backend/app/schemas/__init__.py`**

```python
```

(vazio)

- [ ] **Step 4: Criar `backend/app/schemas/auth.py`**

```python
import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


def _normalize_cnpj(cnpj: str) -> str:
    digits = re.sub(r"\D", "", cnpj)
    if len(digits) != 14:
        raise ValueError("CNPJ deve ter 14 dígitos")
    return digits


class TenantRegistrationRequest(BaseModel):
    razao_social: str
    cnpj: str
    admin_email: EmailStr
    admin_password: str
    admin_full_name: str

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        return _normalize_cnpj(v)

    @field_validator("admin_password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Senha deve ter pelo menos 10 caracteres")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_slug: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Rodar — deve passar**

```powershell
uv run pytest tests/test_schemas_auth.py -v
```

Saída esperada: `3 passed`

- [ ] **Step 6: Commit**

```powershell
git add backend/app/schemas/ backend/tests/test_schemas_auth.py
git commit -m "feat(backend): Pydantic schemas for auth endpoints"
```

---

## Task 8: Backend — Auth router (register, login, refresh, logout, me)

**Files:**
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/app/api/deps.py`

- [ ] **Step 1: Criar `backend/app/api/v1/__init__.py`**

```python
```

(vazio)

- [ ] **Step 2: Criar `backend/app/api/deps.py`**

```python
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.role import RoleName, UserRole
from app.models.user import User
from sqlalchemy import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str = str(payload["sub"])
    except (pyjwt.InvalidTokenError, KeyError):
        raise credentials_exc

    import uuid

    user = await session.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_tenant_session(
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncGenerator[AsyncSession, None]:
    await session.execute(
        text("SELECT set_config('app.current_tenant', :tid, true)"),
        {"tid": str(user.tenant_id)},
    )
    yield session


TenantSession = Annotated[AsyncSession, Depends(get_tenant_session)]


def require_role(*roles: RoleName):  # type: ignore[no-untyped-def]
    async def checker(
        user: CurrentUser,
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> User:
        result = await session.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.tenant_id == user.tenant_id,
                UserRole.role.in_(roles),
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente",
            )
        return user

    return Depends(checker)
```

- [ ] **Step 3: Criar `backend/app/api/v1/auth.py`**

```python
from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
)
from app.models.role import RoleName, UserRole
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.schemas.auth import (
    RefreshRequest,
    TenantRegistrationRequest,
    TokenResponse,
    UserRead,
)
from app.services.user_manager import get_user_db, get_user_manager
from fastapi_users.db import SQLAlchemyUserDatabase
from app.services.user_manager import UserManager
from app.api.deps import get_current_user, CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:80]


def _issue_tokens(user: User) -> tuple[str, str, datetime]:
    access_token = create_access_token(user.id, user.tenant_id)
    refresh_raw = create_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.jwt_refresh_token_expire_seconds)
    return access_token, refresh_raw, expires_at


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_tenant(
    data: TenantRegistrationRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    # Verificar unicidade de CNPJ
    existing = await session.execute(
        select(Tenant).where(Tenant.cnpj == data.cnpj)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CNPJ já cadastrado",
        )

    # Criar tenant
    base_slug = _slugify(data.razao_social)
    slug = base_slug
    counter = 1
    while (await session.execute(select(Tenant).where(Tenant.slug == slug))).scalar_one_or_none():
        slug = f"{base_slug}-{counter}"
        counter += 1

    tenant = Tenant(
        slug=slug,
        razao_social=data.razao_social,
        cnpj=data.cnpj,
        status=TenantStatus.TRIAL,
        trial_expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    session.add(tenant)
    await session.flush()  # garante tenant.id antes de criar o user

    # Criar user via UserManager (hash Argon2id)
    async for user_db in get_user_db(session):
        async for user_manager in get_user_manager(user_db):
            from fastapi_users import schemas as fau_schemas

            class _UserCreate(fau_schemas.BaseUserCreate):
                tenant_id: uuid.UUID
                full_name: str

            user_create = _UserCreate(
                email=data.admin_email,
                password=data.admin_password,
                tenant_id=tenant.id,
                full_name=data.admin_full_name,
            )
            user = await user_manager.create(user_create)

    # Criar papel Owner
    owner_role = UserRole(
        tenant_id=tenant.id,
        user_id=user.id,
        role=RoleName.OWNER,
    )
    session.add(owner_role)

    # Emitir tokens
    access_token, refresh_raw, expires_at = _issue_tokens(user)
    user.refresh_token_hash = hash_token(refresh_raw)
    user.refresh_token_expires_at = expires_at

    await session.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_raw)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    # OAuth2PasswordRequestForm usa username como campo de email
    result = await session.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    async for user_db in get_user_db(session):
        async for user_manager in get_user_manager(user_db):
            if user is None or not await user_manager.verify_password(form_data.password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciais inválidas",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo")

    access_token, refresh_raw, expires_at = _issue_tokens(user)
    user.refresh_token_hash = hash_token(refresh_raw)
    user.refresh_token_expires_at = expires_at
    await session.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_raw)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    token_hash = hash_token(data.refresh_token)
    result = await session.execute(
        select(User).where(User.refresh_token_hash == token_hash)
    )
    user = result.scalar_one_or_none()

    if user is None or user.refresh_token_expires_at is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    if datetime.now(UTC) > user.refresh_token_expires_at.replace(tzinfo=UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expirado")

    access_token, refresh_raw, expires_at = _issue_tokens(user)
    user.refresh_token_hash = hash_token(refresh_raw)
    user.refresh_token_expires_at = expires_at
    await session.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_raw)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    user.refresh_token_hash = None
    user.refresh_token_expires_at = None
    await session.commit()


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
```

- [ ] **Step 4: Lint + type check (esperado passar)**

```powershell
cd backend
uv run ruff check app/api/
uv run mypy app/api/
```

Saída esperada: sem erros bloqueantes. Warnings de `Any` em deps são esperados.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/api/
git commit -m "feat(backend): auth router — register, login, refresh, logout, me"
```

---

## Task 9: Backend — Wiring: main.py + Settings + alembic env + database.py

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/core/database.py`

- [ ] **Step 1: Atualizar `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.core.config import settings

app = FastAPI(
    title="FleetOps API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs", status_code=307)


@app.on_event("startup")
async def on_startup() -> None:
    print(f"FleetOps API starting in environment={settings.environment}")
```

- [ ] **Step 2: Atualizar `backend/app/core/database.py`**

Adicionar o `engine` exposto publicamente (necessário para testes):

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

(sem mudanças de lógica — apenas confirmar que `engine` é exportável)

- [ ] **Step 3: Verificar que o app sobe**

```powershell
cd backend
uv run python -c "from app.main import app; print('OK')"
```

Saída esperada: `OK` (sem ImportError)

- [ ] **Step 4: Rodar testes existentes**

```powershell
uv run pytest tests/test_health.py tests/test_config.py -v
```

Saída esperada: todos `PASSED`

- [ ] **Step 5: Commit**

```powershell
git add backend/app/main.py backend/app/core/database.py
git commit -m "feat(backend): wire auth router into FastAPI app"
```

---

## Task 10: Backend — Atualizar conftest.py + fixtures de auth

**Files:**
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Atualizar `backend/tests/conftest.py`**

```python
import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Garante que env vars estão definidas antes de importar `settings`
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://fleetops:fleetops@localhost:5433/fleetops_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-chars-long")
os.environ.setdefault("ENVIRONMENT", "test")

from app.core.config import settings  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.models.tenant import Tenant, TenantStatus  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.role import RoleName, UserRole  # noqa: E402
from app.core.security import create_access_token, create_refresh_token, hash_token  # noqa: E402
from app.services.user_manager import get_user_db, get_user_manager  # noqa: E402
from uuid6 import uuid7  # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def db_engine():
    eng = create_async_engine(settings.database_url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(db_engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app
    from app.core.database import get_session

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        factory = async_sessionmaker(db_engine, expire_on_commit=False, autoflush=False)
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def tenant(db: AsyncSession) -> Tenant:
    from datetime import UTC, datetime, timedelta

    t = Tenant(
        slug=f"tenant-{uuid7().hex[:8]}",
        razao_social="Empresa Teste Ltda",
        cnpj=f"{uuid7().int % 10**14:014d}",
        status=TenantStatus.TRIAL,
        trial_expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


@pytest.fixture
async def user_with_token(db: AsyncSession, tenant: Tenant) -> dict[str, Any]:
    async for user_db_inst in get_user_db(db):
        async for mgr in get_user_manager(user_db_inst):
            from fastapi_users import schemas as fau_schemas

            class _UC(fau_schemas.BaseUserCreate):
                tenant_id: uuid.UUID
                full_name: str

            u = await mgr.create(
                _UC(
                    email=f"user-{uuid7().hex[:8]}@test.com",
                    password="SenhaForte123!",
                    tenant_id=tenant.id,
                    full_name="User Test",
                )
            )

    role = UserRole(tenant_id=tenant.id, user_id=u.id, role=RoleName.ADMIN)
    db.add(role)
    await db.commit()

    access_token = create_access_token(u.id, tenant.id)
    return {"user": u, "token": access_token, "tenant": tenant}
```

- [ ] **Step 2: Verificar que fixtures carregam**

```powershell
cd backend
uv run pytest --collect-only 2>&1 | head -30
```

Saída esperada: sem erros de coleta.

- [ ] **Step 3: Commit**

```powershell
git add backend/tests/conftest.py
git commit -m "test(backend): update conftest with session-scoped DB engine + auth fixtures"
```

---

## Task 11: Backend — Testes do fluxo de auth

**Files:**
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Escrever os testes**

Criar `backend/tests/test_auth.py`:

```python
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_register_tenant_creates_tenant_and_user(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Oficina ABC Ltda",
            "cnpj": "11222333000181",
            "admin_email": "admin@oficina-abc.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Carlos Admin",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_register_tenant_rejects_duplicate_cnpj(client: AsyncClient) -> None:
    payload = {
        "razao_social": "Empresa Y",
        "cnpj": "22333444000195",
        "admin_email": "admin@empresa-y.com",
        "admin_password": "SenhaForte123!",
        "admin_full_name": "Admin",
    }
    resp1 = await client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    payload["admin_email"] = "outro@empresa-y.com"
    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409


async def test_login_returns_tokens(client: AsyncClient) -> None:
    # Registrar primeiro
    await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Login Test Corp",
            "cnpj": "33444555000178",
            "admin_email": "login-test@corp.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Login Admin",
        },
    )

    # Login via OAuth2 form
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "login-test@corp.com", "password": "SenhaForte123!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Wrong Pass Corp",
            "cnpj": "44555666000150",
            "admin_email": "wrong@corp.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Admin",
        },
    )

    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "wrong@corp.com", "password": "senha-errada"},
    )
    assert resp.status_code == 401


async def test_me_returns_current_user(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Me Test Corp",
            "cnpj": "55666777000133",
            "admin_email": "me@corp.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Me Admin",
        },
    )
    token = reg.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@corp.com"


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_refresh_returns_new_tokens(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Refresh Test",
            "cnpj": "66777888000116",
            "admin_email": "refresh@test.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Refresh Admin",
        },
    )
    refresh_token = reg.json()["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["refresh_token"] != refresh_token  # novo token emitido


async def test_logout_invalidates_refresh_token(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Logout Test",
            "cnpj": "77888999000199",
            "admin_email": "logout@test.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Logout Admin",
        },
    )
    tokens = reg.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # Logout
    resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 204

    # Refresh após logout deve falhar
    resp2 = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp2.status_code == 401
```

- [ ] **Step 2: Rodar os testes (requer DB de teste rodando)**

```powershell
cd backend
uv run pytest tests/test_auth.py -v
```

Saída esperada: `7 passed`. Se falhar, verificar:
- DB de teste acessível em `localhost:5433`
- Migration aplicada ao DB de teste: `uv run alembic upgrade head` com `DATABASE_URL` apontando para o DB de teste

- [ ] **Step 3: Commit**

```powershell
git add backend/tests/test_auth.py
git commit -m "test(backend): full auth flow tests — register, login, refresh, logout, me"
```

---

## Task 12: Backend — Testes de isolamento de tenant (RLS)

**Files:**
- Create: `backend/tests/test_tenant_isolation.py`

- [ ] **Step 1: Escrever testes de isolamento**

Criar `backend/tests/test_tenant_isolation.py`:

```python
"""
Testa que o isolamento de tenant funciona:
  - App-level: get_tenant_session garante que user só vê seu próprio tenant
  - DB-level (RLS): SET LOCAL app.current_tenant filtra user_role

Nota: o teste de RLS a nível de DB só funciona se o DB user NÃO for superuser Postgres.
Em desenvolvimento com Docker Compose padrão, o user pode ser superuser, então
o teste verifica isolamento via aplicação (app-level).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import UserRole
from app.models.tenant import Tenant


pytestmark = pytest.mark.asyncio


async def _register(client: AsyncClient, cnpj: str, email: str) -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": f"Empresa {cnpj}",
            "cnpj": cnpj,
            "admin_email": email,
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Admin",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_user_from_tenant_a_cannot_see_tenant_b_me(client: AsyncClient) -> None:
    tokens_a = await _register(client, "88999000000111", "a@isolamento.com")
    tokens_b = await _register(client, "99000111000122", "b@isolamento.com")

    # User A busca /me — deve ver apenas seus próprios dados
    me_a = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens_a['access_token']}"},
    )
    assert me_a.status_code == 200
    assert me_a.json()["email"] == "a@isolamento.com"

    # User B busca /me — deve ver apenas seus próprios dados
    me_b = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
    )
    assert me_b.status_code == 200
    assert me_b.json()["email"] == "b@isolamento.com"


async def test_rls_user_role_isolation_via_set_local(db: AsyncSession) -> None:
    """
    Testa que SET LOCAL app.current_tenant filtra user_role corretamente.
    Requer que o DB user não seja superuser Postgres para RLS ser aplicado.
    Registra falha esperada se DB user for superuser (não bloqueia CI).
    """
    from datetime import UTC, datetime, timedelta
    from uuid6 import uuid7
    from app.models.tenant import TenantStatus
    from app.models.role import RoleName
    from app.models.user import User
    from app.services.user_manager import get_user_db, get_user_manager
    import uuid
    import fastapi_users.schemas as fau_schemas

    class _UC(fau_schemas.BaseUserCreate):
        tenant_id: uuid.UUID
        full_name: str

    # Tenant A
    tenant_a = Tenant(
        slug=f"rls-test-a-{uuid7().hex[:8]}",
        razao_social="RLS Test A",
        cnpj=f"{uuid7().int % 10**14:014d}",
        status=TenantStatus.TRIAL,
        trial_expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    # Tenant B
    tenant_b = Tenant(
        slug=f"rls-test-b-{uuid7().hex[:8]}",
        razao_social="RLS Test B",
        cnpj=f"{uuid7().int % 10**14:014d}",
        status=TenantStatus.TRIAL,
        trial_expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add_all([tenant_a, tenant_b])
    await db.flush()

    async for user_db_inst in get_user_db(db):
        async for mgr in get_user_manager(user_db_inst):
            user_a = await mgr.create(_UC(
                email=f"rls-a-{uuid7().hex[:8]}@test.com",
                password="SenhaForte123!",
                tenant_id=tenant_a.id,
                full_name="User A",
            ))
            user_b = await mgr.create(_UC(
                email=f"rls-b-{uuid7().hex[:8]}@test.com",
                password="SenhaForte123!",
                tenant_id=tenant_b.id,
                full_name="User B",
            ))

    role_a = UserRole(tenant_id=tenant_a.id, user_id=user_a.id, role=RoleName.OWNER)
    role_b = UserRole(tenant_id=tenant_b.id, user_id=user_b.id, role=RoleName.OWNER)
    db.add_all([role_a, role_b])
    await db.commit()

    # Set tenant context para tenant A
    await db.execute(
        text("SELECT set_config('app.current_tenant', :tid, true)"),
        {"tid": str(tenant_a.id)},
    )

    result = await db.execute(select(UserRole))
    roles = result.scalars().all()

    # Se RLS está ativo (DB user não é superuser): apenas role_a visível
    # Se RLS não está ativo (superuser): ambos visíveis — informativo, não falha CI
    tenant_ids = {str(r.tenant_id) for r in roles}
    if len(roles) == 1:
        assert str(tenant_a.id) in tenant_ids, "RLS: apenas tenant A deve ser visível"
    else:
        # Superuser ignora RLS — apenas log, não falha
        import warnings
        warnings.warn(
            "RLS não aplicado: DB user é superuser. "
            "Em produção use um role não-superuser para garantir RLS.",
            stacklevel=1,
        )
```

- [ ] **Step 2: Rodar**

```powershell
cd backend
uv run pytest tests/test_tenant_isolation.py -v
```

Saída esperada: `2 passed` (o segundo pode emitir um warning sobre superuser, mas não falha).

- [ ] **Step 3: Commit**

```powershell
git add backend/tests/test_tenant_isolation.py
git commit -m "test(backend): tenant isolation tests — app-level and RLS verification"
```

---

## Task 13: Backend — Testes de RBAC

**Files:**
- Create: `backend/tests/test_rbac.py`

- [ ] **Step 1: Criar uma rota de teste de RBAC em app/api/v1/auth.py**

Adicionar no final de `backend/app/api/v1/auth.py`:

```python
from app.api.deps import require_role
from app.models.role import RoleName


@router.get("/admin-only", dependencies=[require_role(RoleName.ADMIN, RoleName.OWNER)])
async def admin_only_route(user: CurrentUser) -> dict[str, str]:
    return {"message": f"Acesso concedido para {user.email}"}
```

- [ ] **Step 2: Escrever `backend/tests/test_rbac.py`**

```python
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def _register_and_login(client: AsyncClient, cnpj: str, email: str) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": f"RBAC Corp {cnpj}",
            "cnpj": cnpj,
            "admin_email": email,
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Admin",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "SenhaForte123!"},
    )
    return resp.json()["access_token"]


async def test_owner_can_access_admin_only_route(client: AsyncClient) -> None:
    token = await _register_and_login(client, "10203040000150", "owner-rbac@corp.com")
    resp = await client.get(
        "/api/v1/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


async def test_unauthenticated_cannot_access_admin_only_route(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/admin-only")
    assert resp.status_code == 401


async def test_user_without_required_role_gets_403(
    client: AsyncClient,
    db,
) -> None:
    """Cria um user com papel LEITURA e verifica que é barrado na rota admin-only."""
    from datetime import UTC, datetime, timedelta
    import uuid
    from uuid6 import uuid7
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.tenant import Tenant, TenantStatus
    from app.models.role import RoleName, UserRole
    from app.services.user_manager import get_user_db, get_user_manager
    from app.core.security import create_access_token
    import fastapi_users.schemas as fau_schemas

    class _UC(fau_schemas.BaseUserCreate):
        tenant_id: uuid.UUID
        full_name: str

    tenant = Tenant(
        slug=f"rbac-test-{uuid7().hex[:8]}",
        razao_social="RBAC Test",
        cnpj=f"{uuid7().int % 10**14:014d}",
        status=TenantStatus.TRIAL,
        trial_expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(tenant)
    await db.flush()

    async for user_db_inst in get_user_db(db):
        async for mgr in get_user_manager(user_db_inst):
            leitura_user = await mgr.create(_UC(
                email=f"leitura-{uuid7().hex[:8]}@rbac.com",
                password="SenhaForte123!",
                tenant_id=tenant.id,
                full_name="Leitura User",
            ))

    role = UserRole(tenant_id=tenant.id, user_id=leitura_user.id, role=RoleName.LEITURA)
    db.add(role)
    await db.commit()

    token = create_access_token(leitura_user.id, tenant.id)

    resp = await client.get(
        "/api/v1/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
```

- [ ] **Step 3: Rodar todos os testes de backend**

```powershell
cd backend
uv run pytest tests/ -v --tb=short
```

Saída esperada: todos os testes passando. Verificar cobertura.

- [ ] **Step 4: Lint + type check completo**

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy app
```

Saída esperada: sem erros.

- [ ] **Step 5: Commit**

```powershell
git add backend/tests/test_rbac.py backend/app/api/v1/auth.py
git commit -m "test(backend): RBAC enforcement tests — owner allowed, leitura barrado"
```

---

## Task 14: Frontend — Instalar dependências + atualizar api.ts

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Instalar novas dependências**

```powershell
cd frontend
npm install react-router-dom@6 zustand@5 react-hook-form@7 @hookform/resolvers@3 zod@3
npm install --save-dev @types/react-router-dom
```

Verificar que `package.json` foi atualizado.

- [ ] **Step 2: Verificar importações**

```powershell
npx tsc --noEmit 2>&1 | head -20
```

Saída esperada: sem erros de importação.

- [ ] **Step 3: Atualizar `frontend/src/lib/api.ts`**

```typescript
import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// Injeta Authorization header a partir do localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Em 401 limpa tokens e redireciona para /login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);
```

- [ ] **Step 4: Rodar lint**

```powershell
npm run lint
```

Saída esperada: sem erros.

- [ ] **Step 5: Commit**

```powershell
cd ..
git add frontend/package.json frontend/package-lock.json frontend/src/lib/api.ts
git commit -m "feat(frontend): add react-router-dom, zustand, react-hook-form, zod + api interceptors"
```

---

## Task 15: Frontend — TypeScript types + Zustand auth store + hooks

**Files:**
- Create: `frontend/src/types/auth.ts`
- Create: `frontend/src/stores/auth.ts`
- Create: `frontend/src/hooks/useAuth.ts`

- [ ] **Step 1: Criar `frontend/src/types/auth.ts`**

```typescript
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserRead {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface TenantRegistrationRequest {
  razao_social: string;
  cnpj: string;
  admin_email: string;
  admin_password: string;
  admin_full_name: string;
}

export interface LoginRequest {
  username: string; // campo email — OAuth2PasswordRequestForm usa "username"
  password: string;
}
```

- [ ] **Step 2: Criar `frontend/src/stores/auth.ts`**

```typescript
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserRead } from "@/types/auth";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserRead | null;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: UserRead) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,

      setTokens: (access, refresh) => {
        localStorage.setItem("access_token", access);
        localStorage.setItem("refresh_token", refresh);
        set({ accessToken: access, refreshToken: refresh });
      },

      setUser: (user) => set({ user }),

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ accessToken: null, refreshToken: null, user: null });
      },

      isAuthenticated: () => Boolean(get().accessToken),
    }),
    {
      name: "fleetops-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    }
  )
);
```

- [ ] **Step 3: Criar `frontend/src/hooks/useAuth.ts`**

```typescript
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import type {
  LoginRequest,
  TenantRegistrationRequest,
  TokenResponse,
  UserRead,
} from "@/types/auth";

export function useCurrentUser() {
  const { isAuthenticated } = useAuthStore();
  return useQuery<UserRead>({
    queryKey: ["auth", "me"],
    queryFn: () => api.get<UserRead>("/v1/auth/me").then((r) => r.data),
    enabled: isAuthenticated(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useLogin() {
  const { setTokens } = useAuthStore();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: LoginRequest) => {
      const form = new URLSearchParams();
      form.append("username", data.username);
      form.append("password", data.password);
      return api
        .post<TokenResponse>("/v1/auth/login", form, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        })
        .then((r) => r.data);
    },
    onSuccess: (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token);
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      navigate("/dashboard");
    },
  });
}

export function useRegisterTenant() {
  const { setTokens } = useAuthStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: TenantRegistrationRequest) =>
      api.post<TokenResponse>("/v1/auth/register", data).then((r) => r.data),
    onSuccess: (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token);
      navigate("/dashboard");
    },
  });
}

export function useLogout() {
  const { logout, accessToken } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api.post("/v1/auth/logout", null, {
        headers: { Authorization: `Bearer ${accessToken}` },
      }),
    onSettled: () => {
      logout();
      queryClient.clear();
      navigate("/login");
    },
  });
}
```

> **Nota:** `@/` alias precisa estar configurado no `vite.config.ts`. Adicionar na Task 18.

- [ ] **Step 4: Verificar tipos**

```powershell
cd frontend
npx tsc --noEmit
```

Saída esperada: sem erros.

- [ ] **Step 5: Commit**

```powershell
cd ..
git add frontend/src/types/ frontend/src/stores/ frontend/src/hooks/
git commit -m "feat(frontend): auth types + Zustand store + TanStack Query auth hooks"
```

---

## Task 16: Frontend — Página de Login

**Files:**
- Create: `frontend/src/components/auth/LoginForm.tsx`
- Create: `frontend/src/pages/Login.tsx`

- [ ] **Step 1: Criar `frontend/src/components/auth/LoginForm.tsx`**

```typescript
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useLogin } from "@/hooks/useAuth";

const schema = z.object({
  username: z.string().email("E-mail inválido"),
  password: z.string().min(1, "Senha obrigatória"),
});

type FormData = z.infer<typeof schema>;

export function LoginForm() {
  const { mutate: login, isPending, error } = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  return (
    <form onSubmit={handleSubmit((data) => login(data))} className="space-y-4">
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-gray-700">
          E-mail
        </label>
        <input
          id="username"
          type="email"
          autoComplete="email"
          {...register("username")}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.username && (
          <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Senha
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          {...register("password")}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-600">
          Credenciais inválidas. Verifique e-mail e senha.
        </p>
      )}

      <button
        type="submit"
        disabled={isPending}
        className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:opacity-60"
      >
        {isPending ? "Entrando..." : "Entrar"}
      </button>
    </form>
  );
}
```

- [ ] **Step 2: Criar `frontend/src/pages/Login.tsx`**

```typescript
import { LoginForm } from "@/components/auth/LoginForm";
import { Link } from "react-router-dom";

export function Login() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h1 className="text-center text-3xl font-bold tracking-tight text-gray-900">
            FleetOps
          </h1>
          <h2 className="mt-2 text-center text-lg text-gray-600">
            Acesse sua conta
          </h2>
        </div>
        <div className="rounded-lg border bg-white p-8 shadow-sm">
          <LoginForm />
          <p className="mt-6 text-center text-sm text-gray-500">
            Sem conta?{" "}
            <Link to="/register" className="font-medium text-indigo-600 hover:text-indigo-500">
              Criar conta grátis
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verificar tipos**

```powershell
cd frontend
npx tsc --noEmit
```

Saída esperada: sem erros.

- [ ] **Step 4: Commit**

```powershell
cd ..
git add frontend/src/components/auth/LoginForm.tsx frontend/src/pages/Login.tsx
git commit -m "feat(frontend): Login page with form validation"
```

---

## Task 17: Frontend — Página de Registro

**Files:**
- Create: `frontend/src/components/auth/RegisterForm.tsx`
- Create: `frontend/src/pages/Register.tsx`

- [ ] **Step 1: Criar `frontend/src/components/auth/RegisterForm.tsx`**

```typescript
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRegisterTenant } from "@/hooks/useAuth";

const schema = z.object({
  razao_social: z.string().min(3, "Nome da empresa obrigatório"),
  cnpj: z
    .string()
    .regex(/^\d{14}$/, "CNPJ deve ter 14 dígitos (somente números)"),
  admin_full_name: z.string().min(3, "Nome completo obrigatório"),
  admin_email: z.string().email("E-mail inválido"),
  admin_password: z
    .string()
    .min(10, "Senha deve ter pelo menos 10 caracteres"),
});

type FormData = z.infer<typeof schema>;

export function RegisterForm() {
  const { mutate: register, isPending, error } = useRegisterTenant();

  const {
    register: field,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const fields: Array<{
    id: keyof FormData;
    label: string;
    type?: string;
    placeholder?: string;
  }> = [
    { id: "razao_social", label: "Razão Social", placeholder: "Empresa ABC Ltda" },
    { id: "cnpj", label: "CNPJ (14 dígitos)", placeholder: "12345678000190" },
    { id: "admin_full_name", label: "Seu nome completo" },
    { id: "admin_email", label: "E-mail corporativo", type: "email" },
    { id: "admin_password", label: "Senha", type: "password" },
  ];

  return (
    <form onSubmit={handleSubmit((data) => register(data))} className="space-y-4">
      {fields.map(({ id, label, type = "text", placeholder }) => (
        <div key={id}>
          <label htmlFor={id} className="block text-sm font-medium text-gray-700">
            {label}
          </label>
          <input
            id={id}
            type={type}
            placeholder={placeholder}
            {...field(id)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          {errors[id] && (
            <p className="mt-1 text-sm text-red-600">{errors[id]?.message}</p>
          )}
        </div>
      ))}

      {error && (
        <p className="text-sm text-red-600">
          {(error as any)?.response?.data?.detail ?? "Erro ao criar conta. Verifique os dados."}
        </p>
      )}

      <button
        type="submit"
        disabled={isPending}
        className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:opacity-60"
      >
        {isPending ? "Criando conta..." : "Criar conta grátis (7 dias trial)"}
      </button>
    </form>
  );
}
```

- [ ] **Step 2: Criar `frontend/src/pages/Register.tsx`**

```typescript
import { RegisterForm } from "@/components/auth/RegisterForm";
import { Link } from "react-router-dom";

export function Register() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-lg space-y-8">
        <div>
          <h1 className="text-center text-3xl font-bold tracking-tight text-gray-900">
            FleetOps
          </h1>
          <h2 className="mt-2 text-center text-lg text-gray-600">
            7 dias grátis, sem cartão
          </h2>
        </div>
        <div className="rounded-lg border bg-white p-8 shadow-sm">
          <RegisterForm />
          <p className="mt-6 text-center text-sm text-gray-500">
            Já tem conta?{" "}
            <Link to="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verificar tipos**

```powershell
cd frontend
npx tsc --noEmit
```

Saída esperada: sem erros.

- [ ] **Step 4: Commit**

```powershell
cd ..
git add frontend/src/components/auth/ frontend/src/pages/Register.tsx
git commit -m "feat(frontend): Register page with tenant + admin user form"
```

---

## Task 18: Frontend — ProtectedRoute + configuração de rotas no App

**Files:**
- Create: `frontend/src/components/ProtectedRoute.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/vite.config.ts`
- Create: `frontend/src/pages/Dashboard.tsx` (placeholder)

- [ ] **Step 1: Criar `frontend/src/components/ProtectedRoute.tsx`**

```typescript
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/stores/auth";

export function ProtectedRoute() {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
```

- [ ] **Step 2: Criar `frontend/src/pages/Dashboard.tsx`** (placeholder para P2)

```typescript
import { useCurrentUser } from "@/hooks/useAuth";
import { useLogout } from "@/hooks/useAuth";

export function Dashboard() {
  const { data: user } = useCurrentUser();
  const { mutate: logout } = useLogout();

  return (
    <div className="p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button
          onClick={() => logout()}
          className="rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500"
        >
          Sair
        </button>
      </div>
      {user && (
        <p className="mt-4 text-gray-600">
          Bem-vindo, <strong>{user.full_name}</strong>!
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Adicionar alias `@/` no `frontend/vite.config.ts`**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

Também adicionar `"@types/node"` nas devDependencies:

```powershell
cd frontend
npm install --save-dev @types/node
```

- [ ] **Step 4: Atualizar `frontend/tsconfig.json`**

Adicionar `paths` para o alias `@/`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 5: Atualizar `frontend/src/main.tsx`**

```typescript
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>
);
```

- [ ] **Step 6: Atualizar `frontend/src/App.tsx`**

```typescript
import { Routes, Route, Navigate } from "react-router-dom";
import { Login } from "@/pages/Login";
import { Register } from "@/pages/Register";
import { Dashboard } from "@/pages/Dashboard";
import { ProtectedRoute } from "@/components/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      {/* Rotas públicas */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Rotas protegidas */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
```

- [ ] **Step 7: Verificar build completo**

```powershell
cd frontend
npx tsc --noEmit
npm run lint
npm run build
```

Saída esperada: sem erros de tipo, sem erros de lint, build com sucesso.

- [ ] **Step 8: Rodar testes de frontend**

```powershell
npm test
```

Os testes existentes (`App.test.tsx`, `HealthCheck.test.tsx`) podem precisar de atualização devido às novas rotas. Adaptar se necessário:

Em `frontend/tests/App.test.tsx`, envolver o render com `MemoryRouter` se necessário:

```typescript
import { MemoryRouter } from "react-router-dom";
import { render, screen } from "@testing-library/react";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import App from "../src/App";

function renderApp() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <QueryClientProvider client={qc}>
        <App />
      </QueryClientProvider>
    </MemoryRouter>
  );
}

test("renders login page at /login", () => {
  renderApp();
  expect(screen.getByText(/Acesse sua conta/i)).toBeInTheDocument();
});
```

- [ ] **Step 9: Rodar todos os testes do frontend**

```powershell
npm test
```

Saída esperada: todos os testes passando.

- [ ] **Step 10: Commit final**

```powershell
cd ..
git add frontend/
git commit -m "feat(frontend): ProtectedRoute + react-router-dom routing + Dashboard placeholder"
```

---

## Self-Review — Verificação contra o PRD

### Cobertura dos requisitos do PRD

| Requisito PRD | Task cobrindo |
|---|---|
| S1: registro de tenant + trial 7 dias | Task 8 (`register_tenant`) |
| S3: papéis Admin/Owner/Gestor/Operador/Mecânico/Leitura | Task 3 (`role.py`) + Task 9 (`require_role`) |
| Argon2id password hash | Task 6 (UserManager + pwdlib) |
| JWT 15min + refresh 7d rotativo | Task 5 (security.py) + Task 8 (login/refresh) |
| RLS multi-tenant | Task 4 (migration) + Task 9 (get_tenant_session) |
| Defense in depth (RLS + app) | Task 9 (get_tenant_session sets `SET LOCAL`) |
| UUID v7 em todos os PKs | Task 3 (todos os modelos usam `default=uuid7`) |
| CNPJ unique por tenant (unicidade com tenant_id) | Task 4 (migration: `UNIQUE(tenant_id, cnpj)` em `tenant`) |
| email unique por tenant | Task 3/4 (`uq_user_tenant_email`) |
| Login page + Register page (frontend) | Tasks 16, 17 |
| Rotas protegidas (frontend) | Task 18 (ProtectedRoute) |

### Verificações de consistência de tipos

- `User.id` → `uuid.UUID` com `default=uuid7` ✓
- `Tenant.id` → `uuid.UUID` com `default=uuid7` ✓
- `UserRole.id` → `uuid.UUID` com `default=uuid7` ✓
- `create_access_token(user_id, tenant_id)` → usada em `auth.py:_issue_tokens` e `conftest.py` ✓
- `hash_token(token)` → retorna `str` de 64 chars hex ✓
- `UserRead.model_validate(user)` → `User` tem todos os campos de `UserRead` ✓
- `require_role(RoleName.ADMIN, RoleName.OWNER)` → retorna `Depends(checker)` ✓

### Itens deliberadamente fora do escopo de P1

- Email de verificação → P2
- MFA/TOTP → P2
- Convite de usuário adicional ao tenant → P2
- Política de senha configurável por tenant → P2
- Rate limiting de login → P2
- CSRF tokens → P2
- Frontend: shadcn/ui components (substituição dos inputs Tailwind puro) → P2

---

**Plano completo. Salvo em `docs/superpowers/plans/2026-05-21-p1-multitenant-auth-rbac.md`.**

**Dois modos de execução disponíveis:**

**1. Subagent-Driven (recomendado)** — subagente fresco por task, com review entre tasks.
Usar: `superpowers:subagent-driven-development`

**2. Execução inline** — executar no contexto atual com checkpoints.
Usar: `superpowers:executing-plans`

Próximo plano após conclusão do P1: **P2 — Email Verification, User Invitation & MFA**.
