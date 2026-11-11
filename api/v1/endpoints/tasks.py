from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants
from app.core.database import get_db
from app.core.dependencies import get_task_service
from app.schemas.base import PaginatedResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    skip: int = Query(default=constants.DEFAULT_PAGINATION_SKIP, ge=0),
    limit: int = Query(
        default=constants.DEFAULT_PAGINATION_LIMIT,
        ge=1,
        le=constants.MAX_PAGINATION_LIMIT,
    ),
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> Any:
    return await service.list_tasks(db, skip=skip, limit=limit)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> Any:
    return await service.create_task(db, payload)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> Any:
    return await service.get_task_or_404(db, task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def patch_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> Any:
    return await service.patch_task(db, task_id, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> None:
    await service.delete_task(db, task_id)
