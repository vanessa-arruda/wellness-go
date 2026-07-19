from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.exercises import service
from app.exercises.client import ExerciseDBError
from app.exercises.schemas import ExerciseDetail, ExercisePage, ExerciseSummary, ReferenceItem

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _as_http_exception(exc: ExerciseDBError) -> HTTPException:
    if exc.status_code == 404:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="ExerciseDB request failed")


@router.get("", response_model=ExercisePage)
async def list_exercises(
    name: str | None = Query(default=None),
    keywords: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
) -> ExercisePage:
    try:
        return await service.get_exercises(name=name, keywords=keywords, cursor=cursor)
    except ExerciseDBError as exc:
        raise _as_http_exception(exc) from exc


@router.get("/search", response_model=list[ExerciseSummary])
async def search_exercises(
    q: str = Query(min_length=1),
    current_user: User = Depends(get_current_user),
) -> list[ExerciseSummary]:
    try:
        return await service.search_exercises(q)
    except ExerciseDBError as exc:
        raise _as_http_exception(exc) from exc


@router.get("/body-parts", response_model=list[ReferenceItem])
async def get_body_parts(current_user: User = Depends(get_current_user)) -> list[ReferenceItem]:
    try:
        return await service.get_body_parts()
    except ExerciseDBError as exc:
        raise _as_http_exception(exc) from exc


@router.get("/equipments", response_model=list[ReferenceItem])
async def get_equipments(current_user: User = Depends(get_current_user)) -> list[ReferenceItem]:
    try:
        return await service.get_equipments()
    except ExerciseDBError as exc:
        raise _as_http_exception(exc) from exc


@router.get("/muscles", response_model=list[ReferenceItem])
async def get_muscles(current_user: User = Depends(get_current_user)) -> list[ReferenceItem]:
    try:
        return await service.get_muscles()
    except ExerciseDBError as exc:
        raise _as_http_exception(exc) from exc


@router.get("/exercise-types", response_model=list[ReferenceItem])
async def get_exercise_types(current_user: User = Depends(get_current_user)) -> list[ReferenceItem]:
    try:
        return await service.get_exercise_types()
    except ExerciseDBError as exc:
        raise _as_http_exception(exc) from exc


@router.get("/{exercise_id}", response_model=ExerciseDetail)
async def get_exercise(
    exercise_id: str,
    current_user: User = Depends(get_current_user),
) -> ExerciseDetail:
    try:
        return await service.get_exercise(exercise_id)
    except ExerciseDBError as exc:
        raise _as_http_exception(exc) from exc
