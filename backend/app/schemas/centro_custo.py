import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CentroCustoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    responsavel: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None


class CentroCustoUpdate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    responsavel: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None
    version: int = Field(ge=1)


class CentroCustoRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    responsavel: str | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
