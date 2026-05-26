"""p2: email verification, invitations, MFA

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-26
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Add columns to user table ────────────────────────────────────────────
    op.add_column("user", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user", sa.Column("mfa_secret", sa.String(32), nullable=True))
    op.add_column("user", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"))

    # ── email_verification_token ─────────────────────────────────────────────
    op.create_table(
        "email_verification_token",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("token_hash", name="uq_email_verification_token_hash"),
    )
    op.create_index("ix_email_verification_token_tenant_id", "email_verification_token", ["tenant_id"])
    op.create_index("ix_email_verification_token_user_id", "email_verification_token", ["user_id"])

    # ── RLS on email_verification_token ──────────────────────────────────────
    op.execute("ALTER TABLE email_verification_token ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE email_verification_token FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON email_verification_token
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant', TRUE), '')::uuid
            )
        """
    )

    # ── user_invitation (with invitation_status enum) ────────────────────────
    op.execute(
        """
        CREATE TYPE invitation_status AS ENUM ('pending', 'accepted', 'rejected', 'expired')
        """
    )
    op.create_table(
        "user_invitation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "invited_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "accepted", "rejected", "expired",
                    name="invitation_status", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "invited_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "accepted_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("role.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.UniqueConstraint("token_hash", name="uq_user_invitation_token_hash"),
    )
    op.create_index("ix_user_invitation_tenant_id", "user_invitation", ["tenant_id"])
    op.create_index("ix_user_invitation_invited_by_id", "user_invitation", ["invited_by_id"])
    op.create_index("ix_user_invitation_role_id", "user_invitation", ["role_id"])

    # ── RLS on user_invitation ──────────────────────────────────────────────
    op.execute("ALTER TABLE user_invitation ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_invitation FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON user_invitation
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant', TRUE), '')::uuid
            )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON user_invitation")
    op.execute("ALTER TABLE user_invitation DISABLE ROW LEVEL SECURITY")
    op.drop_table("user_invitation")
    op.execute("DROP TYPE IF EXISTS invitation_status")

    op.execute("DROP POLICY IF EXISTS tenant_isolation ON email_verification_token")
    op.execute("ALTER TABLE email_verification_token DISABLE ROW LEVEL SECURITY")
    op.drop_table("email_verification_token")

    op.drop_column("user", "mfa_enabled")
    op.drop_column("user", "mfa_secret")
    op.drop_column("user", "email_verified_at")
