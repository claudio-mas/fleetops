import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CentroCustoStatus = Literal["ativo", "inativo"]


class CentroCustoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    codigo: str | None = Field(default=None, max_length=50)
    status: CentroCustoStatus = "ativo"
    responsavel: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None


class CentroCustoUpdate(CentroCustoCreate):
    version: int = Field(ge=1)


class CentroCustoRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    codigo: str | None
    status: CentroCustoStatus
    responsavel: str | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
