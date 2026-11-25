from fastapi import APIRouter, status

from app.api.v1.params import (
    ProjectIdPath,
    ProjectStatusQuery,
    WorkspaceIdPath,
)
from app.core.dependencies import (
    CurrentActiveUserDep,
    DbSession,
    ProjectServiceDep,
)
from app.core.pagination import PaginationDep
from app.schemas.base import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

workspace_projects_router = APIRouter()
router = APIRouter()


@workspace_projects_router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project inside a workspace (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Workspace not found"},
    },
)
async def create_workspace_project(
    workspace_id: WorkspaceIdPath,
    payload: ProjectCreate,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.create_project(db, workspace_id, current_user, payload)
    return ProjectResponse.model_validate(project)


@workspace_projects_router.get(
    "",
    response_model=PaginatedResponse[ProjectResponse],
    summary="List projects in a workspace with optional status filter",
    responses={
        404: {"description": "Workspace not found"},
    },
)
async def list_workspace_projects(
    workspace_id: WorkspaceIdPath,
    pagination: PaginationDep,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: ProjectServiceDep,
    status_filter: ProjectStatusQuery = None,
) -> PaginatedResponse[ProjectResponse]:
    return await service.list_projects(
        db,
        workspace_id=workspace_id,
        current_user=current_user,
        status=status_filter,
        pagination=pagination,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details (requires workspace membership)",
    responses={
        404: {"description": "Project not found"},
    },
)
async def get_project(
    project_id: ProjectIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.get_project(db, project_id, current_user)
    return ProjectResponse.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Project not found"},
        409: {"description": "Project is archived"},
        422: {"description": "Validation error (e.g., null name)"},
    },
)
async def update_project(
    project_id: ProjectIdPath,
    payload: ProjectUpdate,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.update_project(db, project_id, current_user, payload)
    return ProjectResponse.model_validate(project)


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    summary="Archive a project (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Project not found"},
    },
)
async def archive_project(
    project_id: ProjectIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.archive_project(db, project_id, current_user)
    return ProjectResponse.model_validate(project)


@router.post(
    "/{project_id}/unarchive",
    response_model=ProjectResponse,
    summary="Unarchive a project back to ACTIVE (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Project not found"},
    },
)
async def unarchive_project(
    project_id: ProjectIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.unarchive_project(db, project_id, current_user)
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project (OWNER only)",
    responses={
        403: {"description": "Requires OWNER role"},
        404: {"description": "Project not found"},
    },
)
async def delete_project(
    project_id: ProjectIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: ProjectServiceDep,
) -> None:
    await service.delete_project(db, project_id, current_user)
