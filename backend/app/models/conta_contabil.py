from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class ContaContabil(OperationalBase):
    __tablename__ = "conta_contabil"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    grupo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
