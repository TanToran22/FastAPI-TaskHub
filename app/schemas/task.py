from datetime import datetime

from pydantic import Field, field_validator

from app.core import constants, messages
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.base import CoreBaseSchema, PaginatedResponse


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
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: datetime | None = Field(default=None)
    project_id: int | None = Field(default=None, gt=0)
    assignee_id: int | None = Field(default=None, gt=0)


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
    status: TaskStatus | None = Field(default=None)
    priority: TaskPriority | None = Field(default=None)
    due_date: datetime | None = Field(default=None)
    project_id: int | None = Field(default=None, gt=0)
    assignee_id: int | None = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def validate_title_not_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError(
                messages.MSG_FIELD_CANNOT_BE_NULL.format(field_name="title")
            )
        return value


class TaskResponse(TaskBase):
    id: int
    created_by: int | None = None
    created_at: datetime


TaskListResponse = PaginatedResponse[TaskResponse]
