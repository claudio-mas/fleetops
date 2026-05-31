import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock, patch

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


@pytest.fixture(scope="session", autouse=True)
def mock_celery_tasks() -> Any:
    """Mock Celery task dispatch to prevent connecting to the broker.

    Patch ``.delay`` on the shared Task objects (not the module name): every
    ``from app.tasks.email import X`` references the same object, so this holds
    even when a module captured the task before this fixture ran.
    """
    from app.tasks.email import send_email_verification, send_user_invitation

    with (
        patch.object(send_email_verification, "delay", MagicMock(return_value=None)),
        patch.object(send_user_invitation, "delay", MagicMock(return_value=None)),
    ):
        yield


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
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
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


@pytest.fixture(scope="function")
async def tenant(db: AsyncSession) -> Tenant:
    from datetime import UTC, datetime, timedelta

    t = Tenant(
        slug=f"tenant-{uuid7().hex[:16]}",
        razao_social="Empresa Teste Ltda",
        cnpj=f"{uuid7().int % 10**14:014d}",
        status=TenantStatus.TRIAL,
        trial_expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


@pytest.fixture(scope="function")
async def sample_user(db: AsyncSession, tenant: Tenant):  # type: ignore[no-untyped-def]
    import fastapi_users.schemas as fau_schemas

    class _UC(fau_schemas.BaseUserCreate):
        tenant_id: uuid.UUID
        full_name: str

    async for user_db_inst in get_user_db(db):
        async for mgr in get_user_manager(user_db_inst):
            u = await mgr.create(
                _UC(
                    email=f"user-{uuid7().hex[:16]}@test.com",
                    password="SenhaForte123!",
                    tenant_id=tenant.id,
                    full_name="Sample User",
                )
            )

    role = UserRole(tenant_id=tenant.id, user_id=u.id, role=RoleName.ADMIN)
    db.add(role)
    await db.commit()
    await db.refresh(u)

    return u


@pytest.fixture(scope="function")
async def dummy_role(db: AsyncSession):  # type: ignore[no-untyped-def]
    """Create a dummy role record for user invitation FK constraint."""
    from sqlalchemy.sql import text

    role_id = uuid.uuid4()
    await db.execute(
        text("INSERT INTO role (id) VALUES (:id) ON CONFLICT (id) DO NOTHING"),
        {"id": str(role_id)},
    )
    await db.commit()
    return role_id


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
