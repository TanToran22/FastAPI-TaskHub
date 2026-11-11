from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Task
from app.repositories.base import BaseRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskRepository(BaseRepository[Task, TaskCreate, TaskUpdate]):
    def __init__(self) -> None:
        super().__init__(model=Task)

    async def get_multi_ordered(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 20
    ) -> list[Task]:
        query = (
            select(Task)
            .order_by(Task.created_at.desc(), Task.id.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
