from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.role import RoleName, UserRole
from app.models.user import User

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
        raise credentials_exc from None

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
