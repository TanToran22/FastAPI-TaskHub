from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field, field_validator

from app.core import constants, messages
from app.models.enums import WorkspaceRole
from app.schemas.base import CoreBaseSchema

# Restrict assignable roles to prevent privilege escalation to OWNER
AssignableWorkspaceRole = Literal[WorkspaceRole.EDITOR, WorkspaceRole.VIEWER]


class WorkspaceBase(CoreBaseSchema):
    name: str = Field(
        ...,
        min_length=constants.WORKSPACE_NAME_MIN_LENGTH,
        max_length=constants.WORKSPACE_NAME_MAX_LENGTH,
    )


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(CoreBaseSchema):
    name: str | None = Field(
        default=None,
        min_length=constants.WORKSPACE_NAME_MIN_LENGTH,
        max_length=constants.WORKSPACE_NAME_MAX_LENGTH,
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError(
                messages.MSG_FIELD_CANNOT_BE_NULL.format(field_name="name")
            )
        return value


class WorkspaceResponse(WorkspaceBase):
    id: int
    owner_id: int
    created_at: datetime


class WorkspaceMemberInvite(CoreBaseSchema):
    email: EmailStr = Field(..., max_length=constants.USER_EMAIL_MAX_LENGTH)
    role: AssignableWorkspaceRole = WorkspaceRole.VIEWER


class WorkspaceMemberRoleUpdate(CoreBaseSchema):
    role: AssignableWorkspaceRole


class WorkspaceMemberResponse(CoreBaseSchema):
    id: int
    workspace_id: int
    user_id: int
    role: WorkspaceRole
