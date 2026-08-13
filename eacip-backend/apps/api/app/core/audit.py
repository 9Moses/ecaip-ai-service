import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from fastapi import Request


async def log_audit_event(
    db: AsyncSession,
    event_type: str,
    result: str = "success",
    user_id: uuid.UUID | None = None,
    resource: str | None = None,
    ip_address: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        event_type=event_type,
        resource=resource,
        result=result,
        metadata_=metadata or {},
        ip_address=ip_address,
    )
    db.add(entry)
    await db.commit()

    # Deliberately a separate commit from whatever business-logic transaction the
    # caller is in the middle of — an audit log entry should be recorded regardless
    # of whether the surrounding operation ultimately succeeds or the caller's
    # transaction is rolled back for an unrelated reason. See Step 3's discussion
    # of "log failures too" for why this matters in practice.


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
