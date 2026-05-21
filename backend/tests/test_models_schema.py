import uuid
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.models.role import RoleName, UserRole


def test_tenant_model_has_required_columns() -> None:
    cols = {c.name for c in Tenant.__table__.columns}
    assert {"id", "slug", "razao_social", "cnpj", "status", "trial_expires_at",
            "created_at", "updated_at"} <= cols


def test_user_model_has_tenant_id() -> None:
    cols = {c.name for c in User.__table__.columns}
    assert {"id", "tenant_id", "email", "hashed_password", "full_name",
            "refresh_token_hash", "refresh_token_expires_at",
            "is_active", "created_at", "updated_at"} <= cols


def test_user_role_model_has_rls_columns() -> None:
    cols = {c.name for c in UserRole.__table__.columns}
    assert {"id", "tenant_id", "user_id", "role", "created_at"} <= cols


def test_role_name_enum_has_all_roles() -> None:
    roles = {r.value for r in RoleName}
    assert {"owner", "admin", "gestor", "operador", "mecanico", "leitura"} == roles
