from datetime import UTC, datetime

from pydantic import Field, field_validator

from app.core import constants, messages
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.base import CoreBaseSchema


def _validate_due_date_not_past(value: datetime | None) -> datetime | None:
    if value is not None:
        check_val = value if value.tzinfo else value.replace(tzinfo=UTC)
        if check_val < datetime.now(UTC):
            raise ValueError("due_date cannot be in the past.")
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
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    project_id: int | None = Field(default=None, gt=0)
    assignee_id: int | None = Field(default=None, gt=0)

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: datetime | None) -> datetime | None:
        return _validate_due_date_not_past(value)


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

    @field_validator("title", "status", "priority")
    @classmethod
    def validate_required_fields_not_null(
        cls, value: str | TaskStatus | TaskPriority | None, info: object
    ) -> str | TaskStatus | TaskPriority:
        field_name = getattr(info, "field_name", "field")
        if value is None:
            raise ValueError(
                messages.MSG_FIELD_CANNOT_BE_NULL.format(field_name=field_name)
            )
        return value

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: datetime | None) -> datetime | None:
        return _validate_due_date_not_past(value)


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    project_id: int | None = None
    assignee_id: int | None = None
    created_by: int | None = None
    created_at: datetime
