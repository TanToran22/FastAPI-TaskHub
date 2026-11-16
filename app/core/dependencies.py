from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService

_task_repo_singleton = TaskRepository()

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_task_repository() -> TaskRepository:
    return _task_repo_singleton


def get_task_service(
    repo: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskService:
    return TaskService(repository=repo)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
