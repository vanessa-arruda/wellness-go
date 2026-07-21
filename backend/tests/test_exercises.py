import pytest
import respx
from httpx import AsyncClient, Response

from app.core.config import settings
from app.exercises import client as exercisedb_client

EXERCISE_SAMPLE = {
    "exerciseId": "exr_test123",
    "name": "Bench Press",
    "imageUrl": "https://cdn.exercisedb.dev/img.jpg",
    "bodyParts": ["CHEST"],
    "equipments": ["BARBELL"],
    "exerciseType": "STRENGTH",
    "targetMuscles": ["PECTORALIS MAJOR"],
    "secondaryMuscles": ["TRICEPS"],
    "keywords": ["chest workout"],
}

EXERCISE_DETAIL_SAMPLE = {
    **EXERCISE_SAMPLE,
    "videoUrl": "https://cdn.exercisedb.dev/video.mp4",
    "overview": "A classic chest exercise.",
    "instructions": ["Lie on the bench.", "Press the bar up."],
    "exerciseTips": ["Keep your back flat."],
    "variations": ["Incline Bench Press"],
    "relatedExerciseIds": ["exr_related1"],
}


@pytest.fixture(autouse=True)
def _clear_exercisedb_cache():
    exercisedb_client._cache._store.clear()
    yield
    exercisedb_client._cache._store.clear()


async def _register_and_get_access_token(client: AsyncClient, email: str) -> str:
    resp = await client.post("/auth/register", json={"email": email, "password": "s3cret-pw"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


@respx.mock
async def test_list_exercises_proxies_and_maps_response(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "exlist@example.com")
    respx.get(f"{settings.exercisedb_base_url}/exercises").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "meta": {"total": 1, "hasNextPage": False, "hasPreviousPage": False, "nextCursor": None},
                "data": [EXERCISE_SAMPLE],
            },
        )
    )

    resp = await client.get("/exercises", headers={"Authorization": f"Bearer {token}"}, params={"name": "Bench Press"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["items"][0]["exerciseId"] == "exr_test123"
    assert body["items"][0]["bodyParts"] == ["CHEST"]


@respx.mock
async def test_search_exercises(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "exsearch@example.com")
    respx.get(f"{settings.exercisedb_base_url}/exercises/search").mock(
        return_value=Response(200, json={"success": True, "data": [EXERCISE_SAMPLE]})
    )

    resp = await client.get("/exercises/search", headers={"Authorization": f"Bearer {token}"}, params={"q": "bench"})
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "Bench Press"


@respx.mock
async def test_get_exercise_by_id(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "exdetail@example.com")
    respx.get(f"{settings.exercisedb_base_url}/exercises/exr_test123").mock(
        return_value=Response(200, json={"success": True, "data": EXERCISE_DETAIL_SAMPLE})
    )

    resp = await client.get("/exercises/exr_test123", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["overview"] == "A classic chest exercise."
    assert body["instructions"] == ["Lie on the bench.", "Press the bar up."]


@respx.mock
async def test_get_exercise_not_found_maps_to_404(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "exmissing@example.com")
    respx.get(f"{settings.exercisedb_base_url}/exercises/does-not-exist").mock(
        return_value=Response(404, json={"success": False, "message": "Not found"})
    )

    resp = await client.get("/exercises/does-not-exist", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


@respx.mock
async def test_get_body_parts(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "exbodyparts@example.com")
    respx.get(f"{settings.exercisedb_base_url}/bodyparts").mock(
        return_value=Response(
            200,
            json={"success": True, "data": [{"name": "CHEST", "imageUrl": "https://cdn.exercisedb.dev/chest.webp"}]},
        )
    )

    resp = await client.get("/exercises/body-parts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == [{"name": "CHEST", "imageUrl": "https://cdn.exercisedb.dev/chest.webp"}]


async def test_exercises_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/exercises")
    assert resp.status_code in (401, 403)


@respx.mock
async def test_list_exercises_is_cached(client: AsyncClient) -> None:
    token = await _register_and_get_access_token(client, "excache@example.com")
    route = respx.get(f"{settings.exercisedb_base_url}/exercises").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "meta": {"total": 1, "hasNextPage": False, "hasPreviousPage": False, "nextCursor": None},
                "data": [EXERCISE_SAMPLE],
            },
        )
    )

    headers = {"Authorization": f"Bearer {token}"}
    first = await client.get("/exercises", headers=headers, params={"name": "Bench Press"})
    second = await client.get("/exercises", headers=headers, params={"name": "Bench Press"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert route.call_count == 1
