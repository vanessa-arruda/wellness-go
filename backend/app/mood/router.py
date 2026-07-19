import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.db import get_db
from app.mood import service
from app.mood.schemas import MoodEntryIn, MoodEntryRead

router = APIRouter(prefix="/mood", tags=["mood"])


@router.post("", response_model=MoodEntryRead, status_code=status.HTTP_201_CREATED)
async def create_mood_entry(
    payload: MoodEntryIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MoodEntryRead:
    try:
        return await service.create_mood_entry(db, current_user.id, payload)
    except service.DuplicateMoodEntryError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[MoodEntryRead])
async def list_mood_entries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MoodEntryRead]:
    return await service.list_mood_entries(db, current_user.id)


@router.put("/{entry_id}", response_model=MoodEntryRead)
async def update_mood_entry(
    entry_id: uuid.UUID,
    payload: MoodEntryIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MoodEntryRead:
    entry = await service.get_mood_entry(db, current_user.id, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mood entry not found")
    try:
        return await service.update_mood_entry(db, entry, payload)
    except service.DuplicateMoodEntryError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mood_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    entry = await service.get_mood_entry(db, current_user.id, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mood entry not found")
    await service.delete_mood_entry(db, entry)
