import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.profile.models import UnitPreference


class ProfileUpsert(BaseModel):
    display_name: str | None = None
    unit_preference: UnitPreference = UnitPreference.METRIC
    date_of_birth: date | None = None
    height_cm: float | None = None


class ProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str | None
    unit_preference: UnitPreference
    date_of_birth: date | None
    height_cm: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
