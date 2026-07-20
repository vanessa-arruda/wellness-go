import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.db import get_db
from app.dashboard import service
from app.dashboard.schemas import AdherenceSummary, PersonalRecord, TodayOverview, WorkoutStats
from app.measurements.schemas import BodyMeasurementRead, WeightEntryRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Formula-trigger characters per OWASP's CSV Injection guidance. A leading
# apostrophe neutralizes them in spreadsheet apps without altering the
# visible value.
_FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_csv_cell(value: object) -> object:
    if isinstance(value, str) and value.startswith(_FORMULA_TRIGGER_CHARS):
        return "'" + value
    return value


def _csv_response(filename: str, header: list[str], rows: list[list]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows([_sanitize_csv_cell(cell) for cell in row] for row in rows)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/weight-history", response_model=list[WeightEntryRead])
async def weight_history(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WeightEntryRead]:
    return await service.get_weight_history(db, current_user.id, start_date, end_date)


@router.get("/body-measurement-history", response_model=list[BodyMeasurementRead])
async def body_measurement_history(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BodyMeasurementRead]:
    return await service.get_body_measurement_history(db, current_user.id, start_date, end_date)


@router.get("/today", response_model=TodayOverview)
async def today_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TodayOverview:
    return await service.get_today_overview(db, current_user.id)


@router.get("/workout-stats", response_model=WorkoutStats)
async def workout_stats(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkoutStats:
    return await service.get_workout_stats(db, current_user.id, start_date, end_date)


@router.get("/personal-records", response_model=list[PersonalRecord])
async def personal_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PersonalRecord]:
    return await service.get_personal_records(db, current_user.id)


@router.get("/adherence", response_model=AdherenceSummary)
async def adherence(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdherenceSummary:
    return await service.get_adherence(db, current_user.id, start_date, end_date)


@router.get("/export/weight.csv")
async def export_weight_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    entries = await service.get_weight_history(db, current_user.id, None, None)
    rows = [[e.recorded_at.isoformat(), e.weight_kg] for e in entries]
    return _csv_response("weight.csv", ["recorded_at", "weight_kg"], rows)


@router.get("/export/body-measurements.csv")
async def export_body_measurements_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    entries = await service.get_body_measurement_history(db, current_user.id, None, None)
    header = [
        "recorded_at",
        "neck_cm",
        "chest_cm",
        "waist_cm",
        "navel_cm",
        "hips_cm",
        "left_arm_cm",
        "right_arm_cm",
        "left_thigh_cm",
        "right_thigh_cm",
        "left_calf_cm",
        "right_calf_cm",
    ]
    rows = [
        [
            e.recorded_at.isoformat(),
            e.neck_cm,
            e.chest_cm,
            e.waist_cm,
            e.navel_cm,
            e.hips_cm,
            e.left_arm_cm,
            e.right_arm_cm,
            e.left_thigh_cm,
            e.right_thigh_cm,
            e.left_calf_cm,
            e.right_calf_cm,
        ]
        for e in entries
    ]
    return _csv_response("body-measurements.csv", header, rows)


@router.get("/export/mood.csv")
async def export_mood_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    entries = await service.get_mood_history(db, current_user.id, None, None)
    rows = [[e.recorded_at.isoformat(), "|".join(m.value for m in e.moods), e.note or ""] for e in entries]
    return _csv_response("mood.csv", ["recorded_at", "moods", "note"], rows)


@router.get("/export/workout-sessions.csv")
async def export_workout_sessions_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    sessions = await service.get_workout_session_history(db, current_user.id, None, None)
    header = [
        "session_id",
        "started_at",
        "finished_at",
        "exercise_id",
        "exercise_name",
        "set_number",
        "weight",
        "reps",
        "logged_at",
    ]
    rows = []
    for session in sessions:
        if not session.logged_sets:
            rows.append(
                [
                    str(session.id),
                    session.started_at.isoformat(),
                    session.finished_at.isoformat() if session.finished_at else "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
            continue
        for logged_set in session.logged_sets:
            rows.append(
                [
                    str(session.id),
                    session.started_at.isoformat(),
                    session.finished_at.isoformat() if session.finished_at else "",
                    logged_set.exercise_id,
                    logged_set.exercise_name,
                    logged_set.set_number,
                    logged_set.weight,
                    logged_set.reps,
                    logged_set.logged_at.isoformat(),
                ]
            )
    return _csv_response("workout-sessions.csv", header, rows)
