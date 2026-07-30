import secrets

from fastapi import Query
from fastapi.responses import RedirectResponse

from app.core.oauth_google import build_google_auth_url, exchange_code_for_userinfo
import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.config import get_settings
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


async def _issue_tokens(db: AsyncSession, user: User) -> TokenResponse:
    access_token = create_access_token(user.id, user.role.name)
    refresh_token = create_refresh_token(user.id)

    from jose import jwt

    decoded = jwt.decode(
        refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.fromtimestamp(decoded["exp"], tz=UTC),
        )
    )
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> UserResponse:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    default_role = await db.scalar(select(Role).where(Role.name == "Employee"))
    if default_role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default role 'Employee' not seeded — run seed_roles first",
        )

    user = User(
        email=payload.email, password_hash=hash_password(payload.password), role_id=default_role.id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse(
        id=user.id, email=user.email, role=default_role.name, is_active=user.is_active
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == payload.email))
    bad_creds = (
        user is None
        or user.password_hash is None
        or not verify_password(payload.password, user.password_hash)
    )
    if bad_creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    assert user is not None  # narrowed: bad_creds already covers the None case
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    return await _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    from jose import JWTError, jwt

    try:
        decoded = jwt.decode(
            payload.refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        if decoded.get("type") != "refresh":
            raise ValueError("wrong token type")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    token_hash = hash_token(payload.refresh_token)
    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if stored is None or stored.revoked or stored.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or expired",
        )

    # Rotate: revoke the old one, issue a brand new pair
    stored.revoked = True
    user = await db.scalar(select(User).where(User.id == uuid.UUID(decoded["sub"])))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active",
        )

    return await _issue_tokens(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> None:
    token_hash = hash_token(payload.refresh_token)
    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if stored:
        stored.revoked = True
        await db.commit()


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, role=user.role.name, is_active=user.is_active)


@router.get("/oauth/google")
async def google_oauth_start() -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    # For production: store `state` server-side (Redis, short TTL) and verify it
    # on callback to prevent CSRF. Skipped here for MVP simplicity — flagged
    # explicitly as a hardening item before production use.
    return RedirectResponse(url=build_google_auth_url(state))


@router.get("/oauth/google/callback")
async def google_oauth_callback(
    code: str = Query(...),
    state: str = Query(None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    userinfo = await exchange_code_for_userinfo(code)

    email = userinfo.get("email")
    google_subject = userinfo.get("sub")
    if not email or not google_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Google profile missing required fields"
        )

    user = await db.scalar(select(User).where(User.email == email))

    if user is None:
        # First-time Google sign-in: create a new EACIP identity, same as any other user
        default_role = await db.scalar(select(Role).where(Role.name == "Employee"))
        user = User(
            email=email,
            password_hash=None,
            oauth_provider="google",
            oauth_subject=google_subject,
            role_id=default_role.id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif user.oauth_provider is None:
        # Existing email/password user signing in with Google for the first time: link accounts
        user.oauth_provider = "google"
        user.oauth_subject = google_subject
        await db.commit()

    tokens = await _issue_tokens(db, user)

    # Redirect back to the frontend with tokens as query params for it to capture and store.
    # (Frontend build in Part 4 reads these on /auth/callback and moves them into its own storage.)
    redirect_url = (
        f"{settings.frontend_oauth_success_redirect}"
        f"?access_token={tokens.access_token}&refresh_token={tokens.refresh_token}"
    )
    return RedirectResponse(url=redirect_url)
