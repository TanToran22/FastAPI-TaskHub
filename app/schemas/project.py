from datetime import datetime

from pydantic import Field, field_validator

from app.core import constants, messages
from app.models.enums import ProjectStatus
from app.schemas.base import CoreBaseSchema


class ProjectBase(CoreBaseSchema):
    name: str = Field(
        ...,
        min_length=constants.PROJECT_NAME_MIN_LENGTH,
        max_length=constants.PROJECT_NAME_MAX_LENGTH,
    )
    description: str | None = Field(
        default=None,
        max_length=constants.PROJECT_DESCRIPTION_MAX_LENGTH,
    )


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(CoreBaseSchema):
    name: str | None = Field(
        default=None,
        min_length=constants.PROJECT_NAME_MIN_LENGTH,
        max_length=constants.PROJECT_NAME_MAX_LENGTH,
    )
    description: str | None = Field(
        default=None,
        max_length=constants.PROJECT_DESCRIPTION_MAX_LENGTH,
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError(
                messages.MSG_FIELD_CANNOT_BE_NULL.format(field_name="name")
            )
        return value


class ProjectResponse(ProjectBase):
    id: int
    workspace_id: int
    status: ProjectStatus
    created_at: datetime
