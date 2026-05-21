"""initial empty migration (verifies workflow)

Revision ID: 0001
Revises:
Create Date: 2026-05-15

"""
from collections.abc import Sequence

from alembic import op  # noqa: F401

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
