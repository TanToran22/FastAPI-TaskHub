from fastapi import APIRouter, status

from app.api.v1.params import UserIdPath, WorkspaceIdPath
from app.core.dependencies import (
    CurrentActiveUserDep,
    DbSession,
    WorkspaceServiceDep,
)
from app.core.pagination import PaginationDep
from app.schemas.base import PaginatedResponse
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberInvite,
    WorkspaceMemberResponse,
    WorkspaceMemberRoleUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)

router = APIRouter()


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workspace (creator becomes OWNER)",
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def create_workspace(
    payload: WorkspaceCreate,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    workspace = await service.create_workspace(db, current_user, payload)
    return WorkspaceResponse.model_validate(workspace)


@router.get(
    "",
    response_model=PaginatedResponse[WorkspaceResponse],
    summary="List workspaces that the current user belongs to",
)
async def list_workspaces(
    pagination: PaginationDep,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: WorkspaceServiceDep,
) -> PaginatedResponse[WorkspaceResponse]:
    return await service.list_workspaces(db, current_user, pagination)


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Get workspace details (requires membership)",
    responses={
        403: {"description": "Not a member of this workspace"},
        404: {"description": "Workspace not found"},
    },
)
async def get_workspace(
    workspace_id: WorkspaceIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    workspace = await service.get_workspace(db, workspace_id, current_user)
    return WorkspaceResponse.model_validate(workspace)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Update workspace details (OWNER only)",
    responses={
        403: {"description": "Requires OWNER role"},
        404: {"description": "Workspace not found"},
    },
)
async def update_workspace(
    workspace_id: WorkspaceIdPath,
    payload: WorkspaceUpdate,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    workspace = await service.update_workspace(db, workspace_id, current_user, payload)
    return WorkspaceResponse.model_validate(workspace)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workspace (OWNER only)",
    responses={
        403: {"description": "Requires OWNER role"},
        404: {"description": "Workspace not found"},
    },
)
async def delete_workspace(
    workspace_id: WorkspaceIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: WorkspaceServiceDep,
) -> None:
    await service.delete_workspace(db, workspace_id, current_user)


@router.get(
    "/{workspace_id}/members",
    response_model=PaginatedResponse[WorkspaceMemberResponse],
    summary="List members of a workspace",
    responses={
        403: {"description": "Not a member of this workspace"},
        404: {"description": "Workspace not found"},
    },
)
async def list_workspace_members(
    workspace_id: WorkspaceIdPath,
    pagination: PaginationDep,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: WorkspaceServiceDep,
) -> PaginatedResponse[WorkspaceMemberResponse]:
    return await service.list_members(db, workspace_id, current_user, pagination)


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a user to workspace by email (OWNER only)",
    responses={
        403: {"description": "Requires OWNER role"},
        404: {"description": "Workspace or user not found"},
        409: {"description": "User is already a member"},
        422: {"description": "Invalid role (e.g., OWNER not allowed)"},
    },
)
async def invite_workspace_member(
    workspace_id: WorkspaceIdPath,
    payload: WorkspaceMemberInvite,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: WorkspaceServiceDep,
) -> WorkspaceMemberResponse:
    member = await service.invite_member(db, workspace_id, current_user, payload)
    return WorkspaceMemberResponse.model_validate(member)


@router.patch(
    "/{workspace_id}/members/{user_id}",
    response_model=WorkspaceMemberResponse,
    summary="Update a workspace member's role (OWNER only)",
    responses={
        400: {"description": "Cannot modify OWNER role"},
        403: {"description": "Requires OWNER role"},
        404: {"description": "Workspace or member not found"},
    },
)
async def update_workspace_member_role(
    workspace_id: WorkspaceIdPath,
    user_id: UserIdPath,
    payload: WorkspaceMemberRoleUpdate,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: WorkspaceServiceDep,
) -> WorkspaceMemberResponse:
    member = await service.update_member_role(
        db, workspace_id, user_id, current_user, payload
    )
    return WorkspaceMemberResponse.model_validate(member)


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from workspace (OWNER only)",
    responses={
        400: {"description": "Cannot remove workspace OWNER"},
        403: {"description": "Requires OWNER role"},
        404: {"description": "Workspace or member not found"},
    },
)
async def remove_workspace_member(
    workspace_id: WorkspaceIdPath,
    user_id: UserIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: WorkspaceServiceDep,
) -> None:
    await service.remove_member(db, workspace_id, user_id, current_user)
