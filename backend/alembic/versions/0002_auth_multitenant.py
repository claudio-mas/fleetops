"""auth: tenant + user + user_role + RLS

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-21
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── tenant ──────────────────────────────────────────────────────────────
    op.create_table(
        "tenant",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("razao_social", sa.String(255), nullable=False),
        sa.Column("cnpj", sa.String(14), nullable=False),
        sa.Column(
            "status",
            sa.Enum("trial", "pending_payment", "active", "delinquent",
                    "suspended", "cancelled", "expired",
                    name="tenant_status", create_type=True),
            nullable=False,
            server_default="trial",
        ),
        sa.Column("trial_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("slug", name="uq_tenant_slug"),
        sa.UniqueConstraint("cnpj", name="uq_tenant_cnpj"),
    )
    op.create_index("ix_tenant_slug", "tenant", ["slug"])

    # ── user ─────────────────────────────────────────────────────────────────
    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), nullable=True),
        sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
    )
    op.create_index("ix_user_tenant_id", "user", ["tenant_id"])

    # ── user_role (com RLS) ──────────────────────────────────────────────────
    op.create_table(
        "user_role",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("owner", "admin", "gestor", "operador", "mecanico", "leitura",
                    name="role_name", create_type=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("tenant_id", "user_id", "role", name="uq_user_role_tenant"),
    )
    op.create_index("ix_user_role_tenant_id", "user_role", ["tenant_id"])
    op.create_index("ix_user_role_user_id", "user_role", ["user_id"])

    # ── RLS no user_role ─────────────────────────────────────────────────────
    op.execute("ALTER TABLE user_role ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_role FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON user_role
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant', TRUE), '')::uuid
            )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON user_role")
    op.execute("ALTER TABLE user_role DISABLE ROW LEVEL SECURITY")
    op.drop_table("user_role")
    op.execute("DROP TYPE IF EXISTS role_name")
    op.drop_table("user")
    op.drop_table("tenant")
    op.execute("DROP TYPE IF EXISTS tenant_status")
