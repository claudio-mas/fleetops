import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ColaboradorCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    cargo_id: uuid.UUID | None = None
    telefone: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None


class ColaboradorUpdate(ColaboradorCreate):
    version: int = Field(ge=1)


class ColaboradorRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    cargo_id: uuid.UUID | None
    telefone: str | None
    email: str | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
