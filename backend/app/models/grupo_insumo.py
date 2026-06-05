from sqlalchemy import Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class GrupoInsumo(OperationalBase):
    __tablename__ = "grupo_insumo"
    __table_args__ = (
        Index(
            "uq_grupo_insumo_tenant_nome",
            "tenant_id",
            "nome",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
