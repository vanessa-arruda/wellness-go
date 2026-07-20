import csv
import io
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient

_WEEKDAY_VALUES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _today():
    return datetime.now(timezone.utc).date()


async def _register_and_get_access_token(client: AsyncClient, email: str) -> str:
    resp = await client.post("/auth/register", json={"email": email, "password": "s3cret-pw"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


async def _create_template(client: AsyncClient, headers: dict, name: str = "A") -> str:
    resp = await client.post(
        "/workout-templates",
        headers=headers,
        json={
            "name": name,
            "exercises": [
                {"exercise_id": "exr_bench", "exercise_name": "Bench Press", "target_sets": 3, "target_reps": 10}
            ],
        },
    )
    return resp.json()["id"]


async def _schedule(client: AsyncClient, headers: dict, template_id: str, day: str, start: str, end: str) -> dict:
    resp = await client.post(
        f"/workout-templates/{template_id}/schedule",
        headers=headers,
        json={"days_of_week": [day], "start_date": start, "end_date": end},
    )
    assert resp.status_code == 201
    return resp.json()


async def test_weight_history_is_ascending_and_filterable(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "dash1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/measurements/weight", headers=headers, json={"weight_kg": 70.0, "recorded_at": "2026-07-01"})
    await client.post("/measurements/weight", headers=headers, json={"weight_kg": 71.0, "recorded_at": "2026-07-10"})

    resp = await client.get("/dashboard/weight-history", headers=headers)
    assert resp.status_code == 200
    dates = [e["recorded_at"] for e in resp.json()]
    assert dates == ["2026-07-01", "2026-07-10"]

    filtered = await client.get(
        "/dashboard/weight-history",
        headers=headers,
        params={"start_date": "2026-07-05", "end_date": "2026-07-31"},
    )
    assert [e["recorded_at"] for e in filtered.json()] == ["2026-07-10"]


async def test_today_overview(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "dash2@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    today = _today()
    today_str = today.isoformat()
    today_dow = _WEEKDAY_VALUES[today.weekday()]

    template_id = await _create_template(client, headers)
    await _schedule(
        client, headers, template_id, today_dow, today_str, (today + timedelta(days=7)).isoformat()
    )
    await client.post("/measurements/weight", headers=headers, json={"weight_kg": 68.5, "recorded_at": today_str})
    await client.post("/mood", headers=headers, json={"moods": ["joyful"], "recorded_at": today_str})

    before = await client.get("/dashboard/today", headers=headers)
    assert before.status_code == 200
    body = before.json()
    assert body["session_completed_today"] is False
    assert len(body["scheduled"]) == 1
    assert body["scheduled"][0]["template_name"] == "A"
    assert body["mood"]["moods"] == ["joyful"]
    assert body["latest_weight"]["weight_kg"] == 68.5

    session_id = (
        await client.post("/workout-sessions", headers=headers, json={"template_id": template_id})
    ).json()["id"]
    await client.post(
        f"/workout-sessions/{session_id}/sets",
        headers=headers,
        json={"exercise_id": "exr_bench", "exercise_name": "Bench Press", "weight": 40, "reps": 10},
    )
    await client.post(f"/workout-sessions/{session_id}/finish", headers=headers)

    after = await client.get("/dashboard/today", headers=headers)
    assert after.json()["session_completed_today"] is True


async def test_workout_stats_and_personal_records(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "dash3@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    template_id = await _create_template(client, headers)

    session_id = (
        await client.post("/workout-sessions", headers=headers, json={"template_id": template_id})
    ).json()["id"]
    await client.post(
        f"/workout-sessions/{session_id}/sets",
        headers=headers,
        json={"exercise_id": "exr_bench", "exercise_name": "Bench Press", "weight": 40, "reps": 10},
    )
    await client.post(
        f"/workout-sessions/{session_id}/sets",
        headers=headers,
        json={"exercise_id": "exr_bench", "exercise_name": "Bench Press", "weight": 50, "reps": 6},
    )
    await client.post(f"/workout-sessions/{session_id}/finish", headers=headers)

    today = _today()
    stats_resp = await client.get(
        "/dashboard/workout-stats",
        headers=headers,
        params={"start_date": (today - timedelta(days=1)).isoformat(), "end_date": today.isoformat()},
    )
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["sessions_count"] == 1
    trend = stats["exercise_volume_trend"]
    assert len(trend) == 1
    assert trend[0]["exercise_id"] == "exr_bench"
    assert trend[0]["points"][0]["volume"] == 40 * 10 + 50 * 6

    pr_resp = await client.get("/dashboard/personal-records", headers=headers)
    assert pr_resp.status_code == 200
    records = pr_resp.json()
    assert len(records) == 1
    assert records[0]["max_weight"] == 50.0
    assert records[0]["reps_at_max_weight"] == 6
    assert records[0]["max_reps"] == 10


async def test_adherence(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "dash4@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    today = _today()
    window_start = today - timedelta(days=6)

    today_dow = _WEEKDAY_VALUES[today.weekday()]
    missed_dow = _WEEKDAY_VALUES[(today.weekday() - 3) % 7]

    template_done = await _create_template(client, headers, "Done")
    template_missed = await _create_template(client, headers, "Missed")
    await _schedule(client, headers, template_done, today_dow, window_start.isoformat(), today.isoformat())
    await _schedule(client, headers, template_missed, missed_dow, window_start.isoformat(), today.isoformat())

    session_id = (
        await client.post("/workout-sessions", headers=headers, json={"template_id": template_done})
    ).json()["id"]
    await client.post(f"/workout-sessions/{session_id}/finish", headers=headers)

    resp = await client.get(
        "/dashboard/adherence",
        headers=headers,
        params={"start_date": window_start.isoformat(), "end_date": today.isoformat()},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["scheduled_count"] == 2
    assert body["completed_count"] == 1
    assert body["adherence_percentage"] == 50.0


async def test_csv_exports(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "dash5@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/measurements/weight", headers=headers, json={"weight_kg": 72.0, "recorded_at": "2026-07-01"})

    resp = await client.get("/dashboard/export/weight.csv", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "recorded_at,weight_kg" in resp.text
    assert "72.0" in resp.text or "72" in resp.text


async def test_csv_export_neutralizes_formula_injection(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "dash6@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    note_payload = '=HYPERLINK("http://evil.com","click")'
    await client.post(
        "/mood",
        headers=headers,
        json={"moods": ["joyful"], "note": note_payload, "recorded_at": "2026-07-01"},
    )
    mood_csv = (await client.get("/dashboard/export/mood.csv", headers=headers)).text
    mood_rows = list(csv.reader(io.StringIO(mood_csv)))
    note_cell = mood_rows[1][2]
    assert note_cell == "'" + note_payload
    assert not note_cell.startswith("=")

    template_id = await _create_template(client, headers)
    session_id = (
        await client.post("/workout-sessions", headers=headers, json={"template_id": template_id})
    ).json()["id"]
    exercise_name_payload = "=cmd|'/c calc'!A0"
    await client.post(
        f"/workout-sessions/{session_id}/sets",
        headers=headers,
        json={"exercise_id": "exr_bench", "exercise_name": exercise_name_payload, "weight": 40, "reps": 10},
    )
    sessions_csv = (await client.get("/dashboard/export/workout-sessions.csv", headers=headers)).text
    session_rows = list(csv.reader(io.StringIO(sessions_csv)))
    exercise_name_cell = session_rows[1][4]
    assert exercise_name_cell == "'" + exercise_name_payload
    assert not exercise_name_cell.startswith("=")


async def test_dashboard_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/dashboard/today")
    assert resp.status_code in (401, 403)
