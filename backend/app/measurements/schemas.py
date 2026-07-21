import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class WeightEntryIn(BaseModel):
    weight_kg: float = Field(gt=0)
    recorded_at: date


class WeightEntryRead(BaseModel):
    id: uuid.UUID
    weight_kg: float
    recorded_at: date
    created_at: datetime

    model_config = {"from_attributes": True}


class BodyMeasurementIn(BaseModel):
    recorded_at: date
    neck_cm: float | None = Field(default=None, gt=0)
    chest_cm: float | None = Field(default=None, gt=0)
    waist_cm: float | None = Field(default=None, gt=0)
    navel_cm: float | None = Field(default=None, gt=0)
    hips_cm: float | None = Field(default=None, gt=0)
    left_arm_cm: float | None = Field(default=None, gt=0)
    right_arm_cm: float | None = Field(default=None, gt=0)
    left_thigh_cm: float | None = Field(default=None, gt=0)
    right_thigh_cm: float | None = Field(default=None, gt=0)
    left_calf_cm: float | None = Field(default=None, gt=0)
    right_calf_cm: float | None = Field(default=None, gt=0)


class BodyMeasurementRead(BodyMeasurementIn):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
