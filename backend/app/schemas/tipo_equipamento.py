import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TipoEquipamentoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    depreciacao_anual: Decimal | None = Field(default=None, ge=0)
    observacoes: str | None = None


class TipoEquipamentoUpdate(TipoEquipamentoCreate):
    version: int = Field(ge=1)


class TipoEquipamentoRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    depreciacao_anual: Decimal | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
