import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.models.base import Base, TimestampMixin


class TenantStatus(StrEnum):
    TRIAL = "trial"
    PENDING_PAYMENT = "pending_payment"
    ACTIVE = "active"
    DELINQUENT = "delinquent"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenant"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid7)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    razao_social: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    status: Mapped[TenantStatus] = mapped_column(
        Enum(
            TenantStatus, name="tenant_status", values_callable=lambda objs: [e.value for e in objs]
        ),
        default=TenantStatus.TRIAL,
        nullable=False,
    )
    trial_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
