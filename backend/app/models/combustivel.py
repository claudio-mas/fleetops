from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class Combustivel(OperationalBase):
    __tablename__ = "combustivel"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
