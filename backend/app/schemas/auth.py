import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


def _normalize_cnpj(cnpj: str) -> str:
    digits = re.sub(r"\D", "", cnpj)
    if len(digits) != 14:
        raise ValueError("CNPJ deve ter 14 dígitos")
    return digits


class TenantRegistrationRequest(BaseModel):
    razao_social: str
    cnpj: str
    admin_email: EmailStr
    admin_password: str
    admin_full_name: str

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        return _normalize_cnpj(v)

    @field_validator("admin_password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Senha deve ter pelo menos 10 caracteres")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_slug: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
