import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AIExtractionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    extracted_fields: dict[str, Any]
    summary: str | None
    inconsistencies: list[dict[str, Any]]
    confirmed_by: uuid.UUID | None
    confirmed_at: datetime | None

    model_config = {"from_attributes": True}


class ConfirmExtractionRequest(BaseModel):
    extracted_fields: dict[str, Any]
    """The (possibly human-edited) final field values
    to persist as confirmed."""
