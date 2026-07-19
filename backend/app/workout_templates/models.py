import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class DayOfWeek(str, enum.Enum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    exercises: Mapped[list["TemplateExercise"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateExercise.position",
    )


class TemplateExercise(Base):
    __tablename__ = "template_exercises"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_templates.id", ondelete="CASCADE"), index=True
    )
    # Denormalized snapshot of the ExerciseDB exercise (see app/exercises) —
    # there's no local exercises table to foreign-key against.
    exercise_id: Mapped[str] = mapped_column(String(64))
    exercise_name: Mapped[str] = mapped_column(String(200))
    exercise_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    target_sets: Mapped[int] = mapped_column(Integer)
    target_reps: Mapped[int] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer)

    template: Mapped["WorkoutTemplate"] = relationship(back_populates="exercises")


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_templates.id", ondelete="CASCADE"), index=True
    )
    day_of_week: Mapped[DayOfWeek] = mapped_column(Enum(DayOfWeek, name="day_of_week"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    template: Mapped["WorkoutTemplate"] = relationship()
