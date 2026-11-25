from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.pagination import Pagination
from app.models.enums import TaskPriority, TaskStatus
from app.models.models import Task
from app.repositories.base import BaseRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskRepository(BaseRepository[Task, TaskCreate, TaskUpdate]):
    def __init__(self) -> None:
        super().__init__(model=Task)

    @staticmethod
    def _build_filters(
        *,
        project_id: int,
        statuses: list[TaskStatus] | None = None,
        priorities: list[TaskPriority] | None = None,
        assignee_id: int | None = None,
    ) -> list[Any]:
        filters: list[Any] = [Task.project_id == project_id]
        if statuses:
            filters.append(Task.status.in_(statuses))
        if priorities:
            filters.append(Task.priority.in_(priorities))
        if assignee_id is not None:
            filters.append(Task.assignee_id == assignee_id)
        return filters

    async def get_by_id_with_labels(
        self, db: AsyncSession, *, task_id: int
    ) -> Task | None:
        query = (
            select(Task).options(selectinload(Task.labels)).where(Task.id == task_id)
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi_by_project(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        pagination: Pagination,
        statuses: list[TaskStatus] | None = None,
        priorities: list[TaskPriority] | None = None,
        assignee_id: int | None = None,
    ) -> list[Task]:
        filters = self._build_filters(
            project_id=project_id,
            statuses=statuses,
            priorities=priorities,
            assignee_id=assignee_id,
        )
        query = (
            select(Task)
            .options(selectinload(Task.labels))
            .where(*filters)
            .order_by(Task.created_at.desc(), Task.id.desc())
            .offset(pagination.skip)
            .limit(pagination.limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_by_project(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        statuses: list[TaskStatus] | None = None,
        priorities: list[TaskPriority] | None = None,
        assignee_id: int | None = None,
    ) -> int:
        filters = self._build_filters(
            project_id=project_id,
            statuses=statuses,
            priorities=priorities,
            assignee_id=assignee_id,
        )
        query = select(func.count(Task.id)).where(*filters)
        result = await db.execute(query)
        return result.scalar_one()
