from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import NotFoundException
from app.core.pagination import Pagination
from app.core.permissions import (
    ALL_WORKSPACE_ROLES,
    WORKSPACE_OWNER_ROLES,
    WORKSPACE_WRITE_ROLES,
    verify_workspace_role,
)
from app.models.enums import ProjectStatus, WorkspaceRole
from app.models.models import Project, User
from app.repositories.project_repository import ProjectRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.base import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate


class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        workspace_repo: WorkspaceRepository,
        member_repo: WorkspaceMemberRepository,
    ) -> None:
        self.project_repo = project_repo
        self.workspace_repo = workspace_repo
        self.member_repo = member_repo

    async def _verify_workspace(
        self,
        db: AsyncSession,
        workspace_id: int,
        user_id: int,
        allowed_roles: frozenset[WorkspaceRole],
    ) -> None:
        await verify_workspace_role(
            db,
            self.workspace_repo,
            self.member_repo,
            workspace_id=workspace_id,
            user_id=user_id,
            allowed_roles=allowed_roles,
        )

    async def _get_project_for_role(
        self,
        db: AsyncSession,
        project_id: int,
        current_user: User,
        allowed_roles: frozenset[WorkspaceRole],
    ) -> Project:
        project = await self.project_repo.get_by_id(db, id=project_id)
        if not project:
            raise NotFoundException(messages.MSG_PROJECT_NOT_FOUND)
        await self._verify_workspace(
            db,
            workspace_id=project.workspace_id,
            user_id=current_user.id,
            allowed_roles=allowed_roles,
        )
        return project

    async def create_project(
        self,
        db: AsyncSession,
        workspace_id: int,
        current_user: User,
        payload: ProjectCreate,
    ) -> Project:
        await self._verify_workspace(
            db,
            workspace_id=workspace_id,
            user_id=current_user.id,
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
        await self._verify_workspace(
            db,
            workspace_id=workspace_id,
            user_id=current_user.id,
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
        return await self._get_project_for_role(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=ALL_WORKSPACE_ROLES,
        )

    async def update_project(
        self,
        db: AsyncSession,
        project_id: int,
        current_user: User,
        payload: ProjectUpdate,
    ) -> Project:
        project = await self._get_project_for_role(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
        )
        return await self.project_repo.update(db, db_obj=project, obj_in=payload)

    async def archive_project(
        self,
        db: AsyncSession,
        project_id: int,
        current_user: User,
    ) -> Project:
        project = await self._get_project_for_role(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
        )
        return await self.project_repo.update(
            db,
            db_obj=project,
            obj_in={"status": ProjectStatus.ARCHIVED},
        )

    async def delete_project(
        self,
        db: AsyncSession,
        project_id: int,
        current_user: User,
    ) -> None:
        project = await self._get_project_for_role(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_OWNER_ROLES,
        )
        await self.project_repo.delete(db, id=project.id)
