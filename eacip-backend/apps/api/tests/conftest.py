"""
Test configuration.

Each test gets a fresh async engine created inside the current event loop,
preventing the "event loop is closed" / stale-connection crash.

Test isolation (no leftover rows between runs) is handled by a teardown
that deletes test-email rows after each test.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.db import get_db
from app.main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def setup_db_roles(anyio_backend: str) -> None:
    """Seed the database roles once per test session."""
    from app.core.seed_roles import seed_roles

    await seed_roles()


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Yields an AsyncClient bound to the FastAPI app with a fresh DB engine
    created in the current event loop.  Cleans up test rows after each test.
    """
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()

    app.dependency_overrides[get_db] = override_get_db

    TEST_EMAILS = (
        "'test-user@example.com'",
        "'rotate-test@example.com'",
    )
    emails_sql = ", ".join(TEST_EMAILS)

    async def _cleanup(conn_):
        await conn_.execute(text("DELETE FROM refresh_tokens"))
        await conn_.execute(
            text(
                f"DELETE FROM audit_logs WHERE user_id IN "
                f"(SELECT id FROM users WHERE email IN ({emails_sql}))"
            )
        )
        await conn_.execute(text(f"DELETE FROM users WHERE email IN ({emails_sql})"))

    # Pre-test cleanup (removes rows left by a previous interrupted run)
    from sqlalchemy import text

    async with engine.begin() as conn:
        await _cleanup(conn)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db, None)

        # Post-test cleanup
        from sqlalchemy import text as text2  # noqa: F811

        async with engine.begin() as conn:
            await conn.execute(text2("DELETE FROM refresh_tokens"))
            await conn.execute(
                text2(
                    f"DELETE FROM audit_logs WHERE user_id IN "
                    f"(SELECT id FROM users WHERE email IN ({emails_sql}))"
                )
            )
            await conn.execute(text2(f"DELETE FROM users WHERE email IN ({emails_sql})"))

        await engine.dispose()
