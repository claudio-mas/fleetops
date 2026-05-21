from datetime import datetime

from sqlalchemy import DateTime, Integer, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class OperationalMixin(TimestampMixin):
    created_by: Mapped[int | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"), nullable=False)
