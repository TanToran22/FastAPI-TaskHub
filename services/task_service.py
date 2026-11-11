from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants
from app.core.exceptions import ConflictException, NotFoundException
from app.models.models import Task
from app.repositories.task_repository import TaskRepository
from app.schemas.base import PaginatedResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    async def get_task_or_404(self, db: AsyncSession, task_id: int) -> Task:
        task = await self.repository.get_by_id(db, id=task_id)
        if not task:
            raise NotFoundException(constants.MSG_TASK_NOT_FOUND)
        return task

    async def list_tasks(
        self, db: AsyncSession, skip: int = 0, limit: int = 20
    ) -> PaginatedResponse[TaskResponse]:
        items = await self.repository.get_multi_ordered(db, skip=skip, limit=limit)
        total = await self.repository.count(db)
        return PaginatedResponse[TaskResponse](
            items=[TaskResponse.model_validate(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def create_task(self, db: AsyncSession, payload: TaskCreate) -> Task:
        try:
            return await self.repository.create(db, obj_in=payload)
        except IntegrityError as exc:
            await db.rollback()
            raise ConflictException(
                constants.MSG_CONFLICT_RESOURCE, details=str(exc.orig)
            ) from exc

    async def patch_task(
        self, db: AsyncSession, task_id: int, payload: TaskUpdate
    ) -> Task:
        task = await self.get_task_or_404(db, task_id)
        try:
            return await self.repository.update(db, db_obj=task, obj_in=payload)
        except IntegrityError as exc:
            await db.rollback()
            raise ConflictException(
                constants.MSG_CONFLICT_RESOURCE, details=str(exc.orig)
            ) from exc

    async def delete_task(self, db: AsyncSession, task_id: int) -> None:
        deleted = await self.repository.delete(db, id=task_id)
        if not deleted:
            raise NotFoundException(constants.MSG_TASK_NOT_FOUND)
