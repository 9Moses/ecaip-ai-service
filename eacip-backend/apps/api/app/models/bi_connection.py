import uuid
from typing import Any
from datetime import datetime

from sqlalchemy import DateTime, LargeBinary, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class BIConnection(Base):
    __tablename__ = "bi_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    provider: Mapped[str] = mapped_column(String(20))  # "power_bi" | "tableau"
    credentials_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    # power_bi config example: {"tenant_id": "...",
    #                       "client_id": "...",
    #                       "workspace_id": "...",
    #                       "dataset_id": "..."}
    # tableau config example:  {"site_id": "...",
    #                        "server_url": "..."}

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
