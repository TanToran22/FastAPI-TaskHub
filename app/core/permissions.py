from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import messages
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.enums import ProjectStatus, UserRole, WorkspaceRole
from app.models.models import (
    Comment,
    Label,
    Project,
    Task,
    User,
    Workspace,
    WorkspaceMember,
)

ALL_WORKSPACE_ROLES: frozenset[WorkspaceRole] = frozenset(
    {WorkspaceRole.OWNER, WorkspaceRole.EDITOR, WorkspaceRole.VIEWER}
)
WORKSPACE_WRITE_ROLES: frozenset[WorkspaceRole] = frozenset(
    {WorkspaceRole.OWNER, WorkspaceRole.EDITOR}
)
WORKSPACE_OWNER_ROLES: frozenset[WorkspaceRole] = frozenset({WorkspaceRole.OWNER})


def _check_membership_and_role(
    *,
    current_user: User,
    member_role: WorkspaceRole | None,
    allowed_roles: frozenset[WorkspaceRole],
    not_found_msg: str,
) -> WorkspaceRole | None:
    if current_user.role == UserRole.ADMIN:
        return member_role
    if member_role is None:
        # Return 404 consistently for outsiders to avoid leaking resource existence
        raise NotFoundException(not_found_msg)
    if member_role not in allowed_roles:
        raise ForbiddenException(messages.MSG_WORKSPACE_FORBIDDEN)
    return member_role


def _check_project_not_archived(project: Project, require_active: bool) -> None:
    if require_active and project.status == ProjectStatus.ARCHIVED:
        raise ConflictException(messages.MSG_PROJECT_ARCHIVED)


async def get_workspace_access(
    db: AsyncSession,
    *,
    workspace_id: int,
    current_user: User,
    allowed_roles: frozenset[WorkspaceRole] = ALL_WORKSPACE_ROLES,
) -> tuple[Workspace, WorkspaceRole | None]:
    stmt = (
        select(Workspace, WorkspaceMember.role)
        .outerjoin(
            WorkspaceMember,
            and_(
                WorkspaceMember.workspace_id == Workspace.id,
                WorkspaceMember.user_id == current_user.id,
            ),
        )
        .where(Workspace.id == workspace_id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise NotFoundException(messages.MSG_WORKSPACE_NOT_FOUND)

    workspace, member_role = row[0], row[1]
    role = _check_membership_and_role(
        current_user=current_user,
        member_role=member_role,
        allowed_roles=allowed_roles,
        not_found_msg=messages.MSG_WORKSPACE_NOT_FOUND,
    )
    return workspace, role


async def get_project_access(
    db: AsyncSession,
    *,
    project_id: int,
    current_user: User,
    allowed_roles: frozenset[WorkspaceRole] = ALL_WORKSPACE_ROLES,
    require_active: bool = False,
) -> tuple[Project, WorkspaceRole | None]:
    stmt = (
        select(Project, WorkspaceMember.role)
        .outerjoin(
            WorkspaceMember,
            and_(
                WorkspaceMember.workspace_id == Project.workspace_id,
                WorkspaceMember.user_id == current_user.id,
            ),
        )
        .where(Project.id == project_id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise NotFoundException(messages.MSG_PROJECT_NOT_FOUND)

    project, member_role = row[0], row[1]
    role = _check_membership_and_role(
        current_user=current_user,
        member_role=member_role,
        allowed_roles=allowed_roles,
        not_found_msg=messages.MSG_PROJECT_NOT_FOUND,
    )
    _check_project_not_archived(project, require_active)
    return project, role


async def get_task_access(
    db: AsyncSession,
    *,
    task_id: int,
    current_user: User,
    allowed_roles: frozenset[WorkspaceRole] = ALL_WORKSPACE_ROLES,
    require_active: bool = False,
    load_labels: bool = False,
) -> tuple[Task, Project, WorkspaceRole | None]:
    stmt = (
        select(Task, Project, WorkspaceMember.role)
        .join(Project, Task.project_id == Project.id)
        .outerjoin(
            WorkspaceMember,
            and_(
                WorkspaceMember.workspace_id == Project.workspace_id,
                WorkspaceMember.user_id == current_user.id,
            ),
        )
        .where(Task.id == task_id)
    )
    if load_labels:
        stmt = stmt.options(selectinload(Task.labels))

    row = (await db.execute(stmt)).first()
    if not row:
        raise NotFoundException(messages.MSG_TASK_NOT_FOUND)

    task, project, member_role = row[0], row[1], row[2]
    role = _check_membership_and_role(
        current_user=current_user,
        member_role=member_role,
        allowed_roles=allowed_roles,
        not_found_msg=messages.MSG_TASK_NOT_FOUND,
    )
    _check_project_not_archived(project, require_active)
    return task, project, role


async def get_label_access(
    db: AsyncSession,
    *,
    label_id: int,
    current_user: User,
    allowed_roles: frozenset[WorkspaceRole] = ALL_WORKSPACE_ROLES,
    require_active: bool = False,
) -> tuple[Label, Project, WorkspaceRole | None]:
    stmt = (
        select(Label, Project, WorkspaceMember.role)
        .join(Project, Label.project_id == Project.id)
        .outerjoin(
            WorkspaceMember,
            and_(
                WorkspaceMember.workspace_id == Project.workspace_id,
                WorkspaceMember.user_id == current_user.id,
            ),
        )
        .where(Label.id == label_id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise NotFoundException(messages.MSG_LABEL_NOT_FOUND)

    label, project, member_role = row[0], row[1], row[2]
    role = _check_membership_and_role(
        current_user=current_user,
        member_role=member_role,
        allowed_roles=allowed_roles,
        not_found_msg=messages.MSG_LABEL_NOT_FOUND,
    )
    _check_project_not_archived(project, require_active)
    return label, project, role


async def get_comment_access(
    db: AsyncSession,
    *,
    comment_id: int,
    current_user: User,
    require_write: bool = False,
    require_active: bool = False,
) -> tuple[Comment, Project, WorkspaceRole | None]:
    stmt = (
        select(Comment, Project, WorkspaceMember.role)
        .join(Task, Comment.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .outerjoin(
            WorkspaceMember,
            and_(
                WorkspaceMember.workspace_id == Project.workspace_id,
                WorkspaceMember.user_id == current_user.id,
            ),
        )
        .where(Comment.id == comment_id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise NotFoundException(messages.MSG_COMMENT_NOT_FOUND)

    comment, project, member_role = row[0], row[1], row[2]
    role = _check_membership_and_role(
        current_user=current_user,
        member_role=member_role,
        allowed_roles=ALL_WORKSPACE_ROLES,
        not_found_msg=messages.MSG_COMMENT_NOT_FOUND,
    )
    if require_write and not (
        current_user.role == UserRole.ADMIN
        or role == WorkspaceRole.OWNER
        or comment.author_id == current_user.id
    ):
        raise ForbiddenException(messages.MSG_COMMENT_FORBIDDEN)

    _check_project_not_archived(project, require_active)
    return comment, project, role
