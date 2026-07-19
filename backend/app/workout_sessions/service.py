import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.workout_sessions.models import LoggedSet, WorkoutSession
from app.workout_sessions.schemas import LoggedSetIn, LoggedSetUpdate


class SessionAlreadyFinishedError(Exception):
    pass


async def start_session(db: AsyncSession, user_id: uuid.UUID, template_id: uuid.UUID) -> WorkoutSession:
    session = WorkoutSession(user_id=user_id, template_id=template_id)
    db.add(session)
    await db.commit()
    return await get_session(db, user_id, session.id)  # type: ignore[return-value]


async def list_sessions(db: AsyncSession, user_id: uuid.UUID) -> list[WorkoutSession]:
    result = await db.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user_id)
        .options(selectinload(WorkoutSession.logged_sets))
        .order_by(WorkoutSession.started_at.desc())
    )
    return list(result.scalars().all())


async def get_session(db: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID) -> WorkoutSession | None:
    result = await db.execute(
        select(WorkoutSession)
        .where(WorkoutSession.id == session_id, WorkoutSession.user_id == user_id)
        .options(selectinload(WorkoutSession.logged_sets))
    )
    return result.scalar_one_or_none()


async def log_set(db: AsyncSession, session: WorkoutSession, payload: LoggedSetIn) -> LoggedSet:
    if session.finished_at is not None:
        raise SessionAlreadyFinishedError("Cannot log a set on a finished session")

    count_result = await db.execute(
        select(func.count())
        .select_from(LoggedSet)
        .where(LoggedSet.session_id == session.id, LoggedSet.exercise_id == payload.exercise_id)
    )
    set_number = count_result.scalar_one() + 1

    logged_set = LoggedSet(
        session_id=session.id,
        exercise_id=payload.exercise_id,
        exercise_name=payload.exercise_name,
        exercise_image_url=payload.exercise_image_url,
        set_number=set_number,
        weight=payload.weight,
        reps=payload.reps,
    )
    db.add(logged_set)
    await db.commit()
    await db.refresh(logged_set)
    return logged_set


async def get_logged_set(
    db: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID, set_id: uuid.UUID
) -> LoggedSet | None:
    result = await db.execute(
        select(LoggedSet)
        .join(WorkoutSession, WorkoutSession.id == LoggedSet.session_id)
        .where(
            LoggedSet.id == set_id,
            LoggedSet.session_id == session_id,
            WorkoutSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_logged_set(db: AsyncSession, logged_set: LoggedSet, payload: LoggedSetUpdate) -> LoggedSet:
    logged_set.weight = payload.weight
    logged_set.reps = payload.reps
    await db.commit()
    await db.refresh(logged_set)
    return logged_set


async def delete_logged_set(db: AsyncSession, logged_set: LoggedSet) -> None:
    await db.delete(logged_set)
    await db.commit()


async def finish_session(db: AsyncSession, session: WorkoutSession) -> WorkoutSession:
    if session.finished_at is not None:
        raise SessionAlreadyFinishedError("Session is already finished")

    session.finished_at = datetime.now(timezone.utc)
    await db.commit()
    return await get_session(db, session.user_id, session.id)  # type: ignore[return-value]


async def delete_session(db: AsyncSession, session: WorkoutSession) -> None:
    await db.delete(session)
    await db.commit()
