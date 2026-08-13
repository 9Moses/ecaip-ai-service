from fastapi import APIRouter, Depends

from app.core.rbac import require_role
from app.models.user import User
from app.services.analytics_export.backfill import run_backfill
import csv
import io
import uuid
from datetime import datetime

from fastapi import Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/analytics-export/run")
async def trigger_analytics_export_backfill(
    _user: User = Depends(require_role("Admin", "Super Admin")),
) -> dict[str, int]:
    exported_count = await run_backfill()
    return {"exported_count": exported_count}


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    event_type: str | None = None,
    user_id: uuid.UUID | None = None,
    since: datetime | None = None,
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_role("Admin", "Super Admin")),
) -> list[AuditLogResponse]:
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if since:
        query = query.where(AuditLog.created_at >= since)

    result = await db.execute(query)
    return [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            event_type=log.event_type,
            resource=log.resource,
            result=log.result,
            metadata=log.metadata_,
            ip_address=log.ip_address,
            created_at=log.created_at,
        )
        for log in result.scalars().all()
    ]


@router.get("/audit-logs/export")
async def export_audit_logs(
    since: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_role("Admin", "Super Admin")),
) -> StreamingResponse:
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if since:
        query = query.where(AuditLog.created_at >= since)
    result = await db.execute(query)
    logs = result.scalars().all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "user_id",
            "event_type",
            "resource",
            "result",
            "ip_address",
            "created_at",
            "metadata",
        ]
    )
    for log in logs:
        writer.writerow(
            [
                log.id,
                log.user_id,
                log.event_type,
                log.resource,
                log.result,
                log.ip_address,
                log.created_at.isoformat(),
                log.metadata_,
            ]
        )
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=eacip_audit_logs.csv"},
    )
