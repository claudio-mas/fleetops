"""p2: mfa anti-replay (last used TOTP timestep)

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-31
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("mfa_last_used_timestep", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user", "mfa_last_used_timestep")
