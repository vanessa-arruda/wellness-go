import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class MoodTag(str, enum.Enum):
    # Positive
    JOYFUL = "joyful"
    PEACEFUL = "peaceful"
    HOPEFUL = "hopeful"
    ENERGETIC = "energetic"
    CONFIDENT = "confident"
    # Reflective
    NOSTALGIC = "nostalgic"
    CONTEMPLATIVE = "contemplative"
    INSPIRED = "inspired"
    RELIEVED = "relieved"
    CURIOUS = "curious"
    # Negative
    ANXIOUS = "anxious"
    FRUSTRATED = "frustrated"
    GLOOMY = "gloomy"
    TENSE = "tense"
    IRRITABLE = "irritable"


class MoodEntry(Base):
    __tablename__ = "mood_entries"
    __table_args__ = (UniqueConstraint("user_id", "recorded_at", name="uq_mood_entries_user_date"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    moods: Mapped[list[MoodTag]] = mapped_column(ARRAY(Enum(MoodTag, name="mood_tag")))
    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    recorded_at: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
