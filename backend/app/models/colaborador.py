import uuid

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class Colaborador(OperationalBase):
    __tablename__ = "colaborador"
    __table_args__ = (
        Index(
            "uq_colaborador_tenant_nome",
            "tenant_id",
            "nome",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cargo_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cargo.id", ondelete="SET NULL"), nullable=True
    )
    telefone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
