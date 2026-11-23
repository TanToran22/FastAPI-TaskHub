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
    status: ProjectStatus | None = None

    @field_validator("name", "status")
    @classmethod
    def validate_required_fields_not_null(
        cls, value: str | ProjectStatus | None, info: object
    ) -> str | ProjectStatus:
        field_name = getattr(info, "field_name", "field")
        if value is None:
            raise ValueError(
                messages.MSG_FIELD_CANNOT_BE_NULL.format(field_name=field_name)
            )
        return value


class ProjectResponse(ProjectBase):
    id: int
    workspace_id: int
    status: ProjectStatus
    created_at: datetime
