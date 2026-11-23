from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination
from app.models.enums import ProjectStatus
from app.models.models import Project
from app.repositories.base import BaseRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository(BaseRepository[Project, ProjectCreate, ProjectUpdate]):
    def __init__(self) -> None:
        super().__init__(model=Project)

    async def get_multi_by_workspace(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        status: ProjectStatus | None,
        pagination: Pagination,
    ) -> list[Project]:
        query = select(Project).where(Project.workspace_id == workspace_id)
        if status is not None:
            query = query.where(Project.status == status)
        query = (
            query.order_by(Project.created_at.desc(), Project.id.desc())
            .offset(pagination.skip)
            .limit(pagination.limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_by_workspace(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        status: ProjectStatus | None,
    ) -> int:
        query = select(func.count(Project.id)).where(
            Project.workspace_id == workspace_id
        )
        if status is not None:
            query = query.where(Project.status == status)
        result = await db.execute(query)
        return result.scalar_one()
