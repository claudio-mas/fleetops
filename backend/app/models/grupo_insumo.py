from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class GrupoInsumo(OperationalBase):
    __tablename__ = "grupo_insumo"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
