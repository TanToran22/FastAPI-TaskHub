from collections.abc import Sequence
from typing import Any

from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination
from app.models.models import Task
from app.repositories.base import BaseRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskRepository(BaseRepository[Task, TaskCreate, TaskUpdate]):
    def __init__(self) -> None:
        super().__init__(model=Task)

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        pagination: Pagination,
        order_by: Sequence[ColumnElement[Any]] | None = None,
    ) -> Sequence[Task]:
        ordering = (
            order_by
            if order_by is not None
            else (self.model.created_at.desc(), self.model.id.desc())
        )
        return await super().get_multi(
            db,
            pagination=pagination,
            order_by=ordering,
        )
