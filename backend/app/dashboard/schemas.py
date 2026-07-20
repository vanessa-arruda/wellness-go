import uuid
from datetime import date

from pydantic import BaseModel

from app.measurements.schemas import WeightEntryRead
from app.mood.schemas import MoodEntryRead


class ScheduledTemplateSummary(BaseModel):
    schedule_entry_id: uuid.UUID
    template_id: uuid.UUID
    template_name: str


class TodayOverview(BaseModel):
    date: date
    scheduled: list[ScheduledTemplateSummary]
    session_completed_today: bool
    mood: MoodEntryRead | None
    latest_weight: WeightEntryRead | None


class VolumePoint(BaseModel):
    date: date
    volume: float


class ExerciseVolumeTrend(BaseModel):
    exercise_id: str
    exercise_name: str
    points: list[VolumePoint]


class WorkoutStats(BaseModel):
    start_date: date
    end_date: date
    sessions_count: int
    sessions_per_week: float
    exercise_volume_trend: list[ExerciseVolumeTrend]


class PersonalRecord(BaseModel):
    exercise_id: str
    exercise_name: str
    max_weight: float | None
    reps_at_max_weight: int | None
    max_weight_achieved_at: date | None
    max_reps: int | None
    max_reps_achieved_at: date | None


class AdherenceDay(BaseModel):
    date: date
    scheduled_template_id: uuid.UUID
    scheduled_template_name: str
    completed: bool


class AdherenceSummary(BaseModel):
    start_date: date
    end_date: date
    scheduled_count: int
    completed_count: int
    adherence_percentage: float
    days: list[AdherenceDay]
