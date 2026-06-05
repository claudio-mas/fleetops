from sqlalchemy import Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class Fornecedor(OperationalBase):
    __tablename__ = "fornecedor"
    __table_args__ = (
        Index(
            "uq_fornecedor_tenant_nome",
            "tenant_id",
            "nome",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cnpj_cpf: Mapped[str | None] = mapped_column(String(18), nullable=True)
    rg_ie: Mapped[str | None] = mapped_column(String(255), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bairro: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cep: Mapped[str | None] = mapped_column(String(9), nullable=True)
    cidade: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
