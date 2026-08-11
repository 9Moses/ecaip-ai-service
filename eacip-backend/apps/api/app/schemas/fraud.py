import uuid
from datetime import datetime

from pydantic import BaseModel


class FraudFlagResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID | None
    claim_reference: str | None
    score: float
    rationale: str
    evidence: list[dict[str, str]]
    status: str
    assigned_to: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpdateFraudFlagRequest(BaseModel):
    status: str | None = None

    assigned_to: uuid.UUID | None = None
