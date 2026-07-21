import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.profile.models import Profile
from app.profile.schemas import ProfileUpsert


async def get_profile(db: AsyncSession, user_id: uuid.UUID) -> Profile | None:
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    return result.scalar_one_or_none()


async def upsert_profile(db: AsyncSession, user_id: uuid.UUID, payload: ProfileUpsert) -> Profile:
    profile = await get_profile(db, user_id)
    if profile is None:
        profile = Profile(user_id=user_id)
        db.add(profile)

    profile.display_name = payload.display_name
    profile.unit_preference = payload.unit_preference
    profile.date_of_birth = payload.date_of_birth
    profile.height_cm = payload.height_cm

    await db.commit()
    await db.refresh(profile)
    return profile
