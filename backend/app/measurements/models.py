import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class WeightEntry(Base):
    __tablename__ = "weight_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    weight_kg: Mapped[float] = mapped_column(Numeric(5, 2))
    recorded_at: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recorded_at: Mapped[date] = mapped_column(Date)
    neck_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    chest_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    navel_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    hips_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    left_arm_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    right_arm_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    left_thigh_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    right_thigh_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    left_calf_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    right_calf_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
