import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class Insumo(OperationalBase):
    __tablename__ = "insumo"
    __table_args__ = (
        Index(
            "uq_insumo_tenant_nome",
            "tenant_id",
            "nome",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    grupo_insumo_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("grupo_insumo.id", ondelete="SET NULL"), nullable=True
    )
    unidade_medida_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("unidade_medida.id", ondelete="SET NULL"), nullable=True
    )
    preco_medio: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    marca: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fabricante: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
