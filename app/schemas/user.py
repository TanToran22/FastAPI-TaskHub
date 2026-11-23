from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.core import constants, messages
from app.models.enums import UserRole
from app.schemas.base import CoreBaseSchema, NoStripBaseSchema


def _validate_password_byte_length(password: str) -> str:
    if len(password.encode("utf-8")) > constants.BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(messages.MSG_PASSWORD_TOO_LONG_BYTES)
    return password


class UserBase(CoreBaseSchema):
    email: EmailStr = Field(..., max_length=constants.USER_EMAIL_MAX_LENGTH)
    full_name: str = Field(
        ...,
        min_length=constants.USER_FULL_NAME_MIN_LENGTH,
        max_length=constants.USER_FULL_NAME_MAX_LENGTH,
    )


class UserRegister(NoStripBaseSchema):
    email: EmailStr = Field(..., max_length=constants.USER_EMAIL_MAX_LENGTH)
    full_name: str = Field(
        ...,
        min_length=constants.USER_FULL_NAME_MIN_LENGTH,
        max_length=constants.USER_FULL_NAME_MAX_LENGTH,
    )
    password: str = Field(
        ...,
        min_length=constants.USER_PASSWORD_MIN_LENGTH,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
    )

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < constants.USER_FULL_NAME_MIN_LENGTH:
            raise ValueError("Full name must not be blank.")
        return stripped

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, value: str) -> str:
        return _validate_password_byte_length(value)


class UserLogin(NoStripBaseSchema):
    email: EmailStr = Field(..., max_length=constants.USER_EMAIL_MAX_LENGTH)
    password: str = Field(
        ...,
        min_length=constants.USER_MIN_INPUT_LENGTH,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
    )

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, value: str) -> str:
        return _validate_password_byte_length(value)


class UserUpdate(CoreBaseSchema):
    full_name: str | None = Field(
        default=None,
        min_length=constants.USER_FULL_NAME_MIN_LENGTH,
        max_length=constants.USER_FULL_NAME_MAX_LENGTH,
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name_not_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError(
                messages.MSG_FIELD_CANNOT_BE_NULL.format(field_name="full_name")
            )
        return value


class PasswordChange(NoStripBaseSchema):
    current_password: str = Field(
        ...,
        min_length=constants.USER_MIN_INPUT_LENGTH,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
    )
    new_password: str = Field(
        ...,
        min_length=constants.USER_PASSWORD_MIN_LENGTH,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
    )

    @field_validator("current_password", "new_password")
    @classmethod
    def check_password_bytes(cls, value: str) -> str:
        return _validate_password_byte_length(value)


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(CoreBaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = constants.TOKEN_TYPE_BEARER


class TokenRefreshRequest(CoreBaseSchema):
    refresh_token: str = Field(..., min_length=constants.USER_MIN_INPUT_LENGTH)
