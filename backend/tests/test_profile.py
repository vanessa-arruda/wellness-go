from httpx import AsyncClient


async def _register_and_get_access_token(client: AsyncClient, email: str) -> str:
    resp = await client.post("/auth/register", json={"email": email, "password": "s3cret-pw"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


async def test_get_profile_before_setup_is_not_found(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "noprofile@example.com")
    resp = await client.get("/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


async def test_create_and_read_profile(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    put_resp = await client.put(
        "/profile/me",
        headers=headers,
        json={
            "display_name": "Vanessa",
            "unit_preference": "metric",
            "date_of_birth": "1990-05-20",
            "height_cm": 170.5,
        },
    )
    assert put_resp.status_code == 200
    body = put_resp.json()
    assert body["display_name"] == "Vanessa"
    assert body["unit_preference"] == "metric"
    assert body["height_cm"] == 170.5

    get_resp = await client.get("/profile/me", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["display_name"] == "Vanessa"


async def test_update_profile_overwrites_existing(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "update-profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.put(
        "/profile/me",
        headers=headers,
        json={"display_name": "First Name", "unit_preference": "metric"},
    )
    second = await client.put(
        "/profile/me",
        headers=headers,
        json={"display_name": "Second Name", "unit_preference": "imperial"},
    )
    assert second.status_code == 200
    assert second.json()["display_name"] == "Second Name"
    assert second.json()["unit_preference"] == "imperial"


async def test_profile_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/profile/me")
    assert resp.status_code in (401, 403)
