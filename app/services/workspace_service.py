import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.core.pagination import Pagination
from app.core.permissions import (
    ALL_WORKSPACE_ROLES,
    WORKSPACE_OWNER_ROLES,
    verify_workspace_role,
)
from app.models.enums import WorkspaceRole
from app.models.models import User, Workspace, WorkspaceMember
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.base import PaginatedResponse
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberInvite,
    WorkspaceMemberResponse,
    WorkspaceMemberRoleUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)

logger = logging.getLogger("taskhub")


class WorkspaceService:
    def __init__(
        self,
        workspace_repo: WorkspaceRepository,
        member_repo: WorkspaceMemberRepository,
        user_repo: UserRepository,
    ) -> None:
        self.workspace_repo = workspace_repo
        self.member_repo = member_repo
        self.user_repo = user_repo

    async def create_workspace(
        self,
        db: AsyncSession,
        current_user: User,
        payload: WorkspaceCreate,
    ) -> Workspace:
        workspace = await self.workspace_repo.create(
            db,
            obj_in={"name": payload.name, "owner_id": current_user.id},
        )
        # Always add creator as OWNER member in the same transaction
        await self.member_repo.create(
            db,
            obj_in={
                "workspace_id": workspace.id,
                "user_id": current_user.id,
                "role": WorkspaceRole.OWNER,
            },
        )
        return workspace

    async def list_workspaces(
        self,
        db: AsyncSession,
        current_user: User,
        pagination: Pagination,
    ) -> PaginatedResponse[WorkspaceResponse]:
        items = await self.workspace_repo.get_multi_by_user(
            db, user_id=current_user.id, pagination=pagination
        )
        total = await self.workspace_repo.count_by_user(db, user_id=current_user.id)
        return PaginatedResponse[WorkspaceResponse](
            items=[WorkspaceResponse.model_validate(item) for item in items],
            total=total,
            skip=pagination.skip,
            limit=pagination.limit,
        )

    async def get_workspace(
        self,
        db: AsyncSession,
        workspace_id: int,
        current_user: User,
    ) -> Workspace:
        workspace, _ = await verify_workspace_role(
            db,
            self.workspace_repo,
            self.member_repo,
            workspace_id=workspace_id,
            user_id=current_user.id,
            allowed_roles=ALL_WORKSPACE_ROLES,
        )
        return workspace

    async def update_workspace(
        self,
        db: AsyncSession,
        workspace_id: int,
        current_user: User,
        payload: WorkspaceUpdate,
    ) -> Workspace:
        workspace, _ = await verify_workspace_role(
            db,
            self.workspace_repo,
            self.member_repo,
            workspace_id=workspace_id,
            user_id=current_user.id,
            allowed_roles=WORKSPACE_OWNER_ROLES,
        )
        return await self.workspace_repo.update(db, db_obj=workspace, obj_in=payload)

    async def delete_workspace(
        self,
        db: AsyncSession,
        workspace_id: int,
        current_user: User,
    ) -> None:
        workspace, _ = await verify_workspace_role(
            db,
            self.workspace_repo,
            self.member_repo,
            workspace_id=workspace_id,
            user_id=current_user.id,
            allowed_roles=WORKSPACE_OWNER_ROLES,
        )
        await self.workspace_repo.delete(db, id=workspace.id)

    async def list_members(
        self,
        db: AsyncSession,
        workspace_id: int,
        current_user: User,
        pagination: Pagination,
    ) -> PaginatedResponse[WorkspaceMemberResponse]:
        await verify_workspace_role(
            db,
            self.workspace_repo,
            self.member_repo,
            workspace_id=workspace_id,
            user_id=current_user.id,
            allowed_roles=ALL_WORKSPACE_ROLES,
        )
        items = await self.member_repo.get_multi_by_workspace(
            db, workspace_id=workspace_id, pagination=pagination
        )
        total = await self.member_repo.count_by_workspace(db, workspace_id=workspace_id)
        return PaginatedResponse[WorkspaceMemberResponse](
            items=[WorkspaceMemberResponse.model_validate(item) for item in items],
            total=total,
            skip=pagination.skip,
            limit=pagination.limit,
        )

    async def invite_member(
        self,
        db: AsyncSession,
        workspace_id: int,
        current_user: User,
        payload: WorkspaceMemberInvite,
    ) -> WorkspaceMember:
        await verify_workspace_role(
            db,
            self.workspace_repo,
            self.member_repo,
            workspace_id=workspace_id,
            user_id=current_user.id,
            allowed_roles=WORKSPACE_OWNER_ROLES,
        )

        target_user = await self.user_repo.get_by_email(db, email=payload.email.lower())
        if not target_user:
            raise NotFoundException(messages.MSG_USER_NOT_FOUND)

        existing = await self.member_repo.get_by_workspace_and_user(
            db, workspace_id=workspace_id, user_id=target_user.id
        )
        if existing:
            raise ConflictException(messages.MSG_WORKSPACE_MEMBER_ALREADY_EXISTS)

        try:
            return await self.member_repo.create(
                db,
                obj_in={
                    "workspace_id": workspace_id,
                    "user_id": target_user.id,
                    "role": payload.role,
                },
            )
        except IntegrityError as exc:
            await db.rollback()
            logger.warning(
                "IntegrityError during workspace member invite: %s",
                exc.orig,
            )
            raise ConflictException(
                messages.MSG_WORKSPACE_MEMBER_ALREADY_EXISTS
            ) from exc

    async def update_member_role(
        self,
        db: AsyncSession,
        workspace_id: int,
        target_user_id: int,
        current_user: User,
        payload: WorkspaceMemberRoleUpdate,
    ) -> WorkspaceMember:
        await verify_workspace_role(
            db,
            self.workspace_repo,
            self.member_repo,
            workspace_id=workspace_id,
            user_id=current_user.id,
            allowed_roles=WORKSPACE_OWNER_ROLES,
        )

        member = await self.member_repo.get_by_workspace_and_user(
            db, workspace_id=workspace_id, user_id=target_user_id
        )
        if not member:
            raise NotFoundException(messages.MSG_WORKSPACE_MEMBER_NOT_FOUND)

        if member.role == WorkspaceRole.OWNER:
            raise BadRequestException(messages.MSG_CANNOT_MODIFY_OWNER_ROLE)

        return await self.member_repo.update(db, db_obj=member, obj_in=payload)

    async def remove_member(
        self,
        db: AsyncSession,
        workspace_id: int,
        target_user_id: int,
        current_user: User,
    ) -> None:
        await verify_workspace_role(
            db,
            self.workspace_repo,
            self.member_repo,
            workspace_id=workspace_id,
            user_id=current_user.id,
            allowed_roles=WORKSPACE_OWNER_ROLES,
        )

        member = await self.member_repo.get_by_workspace_and_user(
            db, workspace_id=workspace_id, user_id=target_user_id
        )
        if not member:
            raise NotFoundException(messages.MSG_WORKSPACE_MEMBER_NOT_FOUND)

        if member.role == WorkspaceRole.OWNER:
            raise BadRequestException(messages.MSG_CANNOT_REMOVE_WORKSPACE_OWNER)

        await self.member_repo.delete(db, id=member.id)
