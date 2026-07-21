from httpx import AsyncClient


async def _register_and_get_access_token(client: AsyncClient, email: str) -> str:
    resp = await client.post("/auth/register", json={"email": email, "password": "s3cret-pw"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


async def _create_template(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(
        "/workout-templates",
        headers=headers,
        json={
            "name": "A",
            "exercises": [
                {
                    "exercise_id": "exr_bench",
                    "exercise_name": "Bench Press",
                    "target_sets": 3,
                    "target_reps": 10,
                },
                {
                    "exercise_id": "exr_squat",
                    "exercise_name": "Squat",
                    "target_sets": 3,
                    "target_reps": 8,
                },
            ],
        },
    )
    return resp.json()["id"]


async def test_start_session_requires_owned_template(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "sessions1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    import uuid

    resp = await client.post("/workout-sessions", headers=headers, json={"template_id": str(uuid.uuid4())})
    assert resp.status_code == 404


async def test_start_session_and_log_sets_incrementally(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "sessions2@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    template_id = await _create_template(client, headers)

    start_resp = await client.post("/workout-sessions", headers=headers, json={"template_id": template_id})
    assert start_resp.status_code == 201
    session = start_resp.json()
    assert session["finished_at"] is None
    assert session["logged_sets"] == []
    session_id = session["id"]

    first_set = await client.post(
        f"/workout-sessions/{session_id}/sets",
        headers=headers,
        json={"exercise_id": "exr_bench", "exercise_name": "Bench Press", "weight": 40.0, "reps": 10},
    )
    assert first_set.status_code == 201
    assert first_set.json()["set_number"] == 1

    second_set = await client.post(
        f"/workout-sessions/{session_id}/sets",
        headers=headers,
        json={"exercise_id": "exr_bench", "exercise_name": "Bench Press", "weight": 42.5, "reps": 8},
    )
    assert second_set.json()["set_number"] == 2

    # Squat is never logged this session — allowed, no data for it.
    get_resp = await client.get(f"/workout-sessions/{session_id}", headers=headers)
    logged = get_resp.json()["logged_sets"]
    assert len(logged) == 2
    assert {s["exercise_id"] for s in logged} == {"exr_bench"}


async def test_update_logged_set_fixes_a_mistake(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "sessions3@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    template_id = await _create_template(client, headers)
    session_id = (await client.post("/workout-sessions", headers=headers, json={"template_id": template_id})).json()[
        "id"
    ]

    logged = (
        await client.post(
            f"/workout-sessions/{session_id}/sets",
            headers=headers,
            json={"exercise_id": "exr_bench", "exercise_name": "Bench Press", "weight": 999, "reps": 10},
        )
    ).json()

    update_resp = await client.put(
        f"/workout-sessions/{session_id}/sets/{logged['id']}",
        headers=headers,
        json={"weight": 40.0, "reps": 10},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["weight"] == 40.0


async def test_delete_logged_set(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "sessions4@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    template_id = await _create_template(client, headers)
    session_id = (await client.post("/workout-sessions", headers=headers, json={"template_id": template_id})).json()[
        "id"
    ]

    logged = (
        await client.post(
            f"/workout-sessions/{session_id}/sets",
            headers=headers,
            json={"exercise_id": "exr_bench", "exercise_name": "Bench Press", "weight": 40.0, "reps": 10},
        )
    ).json()

    delete_resp = await client.delete(f"/workout-sessions/{session_id}/sets/{logged['id']}", headers=headers)
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/workout-sessions/{session_id}", headers=headers)
    assert get_resp.json()["logged_sets"] == []


async def test_finish_session_blocks_further_logging(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "sessions5@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    template_id = await _create_template(client, headers)
    session_id = (await client.post("/workout-sessions", headers=headers, json={"template_id": template_id})).json()[
        "id"
    ]

    await client.post(
        f"/workout-sessions/{session_id}/sets",
        headers=headers,
        json={"exercise_id": "exr_bench", "exercise_name": "Bench Press", "weight": 40.0, "reps": 10},
    )

    finish_resp = await client.post(f"/workout-sessions/{session_id}/finish", headers=headers)
    assert finish_resp.status_code == 200
    assert finish_resp.json()["finished_at"] is not None

    finish_again = await client.post(f"/workout-sessions/{session_id}/finish", headers=headers)
    assert finish_again.status_code == 409

    log_after_finish = await client.post(
        f"/workout-sessions/{session_id}/sets",
        headers=headers,
        json={"exercise_id": "exr_squat", "exercise_name": "Squat", "weight": 60.0, "reps": 8},
    )
    assert log_after_finish.status_code == 409


async def test_delete_session(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "sessions6@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    template_id = await _create_template(client, headers)
    session_id = (await client.post("/workout-sessions", headers=headers, json={"template_id": template_id})).json()[
        "id"
    ]

    delete_resp = await client.delete(f"/workout-sessions/{session_id}", headers=headers)
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/workout-sessions/{session_id}", headers=headers)
    assert get_resp.status_code == 404


async def test_sessions_require_auth(client: AsyncClient) -> None:
    resp = await client.get("/workout-sessions")
    assert resp.status_code in (401, 403)
