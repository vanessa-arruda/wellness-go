from httpx import AsyncClient


async def _register_and_get_access_token(client: AsyncClient, email: str) -> str:
    resp = await client.post("/auth/register", json={"email": email, "password": "s3cret-pw"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


async def test_weight_entry_crud(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "weight1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/measurements/weight", headers=headers, json={"weight_kg": 70.5, "recorded_at": "2026-07-19"}
    )
    assert create_resp.status_code == 201
    entry_id = create_resp.json()["id"]

    list_resp = await client.get("/measurements/weight", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["weight_kg"] == 70.5

    update_resp = await client.put(
        f"/measurements/weight/{entry_id}", headers=headers, json={"weight_kg": 71.0, "recorded_at": "2026-07-19"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["weight_kg"] == 71.0

    delete_resp = await client.delete(f"/measurements/weight/{entry_id}", headers=headers)
    assert delete_resp.status_code == 204

    empty_list = await client.get("/measurements/weight", headers=headers)
    assert empty_list.json() == []


async def test_body_measurement_crud(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "body1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "recorded_at": "2026-07-19",
        "neck_cm": 38.0,
        "chest_cm": 100.0,
        "waist_cm": 80.0,
        "navel_cm": 85.0,
        "hips_cm": 95.0,
        "left_arm_cm": 32.0,
        "right_arm_cm": 32.5,
        "left_thigh_cm": 55.0,
        "right_thigh_cm": 55.5,
        "left_calf_cm": 37.0,
        "right_calf_cm": 37.5,
    }

    create_resp = await client.post("/measurements/body", headers=headers, json=payload)
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["navel_cm"] == 85.0
    assert body["waist_cm"] == 80.0
    entry_id = body["id"]

    list_resp = await client.get("/measurements/body", headers=headers)
    assert len(list_resp.json()) == 1

    updated_payload = {**payload, "waist_cm": 78.0}
    update_resp = await client.put(f"/measurements/body/{entry_id}", headers=headers, json=updated_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["waist_cm"] == 78.0

    delete_resp = await client.delete(f"/measurements/body/{entry_id}", headers=headers)
    assert delete_resp.status_code == 204

    empty_list = await client.get("/measurements/body", headers=headers)
    assert empty_list.json() == []


async def test_body_measurement_allows_partial_fields(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "body2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/measurements/body", headers=headers, json={"recorded_at": "2026-07-19", "waist_cm": 80.0}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["waist_cm"] == 80.0
    assert body["navel_cm"] is None
    assert body["left_calf_cm"] is None


async def test_measurements_require_auth(client: AsyncClient) -> None:
    resp = await client.get("/measurements/weight")
    assert resp.status_code in (401, 403)

    resp = await client.get("/measurements/body")
    assert resp.status_code in (401, 403)
