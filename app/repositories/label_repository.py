from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination
from app.models.models import Label, task_labels
from app.repositories.base import BaseRepository
from app.schemas.label import LabelCreate, LabelUpdate


class LabelRepository(BaseRepository[Label, LabelCreate, LabelUpdate]):
    def __init__(self) -> None:
        super().__init__(model=Label)

    async def get_by_id_and_project(
        self,
        db: AsyncSession,
        *,
        label_id: int,
        project_id: int,
    ) -> Label | None:
        query = select(Label).where(
            Label.id == label_id,
            Label.project_id == project_id,
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi_by_project(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        pagination: Pagination,
    ) -> list[Label]:
        query = (
            select(Label)
            .where(Label.project_id == project_id)
            .order_by(Label.id.asc())
            .offset(pagination.skip)
            .limit(pagination.limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_by_project(self, db: AsyncSession, *, project_id: int) -> int:
        query = select(func.count(Label.id)).where(Label.project_id == project_id)
        result = await db.execute(query)
        return result.scalar_one()

    async def assign_to_task(
        self, db: AsyncSession, *, task_id: int, label_id: int
    ) -> None:
        stmt = insert(task_labels).values(task_id=task_id, label_id=label_id)
        await db.execute(stmt)
        await db.flush()

    async def remove_from_task(
        self, db: AsyncSession, *, task_id: int, label_id: int
    ) -> int:
        stmt = delete(task_labels).where(
            task_labels.c.task_id == task_id,
            task_labels.c.label_id == label_id,
        )
        result = await db.execute(stmt)
        await db.flush()
        return int(result.rowcount or 0)
