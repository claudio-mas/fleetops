import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UnidadeMedidaCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=5)
    nome: str = Field(min_length=1, max_length=255)
    observacoes: str | None = None


class UnidadeMedidaUpdate(UnidadeMedidaCreate):
    version: int = Field(ge=1)


class UnidadeMedidaRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    nome: str
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
