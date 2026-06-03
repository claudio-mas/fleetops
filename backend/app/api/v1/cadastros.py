from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.crud_router import build_crud_router
from app.crud.base import CRUDBase
from app.models.centro_custo import CentroCusto
from app.schemas.centro_custo import CentroCustoCreate, CentroCustoRead, CentroCustoUpdate

_BASE = "/api/v1/cadastros"

routers: list[APIRouter] = [
    build_crud_router(
        prefix=f"{_BASE}/centro-custo",
        tag="cadastros:centro-custo",
        crud=CRUDBase(CentroCusto, search_fields=["nome", "responsavel"]),
        create_schema=CentroCustoCreate,
        update_schema=CentroCustoUpdate,
        read_schema=CentroCustoRead,
    ),
]
