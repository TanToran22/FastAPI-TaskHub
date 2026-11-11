from datetime import datetime

from pydantic import Field, field_validator

from app.core import constants
from app.schemas.base import CoreBaseSchema


class TaskBase(CoreBaseSchema):
    title: str = Field(
        ...,
        min_length=constants.TASK_TITLE_MIN_LENGTH,
        max_length=constants.TASK_TITLE_MAX_LENGTH,
    )
    description: str | None = Field(
        default=None,
        max_length=constants.TASK_DESCRIPTION_MAX_LENGTH,
    )


class TaskCreate(TaskBase):
    pass


class TaskUpdate(CoreBaseSchema):
    title: str | None = Field(
        default=None,
        min_length=constants.TASK_TITLE_MIN_LENGTH,
        max_length=constants.TASK_TITLE_MAX_LENGTH,
    )
    description: str | None = Field(
        default=None,
        max_length=constants.TASK_DESCRIPTION_MAX_LENGTH,
    )

    @field_validator("title")
    @classmethod
    def validate_title_not_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError(
                constants.MSG_FIELD_CANNOT_BE_NULL.format(field_name="title")
            )
        return value


class TaskResponse(CoreBaseSchema):
    id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime
