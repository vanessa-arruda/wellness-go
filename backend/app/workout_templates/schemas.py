import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.workout_templates.models import DayOfWeek


class TemplateExerciseIn(BaseModel):
    exercise_id: str
    exercise_name: str
    exercise_image_url: str | None = None
    target_sets: int = Field(gt=0)
    target_reps: int = Field(gt=0)


class TemplateExerciseRead(BaseModel):
    id: uuid.UUID
    exercise_id: str
    exercise_name: str
    exercise_image_url: str | None
    target_sets: int
    target_reps: int
    position: int

    model_config = {"from_attributes": True}


class TemplateUpsert(BaseModel):
    name: str
    exercises: list[TemplateExerciseIn] = Field(default_factory=list)


class TemplateRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    exercises: list[TemplateExerciseRead]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    days_of_week: list[DayOfWeek] = Field(min_length=1)
    start_date: date
    end_date: date
    override: bool = False

    @model_validator(mode="after")
    def check_date_range(self) -> "ScheduleCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ScheduleEntryRead(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    template_name: str
    day_of_week: DayOfWeek
    start_date: date
    end_date: date


class ScheduleConflict(BaseModel):
    day_of_week: DayOfWeek
    existing_schedule_id: uuid.UUID
    existing_template_id: uuid.UUID
    existing_template_name: str
    start_date: date
    end_date: date
