import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FornecedorCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    tipo: str | None = Field(default=None, max_length=50)
    cnpj_cpf: str | None = Field(default=None, max_length=18)
    rg_ie: str | None = Field(default=None, max_length=255)
    endereco: str | None = Field(default=None, max_length=255)
    bairro: str | None = Field(default=None, max_length=255)
    cep: str | None = Field(default=None, max_length=9)
    cidade: str | None = Field(default=None, max_length=255)
    uf: str | None = Field(default=None, max_length=2)
    telefone: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None


class FornecedorUpdate(FornecedorCreate):
    version: int = Field(ge=1)


class FornecedorRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    tipo: str | None
    cnpj_cpf: str | None
    rg_ie: str | None
    endereco: str | None
    bairro: str | None
    cep: str | None
    cidade: str | None
    uf: str | None
    telefone: str | None
    email: str | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
