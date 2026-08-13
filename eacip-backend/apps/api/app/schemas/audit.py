import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    event_type: str
    resource: str | None
    result: str
    metadata: dict[str, Any]
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
