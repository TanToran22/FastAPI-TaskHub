from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import ConflictException
from app.core.pagination import Pagination
from app.core.permissions import (
    ALL_WORKSPACE_ROLES,
    WORKSPACE_OWNER_ROLES,
    WORKSPACE_WRITE_ROLES,
    get_project_access,
    get_workspace_access,
)
from app.models.enums import ProjectStatus
from app.models.models import Project, User
from app.repositories.project_repository import ProjectRepository
from app.schemas.base import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate


class ProjectService:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self.project_repo = project_repo

    async def create_project(
        self,
        db: AsyncSession,
        workspace_id: int,
        current_user: User,
        payload: ProjectCreate,
    ) -> Project:
        await get_workspace_access(
            db,
            workspace_id=workspace_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
        )
        create_data = payload.model_dump(exclude_unset=True)
        create_data["workspace_id"] = workspace_id
        return await self.project_repo.create(db, obj_in=create_data)

    async def list_projects(
        self,
        db: AsyncSession,
        workspace_id: int,
        current_user: User,
        status: ProjectStatus | None,
        pagination: Pagination,
    ) -> PaginatedResponse[ProjectResponse]:
        await get_workspace_access(
            db,
            workspace_id=workspace_id,
            current_user=current_user,
            allowed_roles=ALL_WORKSPACE_ROLES,
        )
        items = await self.project_repo.get_multi_by_workspace(
            db,
            workspace_id=workspace_id,
            status=status,
            pagination=pagination,
        )
        total = await self.project_repo.count_by_workspace(
            db,
            workspace_id=workspace_id,
            status=status,
        )
        return PaginatedResponse[ProjectResponse](
            items=[ProjectResponse.model_validate(item) for item in items],
            total=total,
            skip=pagination.skip,
            limit=pagination.limit,
        )

    async def get_project(
        self,
        db: AsyncSession,
        project_id: int,
        current_user: User,
    ) -> Project:
        project, _ = await get_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=ALL_WORKSPACE_ROLES,
        )
        return project

    async def update_project(
        self,
        db: AsyncSession,
        project_id: int,
        current_user: User,
        payload: ProjectUpdate,
    ) -> Project:
        project, _ = await get_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
            require_active=True,
        )
        return await self.project_repo.update(db, db_obj=project, obj_in=payload)

    async def archive_project(
        self,
        db: AsyncSession,
        project_id: int,
        current_user: User,
    ) -> Project:
        project, _ = await get_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
        )
        if project.status == ProjectStatus.ARCHIVED:
            raise ConflictException(messages.MSG_PROJECT_ALREADY_ARCHIVED)
        return await self.project_repo.update(
            db,
            db_obj=project,
            obj_in={"status": ProjectStatus.ARCHIVED},
        )

    async def unarchive_project(
        self,
        db: AsyncSession,
        project_id: int,
        current_user: User,
    ) -> Project:
        project, _ = await get_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
        )
        if project.status == ProjectStatus.ACTIVE:
            raise ConflictException(messages.MSG_PROJECT_NOT_ARCHIVED)
        return await self.project_repo.update(
            db,
            db_obj=project,
            obj_in={"status": ProjectStatus.ACTIVE},
        )

    async def delete_project(
        self,
        db: AsyncSession,
        project_id: int,
        current_user: User,
    ) -> None:
        project, _ = await get_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_OWNER_ROLES,
        )
        await self.project_repo.delete(db, id=project.id)
