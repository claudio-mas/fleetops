import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    TenantRegistrationRequest,
    TokenResponse,
)


def test_tenant_registration_requires_cnpj_14_digits() -> None:
    with pytest.raises(ValidationError):
        TenantRegistrationRequest(
            razao_social="Empresa X",
            cnpj="123",
            admin_email="a@b.com",
            admin_password="senha12345678",
            admin_full_name="Admin",
        )


def test_tenant_registration_valid() -> None:
    req = TenantRegistrationRequest(
        razao_social="Empresa X Ltda",
        cnpj="12345678000190",
        admin_email="admin@empresa.com",
        admin_password="SenhaForte123!",
        admin_full_name="João Admin",
    )
    assert req.cnpj == "12345678000190"


def test_token_response_has_required_fields() -> None:
    tr = TokenResponse(
        access_token="tok",
        refresh_token="ref",
        token_type="bearer",
    )
    assert tr.token_type == "bearer"
