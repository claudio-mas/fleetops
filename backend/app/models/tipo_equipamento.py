from decimal import Decimal

from sqlalchemy import Index, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class TipoEquipamento(OperationalBase):
    __tablename__ = "tipo_equipamento"
    __table_args__ = (
        Index(
            "uq_tipo_equipamento_tenant_nome",
            "tenant_id",
            "nome",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    depreciacao_anual: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
