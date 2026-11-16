from datetime import UTC, datetime

from pydantic import Field, ValidationInfo, field_validator

from app.core import constants, messages
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.base import CoreBaseSchema, PaginatedResponse


def _ensure_future_or_present(value: datetime | None) -> datetime | None:
    if value is None:
        return value
    now = datetime.now(UTC)
    target = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if target < now:
        raise ValueError(messages.MSG_DUE_DATE_IN_PAST)
    return value


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
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: datetime | None = Field(default=None)
    project_id: int | None = Field(default=None, gt=0)
    assignee_id: int | None = Field(default=None, gt=0)

    @field_validator("due_date")
    @classmethod
    def validate_due_date_not_past(cls, value: datetime | None) -> datetime | None:
        return _ensure_future_or_present(value)


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

    @field_validator("title", "status", "priority")
    @classmethod
    def validate_required_fields_not_null(
        cls,
        value: str | TaskStatus | TaskPriority | None,
        info: ValidationInfo,
    ) -> str | TaskStatus | TaskPriority:
        if value is None:
            raise ValueError(
                messages.MSG_FIELD_CANNOT_BE_NULL.format(field_name=info.field_name)
            )
        return value

    @field_validator("due_date")
    @classmethod
    def validate_due_date_not_past(cls, value: datetime | None) -> datetime | None:
        return _ensure_future_or_present(value)


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    created_by: int | None = None
    created_at: datetime


TaskListResponse = PaginatedResponse[TaskResponse]
