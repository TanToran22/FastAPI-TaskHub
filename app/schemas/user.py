from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.core import constants, messages
from app.models.enums import UserRole
from app.schemas.base import CoreBaseSchema


class UserBase(CoreBaseSchema):
    email: EmailStr = Field(..., max_length=constants.USER_EMAIL_MAX_LENGTH)
    full_name: str = Field(
        ...,
        min_length=constants.USER_FULL_NAME_MIN_LENGTH,
        max_length=constants.USER_FULL_NAME_MAX_LENGTH,
    )


class UserRegister(UserBase):
    password: str = Field(
        ...,
        min_length=constants.USER_PASSWORD_MIN_LENGTH,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
    )


class UserLogin(CoreBaseSchema):
    email: EmailStr = Field(..., max_length=constants.USER_EMAIL_MAX_LENGTH)
    password: str = Field(
        ...,
        min_length=1,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
    )


class UserUpdate(CoreBaseSchema):
    full_name: str | None = Field(
        default=None,
        min_length=constants.USER_FULL_NAME_MIN_LENGTH,
        max_length=constants.USER_FULL_NAME_MAX_LENGTH,
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name_not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError(
                messages.MSG_FIELD_CANNOT_BE_NULL.format(field_name="full_name")
            )
        return value


class PasswordChange(CoreBaseSchema):
    current_password: str = Field(
        ...,
        min_length=1,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
    )
    new_password: str = Field(
        ...,
        min_length=constants.USER_PASSWORD_MIN_LENGTH,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
    )


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(CoreBaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(CoreBaseSchema):
    refresh_token: str = Field(..., min_length=1)
