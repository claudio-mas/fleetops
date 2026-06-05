from sqlalchemy import Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class UnidadeMedida(OperationalBase):
    __tablename__ = "unidade_medida"
    __table_args__ = (
        Index(
            "uq_unidade_medida_tenant_codigo",
            "tenant_id",
            "codigo",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    codigo: Mapped[str] = mapped_column(String(5), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
