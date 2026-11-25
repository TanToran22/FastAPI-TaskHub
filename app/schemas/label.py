from pydantic import Field, field_validator

from app.core import constants, messages
from app.schemas.base import CoreBaseSchema


class LabelBase(CoreBaseSchema):
    name: str = Field(
        ...,
        min_length=constants.LABEL_NAME_MIN_LENGTH,
        max_length=constants.LABEL_NAME_MAX_LENGTH,
    )
    color: str = Field(
        default=constants.DEFAULT_LABEL_COLOR,
        min_length=constants.LABEL_COLOR_MIN_LENGTH,
        max_length=constants.LABEL_COLOR_MAX_LENGTH,
    )


class LabelCreate(LabelBase):
    pass


class LabelUpdate(CoreBaseSchema):
    name: str | None = Field(
        default=None,
        min_length=constants.LABEL_NAME_MIN_LENGTH,
        max_length=constants.LABEL_NAME_MAX_LENGTH,
    )
    color: str | None = Field(
        default=None,
        min_length=constants.LABEL_COLOR_MIN_LENGTH,
        max_length=constants.LABEL_COLOR_MAX_LENGTH,
    )

    @field_validator("name", "color")
    @classmethod
    def validate_fields_not_null(cls, value: str | None, info: object) -> str:
        field_name = getattr(info, "field_name", "field")
        if value is None:
            raise ValueError(
                messages.MSG_FIELD_CANNOT_BE_NULL.format(field_name=field_name)
            )
        return value


class LabelResponse(LabelBase):
    id: int
    project_id: int
