import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SessionStart(BaseModel):
    template_id: uuid.UUID


class LoggedSetIn(BaseModel):
    exercise_id: str
    exercise_name: str
    exercise_image_url: str | None = None
    weight: float | None = Field(default=None, ge=0)
    reps: int = Field(gt=0)


class LoggedSetUpdate(BaseModel):
    weight: float | None = Field(default=None, ge=0)
    reps: int = Field(gt=0)


class LoggedSetRead(BaseModel):
    id: uuid.UUID
    exercise_id: str
    exercise_name: str
    exercise_image_url: str | None
    set_number: int
    weight: float | None
    reps: int
    logged_at: datetime

    model_config = {"from_attributes": True}


class SessionRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    template_id: uuid.UUID | None
    started_at: datetime
    finished_at: datetime | None
    logged_sets: list[LoggedSetRead]

    model_config = {"from_attributes": True}
