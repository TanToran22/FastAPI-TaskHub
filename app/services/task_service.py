import logging

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import ConflictException, NotFoundException
from app.core.pagination import Pagination
from app.models.models import Task
from app.repositories.task_repository import TaskRepository
from app.schemas.base import PaginatedResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

logger = logging.getLogger("taskhub")


def _classify_integrity_error(exc: IntegrityError | OperationalError) -> str:
    raw_msg = str(exc.orig).lower()
    if "foreign key" in raw_msg:
        return messages.MSG_FOREIGN_KEY_VIOLATION
    if "not null" in raw_msg or "null value" in raw_msg:
        return "Required database field cannot be null."
    return messages.MSG_INTEGRITY_ERROR


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    async def get_task_or_404(self, db: AsyncSession, task_id: int) -> Task:
        task = await self.repository.get_by_id(db, id=task_id)
        if not task:
            raise NotFoundException(messages.MSG_TASK_NOT_FOUND)
        return task

    async def list_tasks(
        self, db: AsyncSession, pagination: Pagination
    ) -> PaginatedResponse[TaskResponse]:
        items = await self.repository.get_multi(db, pagination=pagination)
        total = await self.repository.count(db)
        return PaginatedResponse[TaskResponse](
            items=[TaskResponse.model_validate(item) for item in items],
            total=total,
            skip=pagination.skip,
            limit=pagination.limit,
        )

    async def create_task(
        self, db: AsyncSession, payload: TaskCreate, created_by: int
    ) -> Task:
        create_data = payload.model_dump(exclude_unset=True)
        create_data["created_by"] = created_by
        try:
            return await self.repository.create(db, obj_in=create_data)
        except (IntegrityError, OperationalError) as exc:
            if (
                isinstance(exc, OperationalError)
                and "foreign key" not in str(exc.orig).lower()
            ):
                raise
            await db.rollback()
            err_msg = _classify_integrity_error(exc)
            logger.warning("IntegrityError in create_task: %s", exc.orig)
            raise ConflictException(err_msg, details=str(exc.orig)) from exc

    async def patch_task(
        self, db: AsyncSession, task_id: int, payload: TaskUpdate
    ) -> Task:
        task = await self.get_task_or_404(db, task_id)
        try:
            return await self.repository.update(db, db_obj=task, obj_in=payload)
        except (IntegrityError, OperationalError) as exc:
            if (
                isinstance(exc, OperationalError)
                and "foreign key" not in str(exc.orig).lower()
            ):
                raise
            await db.rollback()
            err_msg = _classify_integrity_error(exc)
            logger.warning("IntegrityError in patch_task: %s", exc.orig)
            raise ConflictException(err_msg, details=str(exc.orig)) from exc

    async def delete_task(self, db: AsyncSession, task_id: int) -> None:
        deleted = await self.repository.delete(db, id=task_id)
        if not deleted:
            raise NotFoundException(messages.MSG_TASK_NOT_FOUND)
