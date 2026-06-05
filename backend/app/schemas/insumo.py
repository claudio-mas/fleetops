import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class InsumoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    grupo_insumo_id: uuid.UUID | None = None
    unidade_medida_id: uuid.UUID | None = None
    preco_medio: Decimal | None = Field(default=None, ge=0)
    marca: str | None = Field(default=None, max_length=255)
    fabricante: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None


class InsumoUpdate(InsumoCreate):
    version: int = Field(ge=1)


class InsumoRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    grupo_insumo_id: uuid.UUID | None
    unidade_medida_id: uuid.UUID | None
    preco_medio: Decimal | None
    marca: str | None
    fabricante: str | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
