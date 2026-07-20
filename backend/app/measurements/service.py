import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.measurements.models import BodyMeasurement, WeightEntry
from app.measurements.schemas import BodyMeasurementIn, WeightEntryIn


async def list_weight_entries(db: AsyncSession, user_id: uuid.UUID) -> list[WeightEntry]:
    result = await db.execute(
        select(WeightEntry).where(WeightEntry.user_id == user_id).order_by(WeightEntry.recorded_at.desc())
    )
    return list(result.scalars().all())


async def get_weight_entry(db: AsyncSession, user_id: uuid.UUID, entry_id: uuid.UUID) -> WeightEntry | None:
    result = await db.execute(select(WeightEntry).where(WeightEntry.id == entry_id, WeightEntry.user_id == user_id))
    return result.scalar_one_or_none()


async def create_weight_entry(db: AsyncSession, user_id: uuid.UUID, payload: WeightEntryIn) -> WeightEntry:
    entry = WeightEntry(user_id=user_id, weight_kg=payload.weight_kg, recorded_at=payload.recorded_at)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def update_weight_entry(db: AsyncSession, entry: WeightEntry, payload: WeightEntryIn) -> WeightEntry:
    entry.weight_kg = payload.weight_kg
    entry.recorded_at = payload.recorded_at
    await db.commit()
    await db.refresh(entry)
    return entry


async def delete_weight_entry(db: AsyncSession, entry: WeightEntry) -> None:
    await db.delete(entry)
    await db.commit()


async def list_body_measurements(db: AsyncSession, user_id: uuid.UUID) -> list[BodyMeasurement]:
    result = await db.execute(
        select(BodyMeasurement).where(BodyMeasurement.user_id == user_id).order_by(BodyMeasurement.recorded_at.desc())
    )
    return list(result.scalars().all())


async def get_body_measurement(db: AsyncSession, user_id: uuid.UUID, entry_id: uuid.UUID) -> BodyMeasurement | None:
    result = await db.execute(
        select(BodyMeasurement).where(BodyMeasurement.id == entry_id, BodyMeasurement.user_id == user_id)
    )
    return result.scalar_one_or_none()


def _apply_body_measurement_fields(entry: BodyMeasurement, payload: BodyMeasurementIn) -> None:
    entry.recorded_at = payload.recorded_at
    entry.neck_cm = payload.neck_cm
    entry.chest_cm = payload.chest_cm
    entry.waist_cm = payload.waist_cm
    entry.navel_cm = payload.navel_cm
    entry.hips_cm = payload.hips_cm
    entry.left_arm_cm = payload.left_arm_cm
    entry.right_arm_cm = payload.right_arm_cm
    entry.left_thigh_cm = payload.left_thigh_cm
    entry.right_thigh_cm = payload.right_thigh_cm
    entry.left_calf_cm = payload.left_calf_cm
    entry.right_calf_cm = payload.right_calf_cm


async def create_body_measurement(db: AsyncSession, user_id: uuid.UUID, payload: BodyMeasurementIn) -> BodyMeasurement:
    entry = BodyMeasurement(user_id=user_id)
    _apply_body_measurement_fields(entry, payload)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def update_body_measurement(
    db: AsyncSession, entry: BodyMeasurement, payload: BodyMeasurementIn
) -> BodyMeasurement:
    _apply_body_measurement_fields(entry, payload)
    await db.commit()
    await db.refresh(entry)
    return entry


async def delete_body_measurement(db: AsyncSession, entry: BodyMeasurement) -> None:
    await db.delete(entry)
    await db.commit()
