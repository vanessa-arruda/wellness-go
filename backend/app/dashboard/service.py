import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dashboard.schemas import (
    AdherenceDay,
    AdherenceSummary,
    ExerciseVolumeTrend,
    PersonalRecord,
    ScheduledTemplateSummary,
    TodayOverview,
    VolumePoint,
    WorkoutStats,
)
from app.measurements.models import BodyMeasurement, WeightEntry
from app.measurements.schemas import WeightEntryRead
from app.mood.models import MoodEntry
from app.mood.schemas import MoodEntryRead
from app.workout_sessions.models import LoggedSet, WorkoutSession
from app.workout_templates.models import DayOfWeek, ScheduleEntry

_WEEKDAY_ORDER = [
    DayOfWeek.MON,
    DayOfWeek.TUE,
    DayOfWeek.WED,
    DayOfWeek.THU,
    DayOfWeek.FRI,
    DayOfWeek.SAT,
    DayOfWeek.SUN,
]


def _day_of_week_for(d: date) -> DayOfWeek:
    return _WEEKDAY_ORDER[d.weekday()]


def _day_bounds_utc(d: date) -> tuple[datetime, datetime]:
    start = datetime.combine(d, time.min, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


async def get_weight_history(
    db: AsyncSession, user_id: uuid.UUID, start_date: date | None, end_date: date | None
) -> list[WeightEntry]:
    stmt = select(WeightEntry).where(WeightEntry.user_id == user_id)
    if start_date is not None:
        stmt = stmt.where(WeightEntry.recorded_at >= start_date)
    if end_date is not None:
        stmt = stmt.where(WeightEntry.recorded_at <= end_date)
    result = await db.execute(stmt.order_by(WeightEntry.recorded_at.asc()))
    return list(result.scalars().all())


async def get_body_measurement_history(
    db: AsyncSession, user_id: uuid.UUID, start_date: date | None, end_date: date | None
) -> list[BodyMeasurement]:
    stmt = select(BodyMeasurement).where(BodyMeasurement.user_id == user_id)
    if start_date is not None:
        stmt = stmt.where(BodyMeasurement.recorded_at >= start_date)
    if end_date is not None:
        stmt = stmt.where(BodyMeasurement.recorded_at <= end_date)
    result = await db.execute(stmt.order_by(BodyMeasurement.recorded_at.asc()))
    return list(result.scalars().all())


async def get_mood_history(
    db: AsyncSession, user_id: uuid.UUID, start_date: date | None, end_date: date | None
) -> list[MoodEntry]:
    stmt = select(MoodEntry).where(MoodEntry.user_id == user_id)
    if start_date is not None:
        stmt = stmt.where(MoodEntry.recorded_at >= start_date)
    if end_date is not None:
        stmt = stmt.where(MoodEntry.recorded_at <= end_date)
    result = await db.execute(stmt.order_by(MoodEntry.recorded_at.asc()))
    return list(result.scalars().all())


async def get_workout_session_history(
    db: AsyncSession, user_id: uuid.UUID, start_date: date | None, end_date: date | None
) -> list[WorkoutSession]:
    stmt = (
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user_id)
        .options(selectinload(WorkoutSession.logged_sets))
    )
    if start_date is not None:
        stmt = stmt.where(WorkoutSession.started_at >= _day_bounds_utc(start_date)[0])
    if end_date is not None:
        stmt = stmt.where(WorkoutSession.started_at < _day_bounds_utc(end_date)[1])
    result = await db.execute(stmt.order_by(WorkoutSession.started_at.asc()))
    return list(result.scalars().all())


async def get_today_overview(db: AsyncSession, user_id: uuid.UUID) -> TodayOverview:
    today = datetime.now(timezone.utc).date()
    dow = _day_of_week_for(today)

    schedule_result = await db.execute(
        select(ScheduleEntry)
        .where(
            ScheduleEntry.user_id == user_id,
            ScheduleEntry.day_of_week == dow,
            ScheduleEntry.start_date <= today,
            ScheduleEntry.end_date >= today,
        )
        .options(selectinload(ScheduleEntry.template))
    )
    scheduled = [
        ScheduledTemplateSummary(
            schedule_entry_id=entry.id, template_id=entry.template_id, template_name=entry.template.name
        )
        for entry in schedule_result.scalars().all()
    ]

    today_start, today_end = _day_bounds_utc(today)
    session_result = await db.execute(
        select(WorkoutSession.id)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.finished_at.is_not(None),
            WorkoutSession.finished_at >= today_start,
            WorkoutSession.finished_at < today_end,
        )
        .limit(1)
    )
    session_completed_today = session_result.scalar_one_or_none() is not None

    mood_result = await db.execute(
        select(MoodEntry).where(MoodEntry.user_id == user_id, MoodEntry.recorded_at == today)
    )
    mood_entry = mood_result.scalar_one_or_none()

    weight_result = await db.execute(
        select(WeightEntry).where(WeightEntry.user_id == user_id).order_by(WeightEntry.recorded_at.desc()).limit(1)
    )
    latest_weight = weight_result.scalar_one_or_none()

    return TodayOverview(
        date=today,
        scheduled=scheduled,
        session_completed_today=session_completed_today,
        mood=MoodEntryRead.model_validate(mood_entry) if mood_entry else None,
        latest_weight=WeightEntryRead.model_validate(latest_weight) if latest_weight else None,
    )


