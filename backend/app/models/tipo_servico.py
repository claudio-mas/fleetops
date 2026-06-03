from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class TipoServico(OperationalBase):
    __tablename__ = "tipo_servico"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
