from httpx import AsyncClient


async def _register_and_get_access_token(client: AsyncClient, email: str) -> str:
    resp = await client.post("/auth/register", json={"email": email, "password": "s3cret-pw"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


async def test_create_mood_entry_with_multiple_tags(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "mood1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/mood",
        headers=headers,
        json={"moods": ["joyful", "energetic", "confident"], "note": "great workout", "recorded_at": "2026-07-19"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["moods"] == ["joyful", "energetic", "confident"]
    assert body["note"] == "great workout"


async def test_create_mood_entry_requires_at_least_one_tag(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "mood2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/mood", headers=headers, json={"moods": [], "recorded_at": "2026-07-19"})
    assert resp.status_code == 422


async def test_only_one_entry_per_day(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "mood3@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.post("/mood", headers=headers, json={"moods": ["peaceful"], "recorded_at": "2026-07-19"})
    assert first.status_code == 201

    second = await client.post("/mood", headers=headers, json={"moods": ["anxious"], "recorded_at": "2026-07-19"})
    assert second.status_code == 409


async def test_update_mood_entry(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "mood4@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = (
        await client.post("/mood", headers=headers, json={"moods": ["gloomy"], "recorded_at": "2026-07-19"})
    ).json()

    update_resp = await client.put(
        f"/mood/{created['id']}",
        headers=headers,
        json={"moods": ["hopeful", "relieved"], "note": "felt better later", "recorded_at": "2026-07-19"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["moods"] == ["hopeful", "relieved"]


async def test_list_and_delete_mood_entries(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "mood5@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = (
        await client.post("/mood", headers=headers, json={"moods": ["curious"], "recorded_at": "2026-07-19"})
    ).json()

    list_resp = await client.get("/mood", headers=headers)
    assert len(list_resp.json()) == 1

    delete_resp = await client.delete(f"/mood/{created['id']}", headers=headers)
    assert delete_resp.status_code == 204

    empty_list = await client.get("/mood", headers=headers)
    assert empty_list.json() == []


async def test_mood_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/mood")
    assert resp.status_code in (401, 403)
