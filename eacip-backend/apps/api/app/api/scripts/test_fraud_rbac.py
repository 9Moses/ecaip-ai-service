import pytest
from typing import cast
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _register_and_login(client: AsyncClient, email: str) -> str:
    password = "correct-horse-battery-staple"

    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    return cast(str, login_resp.json()["access_token"])


async def test_employee_cannot_access_fraud_queue() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await _register_and_login(client, "employee-fraud-test@example.com")

        response = await client.get(
            "/api/v1/fraud/flags", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
