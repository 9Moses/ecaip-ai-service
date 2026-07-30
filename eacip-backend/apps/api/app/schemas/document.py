import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    document_type: str
    status: str
    extraction_method: str | None
    page_count: int | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentExtractionResposne(BaseModel):
    id: uuid.UUID
    status: str
    raw_text: str | None
    extraction_method: str | None
    page_count: int | None

    model_config = {"from_attributes": True}
