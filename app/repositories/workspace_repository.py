from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination
from app.models.models import Workspace, WorkspaceMember
from app.repositories.base import BaseRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


class WorkspaceRepository(BaseRepository[Workspace, WorkspaceCreate, WorkspaceUpdate]):
    def __init__(self) -> None:
        super().__init__(model=Workspace)

    async def get_multi_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        pagination: Pagination,
    ) -> list[Workspace]:
        query = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at.desc(), Workspace.id.desc())
            .offset(pagination.skip)
            .limit(pagination.limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_by_user(self, db: AsyncSession, *, user_id: int) -> int:
        query = (
            select(func.count(Workspace.id))
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
        )
        result = await db.execute(query)
        return result.scalar_one()
