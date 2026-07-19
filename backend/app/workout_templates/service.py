import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.workout_templates.models import DayOfWeek, ScheduleEntry, TemplateExercise, WorkoutTemplate
from app.workout_templates.schemas import ScheduleConflict, ScheduleCreate, TemplateUpsert


async def list_templates(db: AsyncSession, user_id: uuid.UUID) -> list[WorkoutTemplate]:
    result = await db.execute(
        select(WorkoutTemplate)
        .where(WorkoutTemplate.user_id == user_id)
        .options(selectinload(WorkoutTemplate.exercises))
        .order_by(WorkoutTemplate.created_at)
    )
    return list(result.scalars().all())


async def get_template(db: AsyncSession, user_id: uuid.UUID, template_id: uuid.UUID) -> WorkoutTemplate | None:
    result = await db.execute(
        select(WorkoutTemplate)
        .where(WorkoutTemplate.id == template_id, WorkoutTemplate.user_id == user_id)
        .options(selectinload(WorkoutTemplate.exercises))
    )
    return result.scalar_one_or_none()


def _build_exercise_rows(payload: TemplateUpsert) -> list[TemplateExercise]:
    return [
        TemplateExercise(
            exercise_id=ex.exercise_id,
            exercise_name=ex.exercise_name,
            exercise_image_url=ex.exercise_image_url,
            target_sets=ex.target_sets,
            target_reps=ex.target_reps,
            position=position,
        )
        for position, ex in enumerate(payload.exercises)
    ]


async def create_template(db: AsyncSession, user_id: uuid.UUID, payload: TemplateUpsert) -> WorkoutTemplate:
    template = WorkoutTemplate(user_id=user_id, name=payload.name, exercises=_build_exercise_rows(payload))
    db.add(template)
    await db.commit()
    return await get_template(db, user_id, template.id)  # type: ignore[return-value]


async def update_template(db: AsyncSession, template: WorkoutTemplate, payload: TemplateUpsert) -> WorkoutTemplate:
    template.name = payload.name
    template.exercises = _build_exercise_rows(payload)
    await db.commit()
    return await get_template(db, template.user_id, template.id)  # type: ignore[return-value]


async def delete_template(db: AsyncSession, template: WorkoutTemplate) -> None:
    await db.delete(template)
    await db.commit()


async def _find_conflicts(
    db: AsyncSession,
    user_id: uuid.UUID,
    days: list[DayOfWeek],
    start: date,
    end: date,
) -> list[ScheduleEntry]:
    result = await db.execute(
        select(ScheduleEntry)
        .where(
            ScheduleEntry.user_id == user_id,
            ScheduleEntry.day_of_week.in_(days),
            ScheduleEntry.start_date <= end,
            ScheduleEntry.end_date >= start,
        )
        .options(selectinload(ScheduleEntry.template))
    )
    return list(result.scalars().all())


async def _entries_by_ids(db: AsyncSession, entry_ids: list[uuid.UUID]) -> list[ScheduleEntry]:
    result = await db.execute(
        select(ScheduleEntry)
        .where(ScheduleEntry.id.in_(entry_ids))
        .options(selectinload(ScheduleEntry.template))
    )
    return list(result.scalars().all())


async def create_schedule(
    db: AsyncSession, user_id: uuid.UUID, template_id: uuid.UUID, payload: ScheduleCreate
) -> tuple[list[ScheduleEntry], list[ScheduleConflict]]:
    conflicts = await _find_conflicts(db, user_id, payload.days_of_week, payload.start_date, payload.end_date)

    if conflicts and not payload.override:
        return [], [
            ScheduleConflict(
                day_of_week=c.day_of_week,
                existing_schedule_id=c.id,
                existing_template_id=c.template_id,
                existing_template_name=c.template.name,
                start_date=c.start_date,
                end_date=c.end_date,
            )
            for c in conflicts
        ]

    for c in conflicts:
        # Don't blindly delete: preserve the parts of the conflicting entry
        # that fall outside the new range (e.g. replacing Mondays going
        # forward should keep past Mondays' history intact).
        if c.start_date < payload.start_date:
            db.add(
                ScheduleEntry(
                    user_id=user_id,
                    template_id=c.template_id,
                    day_of_week=c.day_of_week,
                    start_date=c.start_date,
                    end_date=payload.start_date - timedelta(days=1),
                )
            )
        if c.end_date > payload.end_date:
            db.add(
                ScheduleEntry(
                    user_id=user_id,
                    template_id=c.template_id,
                    day_of_week=c.day_of_week,
                    start_date=payload.end_date + timedelta(days=1),
                    end_date=c.end_date,
                )
            )
        await db.delete(c)

    new_entries = [
        ScheduleEntry(
            user_id=user_id,
            template_id=template_id,
            day_of_week=day,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        for day in payload.days_of_week
    ]
    db.add_all(new_entries)
    await db.commit()

    return await _entries_by_ids(db, [e.id for e in new_entries]), []


async def list_schedule(db: AsyncSession, user_id: uuid.UUID) -> list[ScheduleEntry]:
    result = await db.execute(
        select(ScheduleEntry)
        .where(ScheduleEntry.user_id == user_id)
        .options(selectinload(ScheduleEntry.template))
        .order_by(ScheduleEntry.start_date)
    )
    return list(result.scalars().all())


async def get_schedule_entry(db: AsyncSession, user_id: uuid.UUID, entry_id: uuid.UUID) -> ScheduleEntry | None:
    result = await db.execute(
        select(ScheduleEntry).where(ScheduleEntry.id == entry_id, ScheduleEntry.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def delete_schedule_entry(db: AsyncSession, entry: ScheduleEntry) -> None:
    await db.delete(entry)
    await db.commit()
