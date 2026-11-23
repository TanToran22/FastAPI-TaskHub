from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.enums import WorkspaceRole
from app.models.models import Workspace, WorkspaceMember
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository

ALL_WORKSPACE_ROLES: frozenset[WorkspaceRole] = frozenset(
    {WorkspaceRole.OWNER, WorkspaceRole.EDITOR, WorkspaceRole.VIEWER}
)
WORKSPACE_WRITE_ROLES: frozenset[WorkspaceRole] = frozenset(
    {WorkspaceRole.OWNER, WorkspaceRole.EDITOR}
)
WORKSPACE_OWNER_ROLES: frozenset[WorkspaceRole] = frozenset({WorkspaceRole.OWNER})


async def verify_workspace_role(
    db: AsyncSession,
    workspace_repo: WorkspaceRepository,
    member_repo: WorkspaceMemberRepository,
    workspace_id: int,
    user_id: int,
    allowed_roles: frozenset[WorkspaceRole] = ALL_WORKSPACE_ROLES,
) -> tuple[Workspace, WorkspaceMember]:
    workspace = await workspace_repo.get_by_id(db, id=workspace_id)
    if not workspace:
        raise NotFoundException(messages.MSG_WORKSPACE_NOT_FOUND)

    member = await member_repo.get_by_workspace_and_user(
        db, workspace_id=workspace_id, user_id=user_id
    )
    if not member or member.role not in allowed_roles:
        raise ForbiddenException(messages.MSG_WORKSPACE_FORBIDDEN)

    return workspace, member
