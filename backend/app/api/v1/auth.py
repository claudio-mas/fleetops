from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

import fastapi_users.schemas as fau_schemas
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, require_role
from app.core.config import settings
from app.core.database import get_session
from app.core.security import (
    create_mfa_challenge_token,
    hash_token,
    issue_login_tokens,
)
from app.models.role import RoleName, UserRole
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.schemas.auth import (
    LoginResponse,
    RefreshRequest,
    TenantRegistrationRequest,
    TokenResponse,
    UserRead,
)
from app.services.token_service import TokenService
from app.services.user_manager import get_user_db, get_user_manager
from app.tasks.email import send_email_verification

router = APIRouter(prefix="/auth", tags=["auth"])

# Pre-computed dummy Argon2id hash — used in login to equalize timing when user doesn't exist,
# preventing user-enumeration via response-time differences.
_DUMMY_HASH: str = PasswordHash((Argon2Hasher(),)).hash("_timing_equalizer_")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:80]


def _issue_tokens(user: User) -> tuple[str, str, datetime]:
    return issue_login_tokens(user.id, user.tenant_id)


class _UserCreate(fau_schemas.BaseUserCreate):
    tenant_id: uuid.UUID
    full_name: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_tenant(
    data: TenantRegistrationRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    existing = await session.execute(select(Tenant).where(Tenant.cnpj == data.cnpj))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CNPJ já cadastrado")

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
    await session.flush()

    user: User | None = None
    async for user_db in get_user_db(session):
        async for user_manager in get_user_manager(user_db):
            user_create = _UserCreate(
                email=data.admin_email,
                password=data.admin_password,
                tenant_id=tenant.id,
                full_name=data.admin_full_name,
            )
            user = await user_manager.create(user_create)

    if user is None:
        raise HTTPException(status_code=500, detail="Falha ao criar usuário")

    owner_role = UserRole(tenant_id=tenant.id, user_id=user.id, role=RoleName.OWNER)
    session.add(owner_role)

    access_token, refresh_raw, expires_at = _issue_tokens(user)
    user.refresh_token_hash = hash_token(refresh_raw)
    user.refresh_token_expires_at = expires_at

    await session.commit()

    verification_token = await TokenService.create_email_verification_token(
        session, user.id, tenant.id, user.email
    )

    verify_url_base = f"{settings.FRONTEND_URL}/verify-email"
    send_email_verification.delay(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        email=user.email,
        token=verification_token,
        verify_url_base=verify_url_base,
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_raw)


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LoginResponse:
    result = await session.execute(select(User).where(User.email == form_data.username))  # type: ignore[arg-type]
    user = result.scalar_one_or_none()

    async for user_db in get_user_db(session):
        async for user_manager in get_user_manager(user_db):
            # Always run verify to equalize timing (prevents user-enumeration oracle)
            hash_to_check = user.hashed_password if user is not None else _DUMMY_HASH
            password_ok, _ = user_manager.password_helper.verify_and_update(
                form_data.password, hash_to_check
            )
            if not password_ok or user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciais inválidas",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo")

    if user.mfa_enabled:
        challenge = create_mfa_challenge_token(user.id, user.tenant_id)
        return LoginResponse(mfa_required=True, mfa_challenge_token=challenge)

    access_token, refresh_raw, expires_at = _issue_tokens(user)
    user.refresh_token_hash = hash_token(refresh_raw)
    user.refresh_token_expires_at = expires_at
    await session.commit()

    return LoginResponse(access_token=access_token, refresh_token=refresh_raw)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    token_hash = hash_token(data.refresh_token)
    result = await session.execute(select(User).where(User.refresh_token_hash == token_hash))
    user = result.scalar_one_or_none()

    if user is None or user.refresh_token_expires_at is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido"
        )

    if datetime.now(UTC) > user.refresh_token_expires_at.replace(tzinfo=UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expirado"
        )

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


@router.get("/admin-only", dependencies=[require_role(RoleName.ADMIN, RoleName.OWNER)])
async def admin_only_route(user: CurrentUser) -> dict[str, str]:
    return {"message": f"Acesso concedido para {user.email}"}
