from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User


def require_role(*allowed_roles: str) -> Callable:
    """
    Usage:
        @router.get("/fraud/flags")
        async def list_flags(user: User = Depends(require_role("Fraud Analyst", "Admin", "Super Admin"))):
            ...
    """

    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in allowed_roles:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )

        return user

    return dependency