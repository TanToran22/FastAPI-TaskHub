from fastapi import APIRouter, status

from app.core.dependencies import (
    CurrentActiveUserDep,
    DbSession,
    TaskServiceDep,
)
from app.core.pagination import PaginationDep
from app.schemas.base import PaginatedResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[TaskResponse],
    summary="List tasks with pagination",
)
async def list_tasks(
    pagination: PaginationDep,
    db: DbSession,
    service: TaskServiceDep,
    current_user: CurrentActiveUserDep,
) -> PaginatedResponse[TaskResponse]:
    return await service.list_tasks(db, pagination=pagination)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    responses={
        401: {"description": "Not authenticated"},
        409: {"description": "Foreign key or integrity constraint violation"},
    },
)
async def create_task(
    payload: TaskCreate,
    db: DbSession,
    service: TaskServiceDep,
    current_user: CurrentActiveUserDep,
) -> TaskResponse:
    task = await service.create_task(db, payload=payload, created_by=current_user.id)
    return TaskResponse.model_validate(task)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task details by ID",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Task not found"},
    },
)
async def get_task(
    task_id: int,
    db: DbSession,
    service: TaskServiceDep,
    current_user: CurrentActiveUserDep,
) -> TaskResponse:
    task = await service.get_task_or_404(db, task_id)
    return TaskResponse.model_validate(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Partially update a task",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Task not found"},
        409: {"description": "Foreign key or integrity constraint violation"},
    },
)
async def patch_task(
    task_id: int,
    payload: TaskUpdate,
    db: DbSession,
    service: TaskServiceDep,
    current_user: CurrentActiveUserDep,
) -> TaskResponse:
    task = await service.patch_task(db, task_id, payload)
    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Task not found"},
    },
)
async def delete_task(
    task_id: int,
    db: DbSession,
    service: TaskServiceDep,
    current_user: CurrentActiveUserDep,
) -> None:
    await service.delete_task(db, task_id)
