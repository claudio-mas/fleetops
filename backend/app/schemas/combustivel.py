import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CombustivelCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    observacoes: str | None = None


class CombustivelUpdate(CombustivelCreate):
    version: int = Field(ge=1)


class CombustivelRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
