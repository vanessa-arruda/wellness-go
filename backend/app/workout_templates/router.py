import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.db import get_db
from app.workout_templates import service
from app.workout_templates.models import ScheduleEntry
from app.workout_templates.schemas import ScheduleCreate, ScheduleEntryRead, TemplateRead, TemplateUpsert

router = APIRouter(prefix="/workout-templates", tags=["workout-templates"])


def _to_schedule_read(entry: ScheduleEntry) -> ScheduleEntryRead:
    return ScheduleEntryRead(
        id=entry.id,
        template_id=entry.template_id,
        template_name=entry.template.name,
        day_of_week=entry.day_of_week,
        start_date=entry.start_date,
        end_date=entry.end_date,
    )


@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: TemplateUpsert,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TemplateRead:
    return await service.create_template(db, current_user.id, payload)


@router.get("", response_model=list[TemplateRead])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TemplateRead]:
    return await service.list_templates(db, current_user.id)


@router.get("/schedule", response_model=list[ScheduleEntryRead])
async def get_my_schedule(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleEntryRead]:
    entries = await service.list_schedule(db, current_user.id)
    return [_to_schedule_read(entry) for entry in entries]


@router.delete("/schedule/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    entry = await service.get_schedule_entry(db, current_user.id, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule entry not found")
    await service.delete_schedule_entry(db, entry)


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TemplateRead:
    template = await service.get_template(db, current_user.id, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.put("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: uuid.UUID,
    payload: TemplateUpsert,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TemplateRead:
    template = await service.get_template(db, current_user.id, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return await service.update_template(db, template, payload)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    template = await service.get_template(db, current_user.id, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    await service.delete_template(db, template)


@router.post("/{template_id}/schedule", response_model=list[ScheduleEntryRead], status_code=status.HTTP_201_CREATED)
async def create_schedule(
    template_id: uuid.UUID,
    payload: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleEntryRead]:
    template = await service.get_template(db, current_user.id, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    entries, conflicts = await service.create_schedule(db, current_user.id, template_id, payload)
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "There's already another workout scheduled for this date. Override?",
                "conflicts": [c.model_dump(mode="json") for c in conflicts],
            },
        )
    return [_to_schedule_read(entry) for entry in entries]
