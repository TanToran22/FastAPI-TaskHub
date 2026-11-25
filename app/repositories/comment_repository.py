from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination
from app.models.models import Comment
from app.repositories.base import BaseRepository
from app.schemas.comment import CommentCreate, CommentUpdate


class CommentRepository(BaseRepository[Comment, CommentCreate, CommentUpdate]):
    def __init__(self) -> None:
        super().__init__(model=Comment)

    async def get_multi_by_task(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        pagination: Pagination,
    ) -> list[Comment]:
        query = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at.asc(), Comment.id.asc())
            .offset(pagination.skip)
            .limit(pagination.limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_by_task(self, db: AsyncSession, *, task_id: int) -> int:
        query = select(func.count(Comment.id)).where(Comment.task_id == task_id)
        result = await db.execute(query)
        return result.scalar_one()
