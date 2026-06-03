from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, TenantSession, get_current_tenant_id, require_role
from app.crud.base import CRUDBase, VersionConflictError
from app.models.role import RoleName
from app.schemas.common import PaginatedResponse

WRITE_ROLES = (RoleName.OWNER, RoleName.ADMIN, RoleName.GESTOR)

RefValidator = Callable[[TenantSession, uuid.UUID, dict[str, Any]], Awaitable[None]]


def build_crud_router(
    *,
    prefix: str,
    tag: str,
    crud: CRUDBase[Any],
    create_schema: type[BaseModel],
    update_schema: type[BaseModel],
    read_schema: type[BaseModel],
    validate_refs: RefValidator | None = None,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("", response_model=PaginatedResponse[read_schema])  # type: ignore[valid-type]
    async def list_items(
        session: TenantSession,
        tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
        limit: Annotated[int, Query(ge=1, le=200)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
        search: Annotated[str | None, Query(max_length=255)] = None,
    ) -> Any:
        items, total = await crud.list(
            session, tenant_id=tenant_id, limit=limit, offset=offset, search=search
        )
        return PaginatedResponse[read_schema](  # type: ignore[valid-type]
            items=[read_schema.model_validate(i, from_attributes=True) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    @router.get("/{obj_id}", response_model=read_schema)
    async def get_item(
        obj_id: uuid.UUID,
        session: TenantSession,
        tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    ) -> Any:
        obj = await crud.get(session, tenant_id=tenant_id, obj_id=obj_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado")
        return obj

    @router.post(
        "",
        response_model=read_schema,
        status_code=status.HTTP_201_CREATED,
        dependencies=[require_role(*WRITE_ROLES)],
    )
    async def create_item(
        payload: create_schema,  # type: ignore[valid-type]
        session: TenantSession,
        user: CurrentUser,
        tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    ) -> Any:
        data = payload.model_dump()  # type: ignore[attr-defined]
        if validate_refs is not None:
            await validate_refs(session, tenant_id, data)
        obj = await crud.create(session, tenant_id=tenant_id, user_id=user.id, data=data)
        await session.commit()
        await session.refresh(obj)
        return obj

    @router.put(
        "/{obj_id}",
        response_model=read_schema,
        dependencies=[require_role(*WRITE_ROLES)],
    )
    async def update_item(
        obj_id: uuid.UUID,
        payload: update_schema,  # type: ignore[valid-type]
        session: TenantSession,
        user: CurrentUser,
        tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    ) -> Any:
        data = payload.model_dump()  # type: ignore[attr-defined]
        expected_version = data.pop("version")
        if validate_refs is not None:
            await validate_refs(session, tenant_id, data)
        try:
            obj = await crud.update(
                session,
                tenant_id=tenant_id,
                obj_id=obj_id,
                user_id=user.id,
                data=data,
                expected_version=expected_version,
            )
        except VersionConflictError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Registro foi modificado por outro usuário (conflito de versão)",
            ) from None
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado")
        await session.commit()
        await session.refresh(obj)
        return obj

    @router.delete(
        "/{obj_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[require_role(*WRITE_ROLES)],
    )
    async def delete_item(
        obj_id: uuid.UUID,
        session: TenantSession,
        user: CurrentUser,
        tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    ) -> None:
        ok = await crud.soft_delete(session, tenant_id=tenant_id, obj_id=obj_id, user_id=user.id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado")
        await session.commit()

    return router
