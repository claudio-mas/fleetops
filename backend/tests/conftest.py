import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://fleetops:fleetops_dev_password@localhost:5433/fleetops_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-chars-long")
os.environ.setdefault("ENVIRONMENT", "test")

from uuid6 import uuid7  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.models.role import RoleName, UserRole  # noqa: E402
from app.models.tenant import Tenant, TenantStatus  # noqa: E402
from app.services.user_manager import get_user_db, get_user_manager  # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def db_engine():  # type: ignore[no-untyped-def]
    eng = create_async_engine(settings.database_url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:  # type: ignore[no-untyped-def]
    factory = async_sessionmaker(db_engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:  # type: ignore[no-untyped-def]
    from app.core.database import get_session
    from app.main import app

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
async def user_with_token(  # type: ignore[no-untyped-def]
    db: AsyncSession, tenant: Tenant
) -> dict[str, Any]:
    import fastapi_users.schemas as fau_schemas

    class _UC(fau_schemas.BaseUserCreate):
        tenant_id: uuid.UUID
        full_name: str

    async for user_db_inst in get_user_db(db):
        async for mgr in get_user_manager(user_db_inst):
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
