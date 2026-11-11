from datetime import datetime

from pydantic import Field, field_validator

from app.core import constants
from app.models.enums import TaskPriority, TaskStatus
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
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    project_id: int | None = Field(default=None, gt=0)
    assignee_id: int | None = Field(default=None, gt=0)


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
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assignee_id: int | None = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def validate_title_not_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError(
                constants.MSG_FIELD_CANNOT_BE_NULL.format(field_name="title")
            )
        return value


class TaskResponse(TaskBase):
    id: int
    project_id: int | None = None
    assignee_id: int | None = None
    created_by: int | None = None
    created_at: datetime
