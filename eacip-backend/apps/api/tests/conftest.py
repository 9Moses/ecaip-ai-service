"""
Test configuration.

Provides:
- Fresh async SQLAlchemy engine per test.
- FastAPI database dependency override.
- Shared AsyncClient.
- Test database cleanup.
- One-time role seeding.
- Role-specific authentication fixtures.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.db import get_db
from app.main import app
from app.models.role import Role
from app.models.user import User
from typing import TypedDict, cast

TEST_PASSWORD = "correct-horse-battery-staple"

TEST_EMAILS = (
    "test-user@example.com",
    "rotate-test@example.com",
)


class LoginResponse(TypedDict):
    access_token: str


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def setup_db_roles(anyio_backend: str) -> None:
    """Seed database roles once per test session."""
    from app.core.seed_roles import seed_roles

    await seed_roles()


@pytest.fixture()
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create a fresh async engine for each test.

    Creating the engine inside the test fixture ensures that its
    connection pool belongs to the current event loop.
    """
    settings = get_settings()

    engine = create_async_engine(
        settings.database_url,
        echo=False,
    )

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture()
async def db_session_factory(
    db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create a session factory using the test engine."""
    return async_sessionmaker(
        db_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def cleanup_test_data(db_engine: AsyncEngine) -> None:
    """
    Remove test users and their dependent records.

    Only known test emails are targeted.
    """
    emails_sql = ", ".join(f"'{email}'" for email in TEST_EMAILS)

    async with db_engine.begin() as conn:
        # Delete child-table rows first to avoid FK violations.
        await conn.execute(text(f"""
                DELETE FROM refresh_tokens
                WHERE user_id IN (
                    SELECT id
                    FROM users
                    WHERE email IN ({emails_sql})
                )
                """))

        await conn.execute(text(f"""
                DELETE FROM audit_logs
                WHERE user_id IN (
                    SELECT id
                    FROM users
                    WHERE email IN ({emails_sql})
                )
                """))

        await conn.execute(text(f"""
                DELETE FROM users
                WHERE email IN ({emails_sql})
                """))


@pytest.fixture()
async def client(
    db_engine: AsyncEngine,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an AsyncClient with FastAPI's database dependency overridden.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with db_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()

    app.dependency_overrides[get_db] = override_get_db

    # Cleanup before test.
    await cleanup_test_data(db_engine)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    finally:
        app.dependency_overrides.pop(get_db, None)

        # Cleanup after test.
        await cleanup_test_data(db_engine)


async def _register_login_and_promote(
    client: AsyncClient,
    db_session_factory: async_sessionmaker[AsyncSession],
    role_name: str,
) -> str:
    """
    Register a unique user, promote them to the requested role,
    then log in and return the access token.
    """

    email = f"test-{role_name.lower().replace(' ', '-')}-" f"{uuid.uuid4().hex[:8]}@example.com"

    # Register.
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    response.raise_for_status()

    # Promote to requested role.
    async with db_session_factory() as db:
        role = await db.scalar(select(Role).where(Role.name == role_name))

        user = await db.scalar(select(User).where(User.email == email))

        if role is None:
            raise RuntimeError(f"Role '{role_name}' does not exist.")

        if user is None:
            raise RuntimeError(f"User '{email}' was not found after registration.")

        user.role_id = role.id

        await db.commit()

    # Login.
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    login_response.raise_for_status()

    data = cast(LoginResponse, login_response.json())

    return data["access_token"]


@pytest.fixture()
async def employee_token(
    client: AsyncClient,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> str:
    return await _register_login_and_promote(
        client,
        db_session_factory,
        "Employee",
    )


@pytest.fixture()
async def fraud_analyst_token(
    client: AsyncClient,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> str:
    return await _register_login_and_promote(
        client,
        db_session_factory,
        "Fraud Analyst",
    )


@pytest.fixture()
async def claims_manager_token(
    client: AsyncClient,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> str:
    return await _register_login_and_promote(
        client,
        db_session_factory,
        "Claims Manager",
    )


@pytest.fixture()
async def admin_token(
    client: AsyncClient,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> str:
    return await _register_login_and_promote(
        client,
        db_session_factory,
        "Admin",
    )


@pytest.fixture()
async def api_client(
    client: AsyncClient,
) -> AsyncGenerator[AsyncClient, None]:
    """Alias for ``client`` — allows test modules to use either name."""
    yield client
