from pydantic import BaseModel, ConfigDict, Field


class ExerciseSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    exercise_id: str = Field(alias="exerciseId")
    name: str
    image_url: str | None = Field(default=None, alias="imageUrl")
    body_parts: list[str] = Field(default_factory=list, alias="bodyParts")
    equipments: list[str] = Field(default_factory=list)
    exercise_type: str | None = Field(default=None, alias="exerciseType")
    target_muscles: list[str] = Field(default_factory=list, alias="targetMuscles")
    secondary_muscles: list[str] = Field(default_factory=list, alias="secondaryMuscles")
    keywords: list[str] = Field(default_factory=list)


class ExerciseDetail(ExerciseSummary):
    video_url: str | None = Field(default=None, alias="videoUrl")
    overview: str | None = None
    instructions: list[str] = Field(default_factory=list)
    exercise_tips: list[str] = Field(default_factory=list, alias="exerciseTips")
    variations: list[str] = Field(default_factory=list)
    related_exercise_ids: list[str] = Field(default_factory=list, alias="relatedExerciseIds")


class PageMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int
    has_next_page: bool = Field(alias="hasNextPage")
    has_previous_page: bool = Field(alias="hasPreviousPage")
    next_cursor: str | None = Field(default=None, alias="nextCursor")


class ExercisePage(BaseModel):
    meta: PageMeta
    items: list[ExerciseSummary]


class ReferenceItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    image_url: str | None = Field(default=None, alias="imageUrl")
