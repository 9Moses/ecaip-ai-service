from fastapi import APIRouter, Depends

from app.core.rbac import require_role
from app.models.user import User
from app.services.analytics_export.backfill import run_backfill

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/analytics-export/run")
async def trigger_analytics_export_backfill(
    _user: User = Depends(require_role("Admin", "Super Admin")),
) -> dict[str, int]:
    exported_count = await run_backfill()
    return {"exported_count": exported_count}
