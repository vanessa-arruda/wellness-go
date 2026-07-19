from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import router as auth_router
from app.core.db import get_db
from app.exercises.router import router as exercises_router
from app.measurements.router import router as measurements_router
from app.mood.router import router as mood_router
from app.profile.router import router as profile_router
from app.workout_sessions.router import router as workout_sessions_router
from app.workout_templates.router import router as workout_templates_router

app = FastAPI(title="wellness-go")

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(exercises_router)
app.include_router(workout_templates_router)
app.include_router(workout_sessions_router)
app.include_router(measurements_router)
app.include_router(mood_router)


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}
