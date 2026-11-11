from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core import constants
from app.core.dependencies import get_task_service
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter()

SkipParam = Annotated[
    int,
    Query(
        ge=0,
        description="Số lượng bản ghi bỏ qua",
    ),
]
LimitParam = Annotated[
    int,
    Query(
        ge=constants.MIN_PAGINATION_LIMIT,
        le=constants.MAX_PAGINATION_LIMIT,
        description="Số lượng bản ghi tối đa",
    ),
]


@router.get(
    "",
    response_model=TaskListResponse,
    summary="Lấy danh sách tasks",
    responses={
        200: {"description": "Danh sách tasks kèm tổng số lượng"},
    },
)
async def list_tasks(
    skip: SkipParam = constants.DEFAULT_PAGINATION_SKIP,
    limit: LimitParam = constants.DEFAULT_PAGINATION_LIMIT,
    service: TaskService = Depends(get_task_service),
) -> TaskListResponse:
    return service.list_tasks(skip=skip, limit=limit)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới task",
    responses={
        201: {"description": "Task được tạo thành công"},
        422: {"description": "Dữ liệu đầu vào không hợp lệ"},
    },
)
async def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return service.create_task(payload)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Lấy thông tin chi tiết task",
    responses={
        200: {"description": "Thông tin task"},
        404: {"description": "Không tìm thấy task"},
    },
)
async def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return TaskResponse.model_validate(service.get_task_or_404(task_id))


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Cập nhật từng phần task",
    responses={
        200: {"description": "Cập nhật task thành công"},
        404: {"description": "Không tìm thấy task"},
        422: {"description": "Dữ liệu cập nhật không hợp lệ hoặc truyền null"},
    },
)
async def patch_task(
    task_id: int,
    payload: TaskUpdate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return service.patch_task(task_id, payload)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xoá task",
    responses={
        204: {"description": "Đã xoá thành công"},
        404: {"description": "Không tìm thấy task"},
    },
)
async def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> None:
    service.delete_task(task_id)
