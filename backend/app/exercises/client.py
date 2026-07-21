import time
from typing import Any

import httpx

from app.core.config import settings

_REFERENCE_PATHS = {"/bodyparts", "/equipments", "/muscles", "/exercisetypes"}
_LIST_TTL_SECONDS = 60 * 60
_REFERENCE_TTL_SECONDS = 60 * 60 * 24


class ExerciseDBError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class _TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at < time.monotonic():
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        self._store[key] = (time.monotonic() + ttl_seconds, value)


# Process-local cache: RapidAPI's Basic plan explicitly allows caching and
# caps usage at 2,000 requests/month, so avoiding redundant upstream calls
# matters more than freshness here.
_cache = _TTLCache()


async def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    cache_key = f"{path}?{sorted((params or {}).items())}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    async with httpx.AsyncClient(base_url=settings.exercisedb_base_url, timeout=10.0) as http_client:
        response = await http_client.get(
            path,
            params=params,
            headers={
                "x-rapidapi-host": settings.exercisedb_api_host,
                "x-rapidapi-key": settings.exercisedb_api_key or "",
            },
        )

    if response.status_code != 200:
        raise ExerciseDBError(f"ExerciseDB request failed: {response.status_code}", status_code=response.status_code)

    body = response.json()
    if not body.get("success", True):
        raise ExerciseDBError(f"ExerciseDB reported failure: {body}")

    ttl = _REFERENCE_TTL_SECONDS if path in _REFERENCE_PATHS else _LIST_TTL_SECONDS
    _cache.set(cache_key, body, ttl)
    return body


async def list_exercises(
    name: str | None = None, keywords: str | None = None, cursor: str | None = None
) -> dict[str, Any]:
    params = {k: v for k, v in {"name": name, "keywords": keywords, "cursor": cursor}.items() if v}
    return await _get("/exercises", params)


async def search_exercises(query: str) -> dict[str, Any]:
    return await _get("/exercises/search", {"search": query})


async def get_exercise(exercise_id: str) -> dict[str, Any]:
    return await _get(f"/exercises/{exercise_id}")


async def list_body_parts() -> dict[str, Any]:
    return await _get("/bodyparts")


async def list_equipments() -> dict[str, Any]:
    return await _get("/equipments")


async def list_muscles() -> dict[str, Any]:
    return await _get("/muscles")


async def list_exercise_types() -> dict[str, Any]:
    return await _get("/exercisetypes")
