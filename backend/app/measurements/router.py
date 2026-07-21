import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.db import get_db
from app.measurements import service
from app.measurements.schemas import BodyMeasurementIn, BodyMeasurementRead, WeightEntryIn, WeightEntryRead

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.post("/weight", response_model=WeightEntryRead, status_code=status.HTTP_201_CREATED)
async def create_weight_entry(
    payload: WeightEntryIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeightEntryRead:
    return await service.create_weight_entry(db, current_user.id, payload)


@router.get("/weight", response_model=list[WeightEntryRead])
async def list_weight_entries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WeightEntryRead]:
    return await service.list_weight_entries(db, current_user.id)


@router.put("/weight/{entry_id}", response_model=WeightEntryRead)
async def update_weight_entry(
    entry_id: uuid.UUID,
    payload: WeightEntryIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeightEntryRead:
    entry = await service.get_weight_entry(db, current_user.id, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weight entry not found")
    return await service.update_weight_entry(db, entry, payload)


@router.delete("/weight/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weight_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    entry = await service.get_weight_entry(db, current_user.id, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weight entry not found")
    await service.delete_weight_entry(db, entry)


@router.post("/body", response_model=BodyMeasurementRead, status_code=status.HTTP_201_CREATED)
async def create_body_measurement(
    payload: BodyMeasurementIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BodyMeasurementRead:
    return await service.create_body_measurement(db, current_user.id, payload)


@router.get("/body", response_model=list[BodyMeasurementRead])
async def list_body_measurements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BodyMeasurementRead]:
    return await service.list_body_measurements(db, current_user.id)


@router.put("/body/{entry_id}", response_model=BodyMeasurementRead)
async def update_body_measurement(
    entry_id: uuid.UUID,
    payload: BodyMeasurementIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BodyMeasurementRead:
    entry = await service.get_body_measurement(db, current_user.id, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Body measurement not found")
    return await service.update_body_measurement(db, entry, payload)


@router.delete("/body/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_body_measurement(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    entry = await service.get_body_measurement(db, current_user.id, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Body measurement not found")
    await service.delete_body_measurement(db, entry)
