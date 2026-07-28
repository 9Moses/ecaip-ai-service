import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_register_login_me_flow(client: AsyncClient):
    email = "test-user@example.com"
    password = "correct-horse-battery-staple"

    register_resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert register_resp.status_code == 201, register_resp.json()
    assert register_resp.json()["role"] == "Employee"

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_resp.status_code == 200, login_resp.json()
    tokens = login_resp.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_resp.status_code == 200, me_resp.json()
    assert me_resp.json()["email"] == email


async def test_refresh_token_rotation_invalidates_old_token(client: AsyncClient):
    email = "rotate-test@example.com"
    password = "correct-horse-battery-staple"

    reg = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 201, reg.json()

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_resp.status_code == 200, login_resp.json()
    old_refresh = login_resp.json()["refresh_token"]

    first_refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert first_refresh.status_code == 200, first_refresh.json()

    # Reusing the old token must now be rejected (it was rotated)
    reuse_attempt = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse_attempt.status_code == 401, reuse_attempt.json()
