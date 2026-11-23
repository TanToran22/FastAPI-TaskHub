from typing import Annotated

from fastapi import APIRouter, Path, status

from app.core.dependencies import (
    CurrentActiveUserDep,
    DbSession,
    ProjectServiceDep,
)
from app.schemas.project import ProjectResponse, ProjectUpdate

router = APIRouter()

ProjectIdPath = Annotated[int, Path(gt=0, description="Project ID")]


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details (requires workspace membership)",
    responses={
        403: {"description": "Not a member of the project's workspace"},
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
        422: {"description": "Validation error (e.g., null name/status)"},
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
