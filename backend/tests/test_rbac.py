import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import fastapi_users.schemas as fau_schemas
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.core.security import create_access_token
from app.models.role import RoleName, UserRole
from app.models.tenant import Tenant, TenantStatus
from app.services.user_manager import get_user_db, get_user_manager

pytestmark = pytest.mark.asyncio


class _UC(fau_schemas.BaseUserCreate):
    tenant_id: uuid.UUID
    full_name: str


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
    return resp.json()["access_token"]  # type: ignore[no-any-return]


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
    db: AsyncSession,
) -> None:
    tenant = Tenant(
        slug=f"rbac-test-{uuid7().hex[:8]}",
        razao_social="RBAC Test",
        cnpj=f"{uuid7().int % 10**14:014d}",
        status=TenantStatus.TRIAL,
        trial_expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(tenant)
    await db.flush()

    leitura_user: Any = None
    async for user_db_inst in get_user_db(db):
        async for mgr in get_user_manager(user_db_inst):
            leitura_user = await mgr.create(
                _UC(
                    email=f"leitura-{uuid7().hex[:8]}@rbac.com",
                    password="SenhaForte123!",
                    tenant_id=tenant.id,
                    full_name="Leitura User",
                )
            )

    role = UserRole(tenant_id=tenant.id, user_id=leitura_user.id, role=RoleName.LEITURA)
    db.add(role)
    await db.commit()

    token = create_access_token(leitura_user.id, tenant.id)
    resp = await client.get(
        "/api/v1/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
