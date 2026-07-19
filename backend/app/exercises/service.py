from app.exercises import client
from app.exercises.schemas import ExerciseDetail, ExercisePage, ExerciseSummary, PageMeta, ReferenceItem


async def get_exercises(
    name: str | None = None, keywords: str | None = None, cursor: str | None = None
) -> ExercisePage:
    body = await client.list_exercises(name=name, keywords=keywords, cursor=cursor)
    return ExercisePage(
        meta=PageMeta.model_validate(body["meta"]),
        items=[ExerciseSummary.model_validate(item) for item in body["data"]],
    )


async def search_exercises(query: str) -> list[ExerciseSummary]:
    body = await client.search_exercises(query)
    return [ExerciseSummary.model_validate(item) for item in body["data"]]


async def get_exercise(exercise_id: str) -> ExerciseDetail:
    body = await client.get_exercise(exercise_id)
    return ExerciseDetail.model_validate(body["data"])


async def get_body_parts() -> list[ReferenceItem]:
    body = await client.list_body_parts()
    return [ReferenceItem.model_validate(item) for item in body["data"]]


async def get_equipments() -> list[ReferenceItem]:
    body = await client.list_equipments()
    return [ReferenceItem.model_validate(item) for item in body["data"]]


async def get_muscles() -> list[ReferenceItem]:
    body = await client.list_muscles()
    return [ReferenceItem.model_validate(item) for item in body["data"]]


async def get_exercise_types() -> list[ReferenceItem]:
    body = await client.list_exercise_types()
    return [ReferenceItem.model_validate(item) for item in body["data"]]
