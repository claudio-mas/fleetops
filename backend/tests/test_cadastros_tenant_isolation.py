import uuid

import pytest

from app.core.security import create_access_token
from app.models.role import RoleName, UserRole
from app.models.tenant import Tenant, TenantStatus

pytestmark = pytest.mark.asyncio


async def _make_tenant_user(db):  # type: ignore[no-untyped-def]
    import fastapi_users.schemas as fau_schemas

    from app.services.user_manager import get_user_db, get_user_manager

    # uuid4 (não uuid7): uuid7 é ordenado por tempo, então dois tenants criados no
    # mesmo milissegundo colidiriam no prefixo usado para slug/e-mail únicos.
    suffix = uuid.uuid4().hex
    t = Tenant(
        slug=f"t-{suffix[:12]}",
        razao_social="ACME",
        cnpj=f"{uuid.uuid4().int % 10**14:014d}",
        status=TenantStatus.TRIAL,
    )
    db.add(t)
    await db.commit()

    class _UC(fau_schemas.BaseUserCreate):
        tenant_id: uuid.UUID
        full_name: str

    async for udb in get_user_db(db):
        async for mgr in get_user_manager(udb):
            u = await mgr.create(
                _UC(
                    email=f"u-{suffix[:10]}@x.com",
                    password="SenhaForte123!",
                    tenant_id=t.id,
                    full_name="U",
                )
            )
    db.add(UserRole(tenant_id=t.id, user_id=u.id, role=RoleName.ADMIN))
    await db.commit()
    return t, create_access_token(u.id, t.id)


async def test_centro_custo_not_visible_across_tenants(client, db):
    _, token_a = await _make_tenant_user(db)
    _, token_b = await _make_tenant_user(db)

    r = await client.post(
        "/api/v1/cadastros/centro-custo",
        json={"nome": "Secreto A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 201

    r = await client.get(
        "/api/v1/cadastros/centro-custo", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert r.json()["total"] == 0
