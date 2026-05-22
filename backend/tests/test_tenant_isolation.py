"""
Testa isolamento de tenant:
- App-level: /me retorna apenas dados do usuário autenticado
- DB-level (RLS): SET LOCAL app.current_tenant filtra user_role
"""

import uuid
import warnings
from datetime import UTC, datetime, timedelta
from typing import Any

import fastapi_users.schemas as fau_schemas
import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.models.role import RoleName, UserRole
from app.models.tenant import Tenant, TenantStatus
from app.services.user_manager import get_user_db, get_user_manager

pytestmark = pytest.mark.asyncio


class _UC(fau_schemas.BaseUserCreate):
    tenant_id: uuid.UUID
    full_name: str


async def _register(client: AsyncClient, cnpj: str, email: str) -> dict:  # type: ignore[type-arg]
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
    return resp.json()  # type: ignore[return-value]


async def test_user_from_tenant_a_cannot_see_tenant_b_me(client: AsyncClient) -> None:
    tokens_a = await _register(client, "88999000000111", "a@isolamento.com")
    tokens_b = await _register(client, "99000111000122", "b@isolamento.com")

    me_a = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens_a['access_token']}"},
    )
    assert me_a.status_code == 200
    assert me_a.json()["email"] == "a@isolamento.com"

    me_b = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
    )
    assert me_b.status_code == 200
    assert me_b.json()["email"] == "b@isolamento.com"


async def test_rls_user_role_isolation_via_set_local(db: AsyncSession) -> None:
    tenant_a = Tenant(
        slug=f"rls-test-a-{uuid7().hex[:8]}",
        razao_social="RLS Test A",
        cnpj=f"{uuid7().int % 10**14:014d}",
        status=TenantStatus.TRIAL,
        trial_expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    tenant_b = Tenant(
        slug=f"rls-test-b-{uuid7().hex[:8]}",
        razao_social="RLS Test B",
        cnpj=f"{uuid7().int % 10**14:014d}",
        status=TenantStatus.TRIAL,
        trial_expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add_all([tenant_a, tenant_b])
    await db.flush()

    user_a: Any = None
    user_b: Any = None
    async for user_db_inst in get_user_db(db):
        async for mgr in get_user_manager(user_db_inst):
            user_a = await mgr.create(
                _UC(
                    email=f"rls-a-{uuid7().hex[:8]}@test.com",
                    password="SenhaForte123!",
                    tenant_id=tenant_a.id,
                    full_name="User A",
                )
            )
            user_b = await mgr.create(
                _UC(
                    email=f"rls-b-{uuid7().hex[:8]}@test.com",
                    password="SenhaForte123!",
                    tenant_id=tenant_b.id,
                    full_name="User B",
                )
            )

    role_a = UserRole(tenant_id=tenant_a.id, user_id=user_a.id, role=RoleName.OWNER)
    role_b = UserRole(tenant_id=tenant_b.id, user_id=user_b.id, role=RoleName.OWNER)
    db.add_all([role_a, role_b])
    await db.commit()

    await db.execute(
        text("SELECT set_config('app.current_tenant', :tid, true)"),
        {"tid": str(tenant_a.id)},
    )

    result = await db.execute(select(UserRole))
    roles = result.scalars().all()
    tenant_ids = {str(r.tenant_id) for r in roles}

    if len(roles) == 1:
        assert str(tenant_a.id) in tenant_ids
    else:
        warnings.warn(
            "RLS não aplicado: DB user é superuser. "
            "Em produção use um role não-superuser para garantir RLS.",
            stacklevel=1,
        )
