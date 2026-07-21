import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # Nullable so a session survives its source template being deleted later;
    # every create path still requires one (templates-only for MVP1).
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workout_templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    logged_sets: Mapped[list["LoggedSet"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="LoggedSet.logged_at",
    )


class LoggedSet(Base):
    __tablename__ = "logged_sets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workout_sessions.id", ondelete="CASCADE"), index=True)
    # Denormalized snapshot (see app/exercises) — actuals are logged
    # independently of the template's planned values, which can deviate.
    exercise_id: Mapped[str] = mapped_column(String(64))
    exercise_name: Mapped[str] = mapped_column(String(200))
    exercise_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    set_number: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    reps: Mapped[int] = mapped_column(Integer)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session: Mapped["WorkoutSession"] = relationship(back_populates="logged_sets")
