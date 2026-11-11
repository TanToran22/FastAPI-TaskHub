from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import ConflictException, NotFoundException
from app.models.models import Task
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    async def get_task_or_404(self, db: AsyncSession, task_id: int) -> Task:
        task = await self.repository.get_by_id(db, item_id=task_id)
        if not task:
            raise NotFoundException(messages.MSG_TASK_NOT_FOUND)
        return task

    async def list_tasks(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> TaskListResponse:
        items = await self.repository.get_multi_ordered(db, skip=skip, limit=limit)
        total = await self.repository.count(db)
        return TaskListResponse(
            items=[TaskResponse.model_validate(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def create_task(
        self,
        db: AsyncSession,
        payload: TaskCreate,
    ) -> TaskResponse:
        try:
            task = await self.repository.create(db, obj_in=payload)
            await db.commit()
            return TaskResponse.model_validate(task)
        except IntegrityError as exc:
            await db.rollback()
            raise ConflictException(
                "Foreign key constraint violation: "
                "referenced project or assignee does not exist."
            ) from exc

    async def patch_task(
        self,
        db: AsyncSession,
        task_id: int,
        payload: TaskUpdate,
    ) -> TaskResponse:
        task = await self.get_task_or_404(db, task_id)
        try:
            updated = await self.repository.update(db, db_obj=task, obj_in=payload)
            await db.commit()
            return TaskResponse.model_validate(updated)
        except IntegrityError as exc:
            await db.rollback()
            raise ConflictException(
                "Foreign key constraint violation: "
                "referenced project or assignee does not exist."
            ) from exc

    async def delete_task(self, db: AsyncSession, task_id: int) -> None:
        await self.get_task_or_404(db, task_id)
        await self.repository.delete(db, item_id=task_id)
        await db.commit()
