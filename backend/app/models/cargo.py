from decimal import Decimal

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class Cargo(OperationalBase):
    __tablename__ = "cargo"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    salario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
