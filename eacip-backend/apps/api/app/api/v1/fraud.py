import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rbac import require_role
from app.models.fraud_flag import FraudFlag
from app.models.user import User
from app.schemas.fraud import FraudFlagResponse, UpdateFraudFlagRequest

router = APIRouter(prefix="/fraud", tags=["fraud"])

VALID_STATUSES = {"open", "under_review", "cleared", "confirmed_fraud"}
QUEUE_ROLES = ("Fraud Analyst", "Claims Manager", "Admin", "Super Admin")


@router.get("/flags", response_model=list[FraudFlagResponse])
async def list_fraud_flags(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_role(*QUEUE_ROLES)),
) -> list[FraudFlagResponse]:
    query = select(FraudFlag).order_by(FraudFlag.score.desc(), FraudFlag.created_at.desc())
    if status_filter:
        if status_filter not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter"
            )
        query = query.where(FraudFlag.status == status_filter)

    result = await db.execute(query)
    return [FraudFlagResponse.model_validate(f) for f in result.scalars().all()]


@router.get("/flags/{flag_id}", response_model=FraudFlagResponse)
async def get_fraud_flag(
    flag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_role(*QUEUE_ROLES)),
) -> FraudFlagResponse:
    flag = await db.scalar(select(FraudFlag).where(FraudFlag.id == flag_id))
    if flag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fraud flag not found")
    return FraudFlagResponse.model_validate(flag)


@router.patch("/flags/{flag_id}", response_model=FraudFlagResponse)
async def update_fraud_flag(
    flag_id: uuid.UUID,
    payload: UpdateFraudFlagRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("Fraud Analyst", "Admin", "Super Admin")),
) -> FraudFlagResponse:
    flag = await db.scalar(select(FraudFlag).where(FraudFlag.id == flag_id))
    if flag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fraud flag not found")

    if payload.status is not None:
        if payload.status not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
        flag.status = payload.status

    if payload.assigned_to is not None:
        flag.assigned_to = payload.assigned_to

    await db.commit()
    await db.refresh(flag)

    return FraudFlagResponse.model_validate(flag)
