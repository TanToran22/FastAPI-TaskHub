from fastapi import APIRouter, status

from app.api.v1.params import LabelIdPath, ProjectIdPath
from app.core.dependencies import (
    CurrentActiveUserDep,
    DbSession,
    LabelServiceDep,
)
from app.core.pagination import PaginationDep
from app.schemas.base import PaginatedResponse
from app.schemas.label import LabelCreate, LabelResponse, LabelUpdate

project_labels_router = APIRouter()
router = APIRouter()


@project_labels_router.post(
    "",
    response_model=LabelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a label in a project (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Project not found"},
        409: {"description": "Project is archived or label name exists"},
    },
)
async def create_project_label(
    project_id: ProjectIdPath,
    payload: LabelCreate,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: LabelServiceDep,
) -> LabelResponse:
    label = await service.create_label(
        db, project_id=project_id, current_user=current_user, payload=payload
    )
    return LabelResponse.model_validate(label)


@project_labels_router.get(
    "",
    response_model=PaginatedResponse[LabelResponse],
    summary="List labels in a project",
    responses={
        404: {"description": "Project not found"},
    },
)
async def list_project_labels(
    project_id: ProjectIdPath,
    pagination: PaginationDep,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: LabelServiceDep,
) -> PaginatedResponse[LabelResponse]:
    return await service.list_labels(
        db,
        project_id=project_id,
        current_user=current_user,
        pagination=pagination,
    )


@router.patch(
    "/{label_id}",
    response_model=LabelResponse,
    summary="Update a label (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Label not found"},
        409: {"description": "Project is archived or label name exists"},
    },
)
async def update_label(
    label_id: LabelIdPath,
    payload: LabelUpdate,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: LabelServiceDep,
) -> LabelResponse:
    label = await service.update_label(
        db, label_id=label_id, current_user=current_user, payload=payload
    )
    return LabelResponse.model_validate(label)


@router.delete(
    "/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a label (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Label not found"},
        409: {"description": "Project is archived"},
    },
)
async def delete_label(
    label_id: LabelIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: LabelServiceDep,
) -> None:
    await service.delete_label(db, label_id=label_id, current_user=current_user)