async def get_workout_stats(
    db: AsyncSession, user_id: uuid.UUID, start_date: date, end_date: date
) -> WorkoutStats:
    start_dt, _ = _day_bounds_utc(start_date)
    _, end_dt = _day_bounds_utc(end_date)

    result = await db.execute(
        select(WorkoutSession)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.finished_at.is_not(None),
            WorkoutSession.finished_at >= start_dt,
            WorkoutSession.finished_at < end_dt,
        )
        .options(selectinload(WorkoutSession.logged_sets))
    )
    sessions = list(result.scalars().all())

    sessions_count = len(sessions)
    days_in_range = (end_date - start_date).days + 1
    sessions_per_week = sessions_count / (days_in_range / 7)

    volume_by_exercise: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    exercise_names: dict[str, str] = {}

    for session in sessions:
        session_date = session.finished_at.date()  # type: ignore[union-attr]
        for logged_set in session.logged_sets:
            weight = float(logged_set.weight) if logged_set.weight is not None else 0.0
            volume_by_exercise[logged_set.exercise_id][session_date] += weight * logged_set.reps
            exercise_names[logged_set.exercise_id] = logged_set.exercise_name

    exercise_volume_trend = [
        ExerciseVolumeTrend(
            exercise_id=exercise_id,
            exercise_name=exercise_names[exercise_id],
            points=[VolumePoint(date=d, volume=v) for d, v in sorted(date_volumes.items())],
        )
        for exercise_id, date_volumes in volume_by_exercise.items()
    ]

    return WorkoutStats(
        start_date=start_date,
        end_date=end_date,
        sessions_count=sessions_count,
        sessions_per_week=round(sessions_per_week, 2),
        exercise_volume_trend=exercise_volume_trend,
    )


async def get_personal_records(db: AsyncSession, user_id: uuid.UUID) -> list[PersonalRecord]:
    result = await db.execute(
        select(LoggedSet, WorkoutSession.started_at)
        .join(WorkoutSession, WorkoutSession.id == LoggedSet.session_id)
        .where(WorkoutSession.user_id == user_id)
    )
    rows = result.all()

    best_weight: dict[str, tuple[float, int, date, str]] = {}
    best_reps: dict[str, tuple[int, date, str]] = {}

    for logged_set, started_at in rows:
        exercise_id = logged_set.exercise_id
        exercise_name = logged_set.exercise_name
        set_date = started_at.date()
        weight = float(logged_set.weight) if logged_set.weight is not None else None

        if weight is not None:
            current = best_weight.get(exercise_id)
            if current is None or weight > current[0]:
                best_weight[exercise_id] = (weight, logged_set.reps, set_date, exercise_name)

        current_reps = best_reps.get(exercise_id)
        if current_reps is None or logged_set.reps > current_reps[0]:
            best_reps[exercise_id] = (logged_set.reps, set_date, exercise_name)

    records = []
    for exercise_id in set(best_weight) | set(best_reps):
        weight_entry = best_weight.get(exercise_id)
        reps_entry = best_reps.get(exercise_id)
        name = (weight_entry[3] if weight_entry else None) or (reps_entry[2] if reps_entry else "")
        records.append(
            PersonalRecord(
                exercise_id=exercise_id,
                exercise_name=name,
                max_weight=weight_entry[0] if weight_entry else None,
                reps_at_max_weight=weight_entry[1] if weight_entry else None,
                max_weight_achieved_at=weight_entry[2] if weight_entry else None,
                max_reps=reps_entry[0] if reps_entry else None,
                max_reps_achieved_at=reps_entry[1] if reps_entry else None,
            )
        )
    records.sort(key=lambda r: r.exercise_name)
    return records


async def get_adherence(db: AsyncSession, user_id: uuid.UUID, start_date: date, end_date: date) -> AdherenceSummary:
    entries_result = await db.execute(
        select(ScheduleEntry)
        .where(
            ScheduleEntry.user_id == user_id,
            ScheduleEntry.start_date <= end_date,
            ScheduleEntry.end_date >= start_date,
        )
        .options(selectinload(ScheduleEntry.template))
    )
    entries = list(entries_result.scalars().all())

    scheduled_days: dict[date, ScheduleEntry] = {}
    for entry in entries:
        current = max(entry.start_date, start_date)
        range_end = min(entry.end_date, end_date)
        while current <= range_end:
            if _day_of_week_for(current) == entry.day_of_week:
                scheduled_days[current] = entry
            current += timedelta(days=1)

    if not scheduled_days:
        return AdherenceSummary(
            start_date=start_date,
            end_date=end_date,
            scheduled_count=0,
            completed_count=0,
            adherence_percentage=0.0,
            days=[],
        )

    start_dt, _ = _day_bounds_utc(start_date)
    _, end_dt = _day_bounds_utc(end_date)
    sessions_result = await db.execute(
        select(WorkoutSession.finished_at).where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.finished_at.is_not(None),
            WorkoutSession.finished_at >= start_dt,
            WorkoutSession.finished_at < end_dt,
        )
    )
    completed_dates = {row[0].date() for row in sessions_result.all()}

    days = [
        AdherenceDay(
            date=d,
            scheduled_template_id=entry.template_id,
            scheduled_template_name=entry.template.name,
            completed=d in completed_dates,
        )
        for d, entry in sorted(scheduled_days.items())
    ]
    completed_count = sum(1 for day in days if day.completed)
    scheduled_count = len(days)
    percentage = (completed_count / scheduled_count * 100) if scheduled_count else 0.0

    return AdherenceSummary(
        start_date=start_date,
        end_date=end_date,
        scheduled_count=scheduled_count,
        completed_count=completed_count,
        adherence_percentage=round(percentage, 1),
        days=days,
    )
