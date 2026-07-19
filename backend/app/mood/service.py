import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.mood.models import MoodEntry
from app.mood.schemas import MoodEntryIn


class DuplicateMoodEntryError(Exception):
    pass


async def list_mood_entries(db: AsyncSession, user_id: uuid.UUID) -> list[MoodEntry]:
    result = await db.execute(
        select(MoodEntry).where(MoodEntry.user_id == user_id).order_by(MoodEntry.recorded_at.desc())
    )
    return list(result.scalars().all())


async def get_mood_entry(db: AsyncSession, user_id: uuid.UUID, entry_id: uuid.UUID) -> MoodEntry | None:
    result = await db.execute(select(MoodEntry).where(MoodEntry.id == entry_id, MoodEntry.user_id == user_id))
    return result.scalar_one_or_none()


async def _get_by_date(db: AsyncSession, user_id: uuid.UUID, recorded_at: date) -> MoodEntry | None:
    result = await db.execute(
        select(MoodEntry).where(MoodEntry.user_id == user_id, MoodEntry.recorded_at == recorded_at)
    )
    return result.scalar_one_or_none()


async def create_mood_entry(db: AsyncSession, user_id: uuid.UUID, payload: MoodEntryIn) -> MoodEntry:
    existing = await _get_by_date(db, user_id, payload.recorded_at)
    if existing is not None:
        raise DuplicateMoodEntryError(f"A mood entry already exists for {payload.recorded_at}")

    entry = MoodEntry(user_id=user_id, moods=payload.moods, note=payload.note, recorded_at=payload.recorded_at)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def update_mood_entry(db: AsyncSession, entry: MoodEntry, payload: MoodEntryIn) -> MoodEntry:
    if payload.recorded_at != entry.recorded_at:
        existing = await _get_by_date(db, entry.user_id, payload.recorded_at)
        if existing is not None and existing.id != entry.id:
            raise DuplicateMoodEntryError(f"A mood entry already exists for {payload.recorded_at}")

    entry.moods = payload.moods
    entry.note = payload.note
    entry.recorded_at = payload.recorded_at
    await db.commit()
    await db.refresh(entry)
    return entry


async def delete_mood_entry(db: AsyncSession, entry: MoodEntry) -> None:
    await db.delete(entry)
    await db.commit()
