"""centro_custo: add codigo + status

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-05
"""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("centro_custo", sa.Column("codigo", sa.String(50), nullable=True))
    op.add_column(
        "centro_custo",
        sa.Column(
            "status",
            sa.String(20),
            server_default=sa.text("'ativo'"),
            nullable=False,
        ),
    )
    op.create_index(
        "uq_centro_custo_tenant_codigo",
        "centro_custo",
        ["tenant_id", "codigo"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND codigo IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_centro_custo_tenant_codigo", table_name="centro_custo")
    op.drop_column("centro_custo", "status")
    op.drop_column("centro_custo", "codigo")
