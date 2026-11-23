from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination
from app.models.models import WorkspaceMember
from app.repositories.base import BaseRepository
from app.schemas.workspace import WorkspaceMemberInvite, WorkspaceMemberRoleUpdate


class WorkspaceMemberRepository(
    BaseRepository[
        WorkspaceMember,
        WorkspaceMemberInvite,
        WorkspaceMemberRoleUpdate,
    ]
):
    def __init__(self) -> None:
        super().__init__(model=WorkspaceMember)

    async def get_by_workspace_and_user(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        user_id: int,
    ) -> WorkspaceMember | None:
        query = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi_by_workspace(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        pagination: Pagination,
    ) -> list[WorkspaceMember]:
        query = (
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .order_by(WorkspaceMember.id.asc())
            .offset(pagination.skip)
            .limit(pagination.limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_by_workspace(self, db: AsyncSession, *, workspace_id: int) -> int:
        query = select(func.count(WorkspaceMember.id)).where(
            WorkspaceMember.workspace_id == workspace_id
        )
        result = await db.execute(query)
        return result.scalar_one()
