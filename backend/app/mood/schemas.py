import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.mood.models import MoodTag


class MoodEntryIn(BaseModel):
    moods: list[MoodTag] = Field(min_length=1)
    note: str | None = Field(default=None, max_length=1000)
    recorded_at: date


class MoodEntryRead(BaseModel):
    id: uuid.UUID
    moods: list[MoodTag]
    note: str | None
    recorded_at: date
    created_at: datetime

    model_config = {"from_attributes": True}
