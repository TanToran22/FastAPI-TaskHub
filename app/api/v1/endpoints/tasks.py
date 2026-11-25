from fastapi import APIRouter, status

from app.api.v1.params import (
    AssigneeIdFilterQuery,
    LabelIdPath,
    ProjectIdPath,
    TaskIdPath,
    TaskPriorityFilterQuery,
    TaskStatusFilterQuery,
)
from app.core.dependencies import (
    CurrentActiveUserDep,
    DbSession,
    TaskServiceDep,
)
from app.core.pagination import PaginationDep
from app.schemas.base import PaginatedResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

project_tasks_router = APIRouter()
router = APIRouter()


@project_tasks_router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task inside a project (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Project not found"},
        409: {"description": "Project is archived"},
        422: {"description": "Invalid payload or assignee not in workspace"},
    },
)
async def create_project_task(
    project_id: ProjectIdPath,
    payload: TaskCreate,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: TaskServiceDep,
) -> TaskResponse:
    task = await service.create_task(
        db, project_id=project_id, current_user=current_user, payload=payload
    )
    return TaskResponse.model_validate(task)


@project_tasks_router.get(
    "",
    response_model=PaginatedResponse[TaskResponse],
    summary="List tasks in a project with filtering and pagination",
    responses={
        404: {"description": "Project not found"},
    },
)
async def list_project_tasks(
    project_id: ProjectIdPath,
    pagination: PaginationDep,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: TaskServiceDep,
    status_filter: TaskStatusFilterQuery = None,
    priority_filter: TaskPriorityFilterQuery = None,
    assignee_id: AssigneeIdFilterQuery = None,
) -> PaginatedResponse[TaskResponse]:
    return await service.list_tasks(
        db,
        project_id=project_id,
        current_user=current_user,
        pagination=pagination,
        statuses=status_filter,
        priorities=priority_filter,
        assignee_id=assignee_id,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task details by ID (requires workspace membership)",
    responses={
        404: {"description": "Task not found"},
    },
)
async def get_task(
    task_id: TaskIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: TaskServiceDep,
) -> TaskResponse:
    task = await service.get_task(db, task_id=task_id, current_user=current_user)
    return TaskResponse.model_validate(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Partially update a task (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Task not found"},
        409: {"description": "Project is archived"},
        422: {"description": "Invalid payload or assignee not in workspace"},
    },
)
async def patch_task(
    task_id: TaskIdPath,
    payload: TaskUpdate,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: TaskServiceDep,
) -> TaskResponse:
    task = await service.patch_task(
        db, task_id=task_id, current_user=current_user, payload=payload
    )
    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Task not found"},
        409: {"description": "Project is archived"},
    },
)
async def delete_task(
    task_id: TaskIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: TaskServiceDep,
) -> None:
    await service.delete_task(db, task_id=task_id, current_user=current_user)


@router.post(
    "/{task_id}/labels/{label_id}",
    response_model=TaskResponse,
    summary="Assign a label to a task (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Task or label not found"},
        409: {"description": "Project is archived or label already assigned"},
        422: {"description": "Label does not belong to the task's project"},
    },
)
async def assign_label_to_task(
    task_id: TaskIdPath,
    label_id: LabelIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: TaskServiceDep,
) -> TaskResponse:
    task = await service.assign_label(
        db, task_id=task_id, label_id=label_id, current_user=current_user
    )
    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a label from a task (OWNER or EDITOR)",
    responses={
        403: {"description": "Requires OWNER or EDITOR role"},
        404: {"description": "Task or label assignment not found"},
        409: {"description": "Project is archived"},
    },
)
async def remove_label_from_task(
    task_id: TaskIdPath,
    label_id: LabelIdPath,
    db: DbSession,
    current_user: CurrentActiveUserDep,
    service: TaskServiceDep,
) -> None:
    await service.remove_label(
        db, task_id=task_id, label_id=label_id, current_user=current_user
    )
