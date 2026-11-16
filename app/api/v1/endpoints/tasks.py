from fastapi import APIRouter, status

from app.core.dependencies import DbSession, TaskServiceDep
from app.core.pagination import PaginationDep
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate

router = APIRouter()


@router.get(
    "",
    response_model=TaskListResponse,
    summary="Lấy danh sách tasks",
    responses={200: {"description": "Danh sách tasks kèm phân trang"}},
)
async def list_tasks(
    pagination: PaginationDep,
    db: DbSession,
    service: TaskServiceDep,
) -> TaskListResponse:
    return await service.list_tasks(db=db, pagination=pagination)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới task",
    responses={
        201: {"description": "Task được tạo thành công"},
        409: {"description": "Khóa ngoại không hợp lệ"},
        422: {"description": "Dữ liệu validation không hợp lệ"},
    },
)
async def create_task(
    payload: TaskCreate,
    db: DbSession,
    service: TaskServiceDep,
) -> TaskResponse:
    return await service.create_task(db=db, payload=payload)


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
    db: DbSession,
    service: TaskServiceDep,
) -> TaskResponse:
    task = await service.get_task_or_404(db=db, task_id=task_id)
    return TaskResponse.model_validate(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Cập nhật từng phần task",
    responses={
        200: {"description": "Cập nhật task thành công"},
        404: {"description": "Không tìm thấy task"},
        409: {"description": "Khóa ngoại không hợp lệ"},
        422: {"description": "Dữ liệu cập nhật không hợp lệ hoặc truyền null"},
    },
)
async def patch_task(
    task_id: int,
    payload: TaskUpdate,
    db: DbSession,
    service: TaskServiceDep,
) -> TaskResponse:
    return await service.patch_task(db=db, task_id=task_id, payload=payload)


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
    db: DbSession,
    service: TaskServiceDep,
) -> None:
    await service.delete_task(db=db, task_id=task_id)
