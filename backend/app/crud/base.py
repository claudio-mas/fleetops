from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.models.base import OperationalBase


class VersionConflictError(Exception):
    """Raised when optimistic-lock version does not match the stored row."""


class CRUDBase[ModelT: OperationalBase]:
    def __init__(self, model: type[ModelT], *, search_fields: list[str]) -> None:
        self.model = model
        self.search_fields = search_fields

    async def list(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        limit: int,
        offset: int,
        search: str | None = None,
    ) -> tuple[list[ModelT], int]:
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None),
        )
        if search and self.search_fields:
            conds = [getattr(self.model, f).ilike(f"%{search}%") for f in self.search_fields]
            stmt = stmt.where(or_(*conds))
        total = (
            await session.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()
        stmt = stmt.order_by(self.model.created_at.desc()).limit(limit).offset(offset)
        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    async def get(
        self, session: AsyncSession, *, tenant_id: uuid.UUID, obj_id: uuid.UUID
    ) -> ModelT | None:
        obj = await session.get(self.model, obj_id)
        if obj is None or obj.tenant_id != tenant_id or obj.deleted_at is not None:
            return None
        return obj

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        data: dict[str, Any],
    ) -> ModelT:
        obj = self.model(
            id=uuid7(),
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            **data,
        )
        session.add(obj)
        await session.flush()
        return obj

    async def update(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        obj_id: uuid.UUID,
        user_id: uuid.UUID,
        data: dict[str, Any],
        expected_version: int,
    ) -> ModelT | None:
        obj = await self.get(session, tenant_id=tenant_id, obj_id=obj_id)
        if obj is None:
            return None
        if obj.version != expected_version:
            raise VersionConflictError
        for key, value in data.items():
            setattr(obj, key, value)
        obj.updated_by = user_id
        obj.version = obj.version + 1
        await session.flush()
        return obj

    async def soft_delete(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        obj_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        obj = await self.get(session, tenant_id=tenant_id, obj_id=obj_id)
        if obj is None:
            return False
        obj.deleted_at = datetime.now(UTC)
        obj.updated_by = user_id
        await session.flush()
        return True
