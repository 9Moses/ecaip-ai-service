import hashlib
import uuid
from datetime import datetime, timedelta, UTC

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.models.user import User

settings = get_settings()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
#oath2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
http_bearer = HTTPBearer()

def hash_password(password: str) -> str:
    return str(pwd_context.hash(password))


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bool(pwd_context.verify(plain_password, password_hash))


def hash_token(token: str) -> str:
    """Refresh tokens are stored hashed, never in plaintext, per doc 07 §7.4."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: uuid.UUID, role_name: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "role": role_name, "exp": expire, "type": "access"}
    return str(jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm))


def create_refresh_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": str(user_id), "jti": str(uuid.uuid4()), "exp": expire, "type": "refresh"}
    return str(jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentails",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            raise credentials_error
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = await db.scalar(select(User).where(User.id == uuid.UUID(user_id)))
    if user is None or not user.is_active:
        raise credentials_error
    return user