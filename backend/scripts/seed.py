import asyncio
import os
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import fastapi_users.schemas as fau_schemas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from uuid6 import uuid7

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from app.core.config import settings
from app.models.role import RoleName, UserRole
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.services.user_manager import get_user_db, get_user_manager


class _UserCreate(fau_schemas.BaseUserCreate):
    tenant_id: UUID
    full_name: str


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:80] or "fleetops-dev"


async def _ensure_tenant(session) -> Tenant:
    tenant_name = os.getenv("SEED_TENANT_RAZAO", "FleetOps Dev")
    tenant_cnpj = os.getenv("SEED_TENANT_CNPJ", "11222333000181")
    tenant_slug = os.getenv("SEED_TENANT_SLUG", _slugify(tenant_name))

    result = await session.execute(select(Tenant).where(Tenant.cnpj == tenant_cnpj))
    tenant = result.scalar_one_or_none()
    if tenant is not None:
        return tenant

    base_slug = tenant_slug
    slug = base_slug
    counter = 1
    while (await session.execute(select(Tenant).where(Tenant.slug == slug))).scalar_one_or_none():
        slug = f"{base_slug}-{counter}"
        counter += 1

    tenant = Tenant(
        slug=slug,
        razao_social=tenant_name,
        cnpj=tenant_cnpj,
        status=TenantStatus.TRIAL,
        trial_expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    session.add(tenant)
    await session.flush()
    return tenant


async def _ensure_user(session, tenant: Tenant) -> User:
    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@fleetops.dev")
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "SenhaForte123!")
    admin_full_name = os.getenv("SEED_ADMIN_FULL_NAME", "Admin Dev")

    result = await session.execute(select(User).where(User.email == admin_email))
    user = result.scalar_one_or_none()

    async for user_db in get_user_db(session):
        async for user_manager in get_user_manager(user_db):
            if user is None:
                user = await user_manager.create(
                    _UserCreate(
                        email=admin_email,
                        password=admin_password,
                        tenant_id=tenant.id,
                        full_name=admin_full_name,
                    )
                )
                user.email_verified_at = datetime.now(UTC)
            else:
                if user.tenant_id != tenant.id:
                    raise ValueError("Usuario ja existe em outro tenant")
                user.hashed_password = user_manager.password_helper.hash(admin_password)
                user.full_name = admin_full_name
                user.is_active = True
                if user.email_verified_at is None:
                    user.email_verified_at = datetime.now(UTC)
                # Resetar MFA para que o seed sempre permita login sem TOTP
                user.mfa_enabled = False
                user.mfa_secret = None
                user.mfa_last_used_timestep = None

    role_result = await session.execute(
        select(UserRole).where(
            UserRole.tenant_id == tenant.id,
            UserRole.user_id == user.id,
            UserRole.role == RoleName.OWNER,
        )
    )
    role = role_result.scalar_one_or_none()
    if role is None:
        session.add(UserRole(tenant_id=tenant.id, user_id=user.id, role=RoleName.OWNER))

    return user


async def main() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    async with session_factory() as session:
        tenant = await _ensure_tenant(session)
        user = await _ensure_user(session, tenant)
        await session.commit()

    await engine.dispose()

    print("Seed concluido")
    print(f"Tenant: {tenant.slug}")
    print(f"Email: {user.email}")
    print("Senha: (definida via SEED_ADMIN_PASSWORD)")


if __name__ == "__main__":
    asyncio.run(main())
