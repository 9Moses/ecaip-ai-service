import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rbac import require_role
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import UpdateRoleRequest, UserResponse
from app.core.audit import log_audit_event

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role("Admin", "Super Admin")),
) -> list[UserResponse]:
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            role=u.role.name,
            is_active=u.is_active,
        )
        for u in users
    ]


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: uuid.UUID,
    payload: UpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role("Admin", "Super Admin")),
) -> UserResponse:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_role = await db.scalar(select(Role).where(Role.name == payload.role_name))
    if new_role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown role")

    try:
        user.role_id = new_role.id
        await db.commit()
        await db.refresh(user)

        await log_audit_event(
            db,
            "user.role_changed",
            user_id=_admin.id,
            resource=f"user:{user_id}",
            metadata={"new_role": new_role.name},
        )
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user role."
        )
    return UserResponse(id=user.id, email=user.email, role=new_role.name, is_active=user.is_active)
