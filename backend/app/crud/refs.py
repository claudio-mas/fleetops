from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import OperationalBase


async def _exists(
    session: AsyncSession, model: type[OperationalBase], tenant_id: uuid.UUID, obj_id: uuid.UUID
) -> bool:
    stmt = select(model.id).where(
        model.id == obj_id,
        model.tenant_id == tenant_id,
        model.deleted_at.is_(None),
    )
    return (await session.execute(stmt)).first() is not None


def fk_validator(
    field: str, model: type[OperationalBase], label: str
) -> Callable[[AsyncSession, uuid.UUID, dict[str, Any]], Awaitable[None]]:
    async def _validate(session: AsyncSession, tenant_id: uuid.UUID, data: dict[str, Any]) -> None:
        value = data.get(field)
        if value is None:
            return
        if not await _exists(session, model, tenant_id, value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{label} não encontrado(a) neste tenant",
            )

    return _validate


def compose(
    *validators: Callable[[AsyncSession, uuid.UUID, dict[str, Any]], Awaitable[None]],
) -> Callable[[AsyncSession, uuid.UUID, dict[str, Any]], Awaitable[None]]:
    async def _run(session: AsyncSession, tenant_id: uuid.UUID, data: dict[str, Any]) -> None:
        for v in validators:
            await v(session, tenant_id, data)

    return _run
