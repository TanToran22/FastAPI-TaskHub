from fastapi import APIRouter, status

from app.api.v1.params import CommentIdPath, TaskIdPath
from app.core.dependencies import (
    CommentServiceDep,
    CurrentActiveUserDep,
    DbSession,
)
from app.core.pagination import PaginationDep
from app.schemas.base import PaginatedResponse
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate

task_comments_router = APIRouter()
router = APIRouter()


@task_comments_router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a task (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Task not found"},
        409: {"description": "Project is archived"},
    },
)
async def create_task_comment(
    task_id: TaskIdPath,
    payload: CommentCreate,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: CommentServiceDep,
) -> CommentResponse:
    comment = await service.create_comment(
        db, task_id=task_id, current_user=current_user, payload=payload
    )
    return CommentResponse.model_validate(comment)


@task_comments_router.get(
    "",
    response_model=PaginatedResponse[CommentResponse],
    summary="List comments on a task ordered by creation time ascending",
    responses={
        404: {"description": "Task not found"},
    },
)
async def list_task_comments(
    task_id: TaskIdPath,
    pagination: PaginationDep,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: CommentServiceDep,
) -> PaginatedResponse[CommentResponse]:
    return await service.list_comments(
        db,
        task_id=task_id,
        current_user=current_user,
        pagination=pagination,
    )


@router.patch(
    "/{comment_id}",
    response_model=CommentResponse,
    summary="Edit a comment (author, workspace OWNER, or system ADMIN)",
    responses={
        403: {"description": "Not allowed to edit this comment"},
        404: {"description": "Comment not found"},
        409: {"description": "Project is archived"},
    },
)
async def update_comment(
    comment_id: CommentIdPath,
    payload: CommentUpdate,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: CommentServiceDep,
) -> CommentResponse:
    comment = await service.update_comment(
        db, comment_id=comment_id, current_user=current_user, payload=payload
    )
    return CommentResponse.model_validate(comment)


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment (author, workspace OWNER, or system ADMIN)",
    responses={
        403: {"description": "Not allowed to delete this comment"},
        404: {"description": "Comment not found"},
        409: {"description": "Project is archived"},
    },
)
async def delete_comment(
    comment_id: CommentIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: CommentServiceDep,
) -> None:
    await service.delete_comment(db, comment_id=comment_id, current_user=current_user)
