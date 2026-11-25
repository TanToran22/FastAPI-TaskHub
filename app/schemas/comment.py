from datetime import datetime

from pydantic import Field, field_validator

from app.core import constants, messages
from app.schemas.base import CoreBaseSchema


class CommentBase(CoreBaseSchema):
    content: str = Field(
        ...,
        min_length=constants.COMMENT_CONTENT_MIN_LENGTH,
        max_length=constants.COMMENT_CONTENT_MAX_LENGTH,
    )


class CommentCreate(CommentBase):
    pass


class CommentUpdate(CoreBaseSchema):
    content: str | None = Field(
        default=None,
        min_length=constants.COMMENT_CONTENT_MIN_LENGTH,
        max_length=constants.COMMENT_CONTENT_MAX_LENGTH,
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError(
                messages.MSG_FIELD_CANNOT_BE_NULL.format(field_name="content")
            )
        return value


class CommentResponse(CommentBase):
    id: int
    task_id: int
    author_id: int
    created_at: datetime
