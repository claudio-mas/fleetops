from sqlalchemy import Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class Combustivel(OperationalBase):
    __tablename__ = "combustivel"
    __table_args__ = (
        Index(
            "uq_combustivel_tenant_nome",
            "tenant_id",
            "nome",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
