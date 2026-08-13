import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ClaimsAnalyticsExport(Base):
    __tablename__ = "claims_analytics_export"

    export_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), unique=True, nullable=False
    )

    claim_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    policy_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    document_type: Mapped[str] = mapped_column(String(50))

    incident_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    claimed_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)

    fraud_score: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    fraud_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    inconsistency_count: Mapped[int] = mapped_column(Integer, default=0)

    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    exported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
