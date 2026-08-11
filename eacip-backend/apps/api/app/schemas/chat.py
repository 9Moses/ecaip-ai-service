import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    sources: list[dict[str, Any]]
    chart_data: list[dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str
