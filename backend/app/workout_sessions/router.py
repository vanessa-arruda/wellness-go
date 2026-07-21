import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.db import get_db
from app.workout_sessions import service
from app.workout_sessions.models import WorkoutSession
from app.workout_sessions.schemas import LoggedSetIn, LoggedSetRead, LoggedSetUpdate, SessionRead, SessionStart
from app.workout_templates.service import get_template

router = APIRouter(prefix="/workout-sessions", tags=["workout-sessions"])


async def _get_owned_session(db: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID) -> WorkoutSession:
    session = await service.get_session(db, user_id, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout session not found")
    return session


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def start_session(
    payload: SessionStart,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionRead:
    template = await get_template(db, current_user.id, payload.template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return await service.start_session(db, current_user.id, payload.template_id)


@router.get("", response_model=list[SessionRead])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SessionRead]:
    return await service.list_sessions(db, current_user.id)


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionRead:
    return await _get_owned_session(db, current_user.id, session_id)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    session = await _get_owned_session(db, current_user.id, session_id)
    await service.delete_session(db, session)


@router.post("/{session_id}/sets", response_model=LoggedSetRead, status_code=status.HTTP_201_CREATED)
async def log_set(
    session_id: uuid.UUID,
    payload: LoggedSetIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LoggedSetRead:
    session = await _get_owned_session(db, current_user.id, session_id)
    try:
        return await service.log_set(db, session, payload)
    except service.SessionAlreadyFinishedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/{session_id}/sets/{set_id}", response_model=LoggedSetRead)
async def update_logged_set(
    session_id: uuid.UUID,
    set_id: uuid.UUID,
    payload: LoggedSetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LoggedSetRead:
    logged_set = await service.get_logged_set(db, current_user.id, session_id, set_id)
    if logged_set is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Logged set not found")
    return await service.update_logged_set(db, logged_set, payload)


@router.delete("/{session_id}/sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_logged_set(
    session_id: uuid.UUID,
    set_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    logged_set = await service.get_logged_set(db, current_user.id, session_id, set_id)
    if logged_set is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Logged set not found")
    await service.delete_logged_set(db, logged_set)


@router.post("/{session_id}/finish", response_model=SessionRead)
async def finish_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionRead:
    session = await _get_owned_session(db, current_user.id, session_id)
    try:
        return await service.finish_session(db, session)
    except service.SessionAlreadyFinishedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
