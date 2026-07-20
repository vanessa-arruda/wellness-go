from httpx import AsyncClient


async def _register_and_get_access_token(client: AsyncClient, email: str) -> str:
    resp = await client.post("/auth/register", json={"email": email, "password": "s3cret-pw"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


def _template_payload(name: str) -> dict:
    return {
        "name": name,
        "exercises": [
            {
                "exercise_id": "exr_bench",
                "exercise_name": "Bench Press",
                "exercise_image_url": "https://cdn.exercisedb.dev/bench.jpg",
                "target_sets": 3,
                "target_reps": 10,
            },
            {
                "exercise_id": "exr_squat",
                "exercise_name": "Squat",
                "exercise_image_url": None,
                "target_sets": 4,
                "target_reps": 8,
            },
        ],
    }


async def test_create_and_get_template(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "templates1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post("/workout-templates", headers=headers, json=_template_payload("A"))
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["name"] == "A"
    assert [e["exercise_name"] for e in body["exercises"]] == ["Bench Press", "Squat"]
    assert [e["position"] for e in body["exercises"]] == [0, 1]

    get_resp = await client.get(f"/workout-templates/{body['id']}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "A"


async def test_update_template_replaces_exercise_list(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "templates2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post("/workout-templates", headers=headers, json=_template_payload("A"))
    template_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/workout-templates/{template_id}",
        headers=headers,
        json={
            "name": "A (updated)",
            "exercises": [
                {
                    "exercise_id": "exr_deadlift",
                    "exercise_name": "Deadlift",
                    "exercise_image_url": None,
                    "target_sets": 5,
                    "target_reps": 5,
                }
            ],
        },
    )
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["name"] == "A (updated)"
    assert [e["exercise_name"] for e in body["exercises"]] == ["Deadlift"]


async def test_delete_template(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "templates3@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post("/workout-templates", headers=headers, json=_template_payload("A"))
    template_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/workout-templates/{template_id}", headers=headers)
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/workout-templates/{template_id}", headers=headers)
    assert get_resp.status_code == 404


async def test_templates_require_auth(client: AsyncClient) -> None:
    resp = await client.get("/workout-templates")
    assert resp.status_code in (401, 403)


async def test_schedule_create_and_list(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "schedule1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    template_id = (await client.post("/workout-templates", headers=headers, json=_template_payload("A"))).json()["id"]

    schedule_resp = await client.post(
        f"/workout-templates/{template_id}/schedule",
        headers=headers,
        json={
            "days_of_week": ["mon", "wed"],
            "start_date": "2026-07-20",
            "end_date": "2026-12-31",
        },
    )
    assert schedule_resp.status_code == 201
    entries = schedule_resp.json()
    assert {e["day_of_week"] for e in entries} == {"mon", "wed"}
    assert all(e["template_name"] == "A" for e in entries)

    list_resp = await client.get("/workout-templates/schedule", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2


async def test_schedule_conflict_without_override_returns_409(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "schedule2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    template_a = (await client.post("/workout-templates", headers=headers, json=_template_payload("A"))).json()["id"]
    template_b = (await client.post("/workout-templates", headers=headers, json=_template_payload("B"))).json()["id"]

    await client.post(
        f"/workout-templates/{template_a}/schedule",
        headers=headers,
        json={"days_of_week": ["mon"], "start_date": "2026-07-20", "end_date": "2026-12-31"},
    )

    conflict_resp = await client.post(
        f"/workout-templates/{template_b}/schedule",
        headers=headers,
        json={"days_of_week": ["mon"], "start_date": "2026-08-01", "end_date": "2026-09-01"},
    )
    assert conflict_resp.status_code == 409
    detail = conflict_resp.json()["detail"]
    assert detail["conflicts"][0]["existing_template_name"] == "A"


async def test_schedule_override_splits_conflicting_range(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "schedule3@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    template_a = (await client.post("/workout-templates", headers=headers, json=_template_payload("A"))).json()["id"]
    template_c = (await client.post("/workout-templates", headers=headers, json=_template_payload("C"))).json()["id"]

    # A on Mondays for the whole year.
    await client.post(
        f"/workout-templates/{template_a}/schedule",
        headers=headers,
        json={"days_of_week": ["mon"], "start_date": "2026-01-01", "end_date": "2026-12-31"},
    )

    # Replace A with C on Mondays from 2026-08-01 onward — should keep A's
    # history before that date instead of deleting it outright.
    override_resp = await client.post(
        f"/workout-templates/{template_c}/schedule",
        headers=headers,
        json={
            "days_of_week": ["mon"],
            "start_date": "2026-08-01",
            "end_date": "2026-12-31",
            "override": True,
        },
    )
    assert override_resp.status_code == 201

    all_entries = (await client.get("/workout-templates/schedule", headers=headers)).json()
    by_template = {e["template_name"]: e for e in all_entries}

    assert len(all_entries) == 2
    assert by_template["A"]["start_date"] == "2026-01-01"
    assert by_template["A"]["end_date"] == "2026-07-31"
    assert by_template["C"]["start_date"] == "2026-08-01"
    assert by_template["C"]["end_date"] == "2026-12-31"


async def test_delete_schedule_entry(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "schedule4@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    template_id = (await client.post("/workout-templates", headers=headers, json=_template_payload("A"))).json()["id"]
    entry_id = (
        await client.post(
            f"/workout-templates/{template_id}/schedule",
            headers=headers,
            json={"days_of_week": ["fri"], "start_date": "2026-07-20", "end_date": "2026-08-20"},
        )
    ).json()[0]["id"]

    delete_resp = await client.delete(f"/workout-templates/schedule/{entry_id}", headers=headers)
    assert delete_resp.status_code == 204

    remaining = (await client.get("/workout-templates/schedule", headers=headers)).json()
    assert remaining == []
