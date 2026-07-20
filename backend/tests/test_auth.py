from httpx import AsyncClient


async def test_register_login_refresh_roundtrip(client: AsyncClient) -> None:
    register_resp = await client.post("/auth/register", json={"email": "test@example.com", "password": "s3cret-pw"})
    assert register_resp.status_code == 201
    body = register_resp.json()
    assert body["access_token"]
    assert "refresh_token" not in body
    assert "refresh_token" in register_resp.cookies

    login_resp = await client.post("/auth/login", json={"email": "test@example.com", "password": "s3cret-pw"})
    assert login_resp.status_code == 200
    assert "refresh_token" not in login_resp.json()

    refresh_resp = await client.post("/auth/refresh")
    assert refresh_resp.status_code == 200
    assert refresh_resp.json()["access_token"]


async def test_register_duplicate_email_conflicts(client: AsyncClient) -> None:
    payload = {"email": "dupe@example.com", "password": "s3cret-pw"}
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 409


async def test_login_wrong_password_is_unauthorized(client: AsyncClient) -> None:
    await client.post("/auth/register", json={"email": "wrongpw@example.com", "password": "correct-pw"})
    resp = await client.post("/auth/login", json={"email": "wrongpw@example.com", "password": "incorrect-pw"})
    assert resp.status_code == 401


async def test_refresh_without_cookie_is_unauthorized(client: AsyncClient) -> None:
    resp = await client.post("/auth/refresh")
    assert resp.status_code == 401


async def test_refresh_with_invalid_cookie_is_unauthorized(client: AsyncClient) -> None:
    client.cookies.set("refresh_token", "not-a-real-token")
    resp = await client.post("/auth/refresh")
    assert resp.status_code == 401


async def test_logout_clears_refresh_cookie(client: AsyncClient) -> None:
    await client.post("/auth/register", json={"email": "logout@example.com", "password": "s3cret-pw"})
    assert "refresh_token" in client.cookies

    logout_resp = await client.post("/auth/logout")
    assert logout_resp.status_code == 204

    refresh_resp = await client.post("/auth/refresh")
    assert refresh_resp.status_code == 401
