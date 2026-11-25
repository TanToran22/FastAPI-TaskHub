from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants, messages, security
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.models.enums import UserRole
from app.models.models import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.label_repository import LabelRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.services.auth_service import AuthService
from app.services.comment_service import CommentService
from app.services.label_service import LabelService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.services.workspace_service import WorkspaceService

bearer_scheme = HTTPBearer(auto_error=False)

_task_repo_singleton = TaskRepository()
_user_repo_singleton = UserRepository()
_workspace_repo_singleton = WorkspaceRepository()
_workspace_member_repo_singleton = WorkspaceMemberRepository()
_project_repo_singleton = ProjectRepository()
_label_repo_singleton = LabelRepository()
_comment_repo_singleton = CommentRepository()


def get_task_repository() -> TaskRepository:
    return _task_repo_singleton


def get_user_repository() -> UserRepository:
    return _user_repo_singleton


def get_workspace_repository() -> WorkspaceRepository:
    return _workspace_repo_singleton


def get_workspace_member_repository() -> WorkspaceMemberRepository:
    return _workspace_member_repo_singleton


def get_project_repository() -> ProjectRepository:
    return _project_repo_singleton


def get_label_repository() -> LabelRepository:
    return _label_repo_singleton


def get_comment_repository() -> CommentRepository:
    return _comment_repo_singleton


def get_task_service() -> TaskService:
    return TaskService(
        task_repo=get_task_repository(),
        label_repo=get_label_repository(),
        member_repo=get_workspace_member_repository(),
    )


def get_label_service() -> LabelService:
    return LabelService(label_repo=get_label_repository())


def get_comment_service() -> CommentService:
    return CommentService(comment_repo=get_comment_repository())


def get_auth_service() -> AuthService:
    return AuthService(user_repository=get_user_repository())


def get_user_service() -> UserService:
    return UserService(user_repository=get_user_repository())


def get_workspace_service() -> WorkspaceService:
    return WorkspaceService(
        workspace_repo=get_workspace_repository(),
        member_repo=get_workspace_member_repository(),
        user_repo=get_user_repository(),
    )


def get_project_service() -> ProjectService:
    return ProjectService(project_repo=get_project_repository())


DbSession = Annotated[AsyncSession, Depends(get_db)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
LabelServiceDep = Annotated[LabelService, Depends(get_label_service)]
CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
WorkspaceServiceDep = Annotated[WorkspaceService, Depends(get_workspace_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    if not credentials or credentials.scheme.lower() != constants.TOKEN_TYPE_BEARER:
        raise UnauthorizedException(messages.MSG_INVALID_TOKEN)

    payload = security.decode_token(credentials.credentials)
    if payload.get("type") != constants.TOKEN_TYPE_ACCESS:
        raise UnauthorizedException(messages.MSG_INVALID_TOKEN)

    sub = payload.get("sub")
    if sub is None or not str(sub).isdigit():
        raise UnauthorizedException(messages.MSG_INVALID_TOKEN)

    user = await user_repo.get_by_id(db, id=int(sub))
    if not user:
        raise UnauthorizedException(messages.MSG_INVALID_TOKEN)
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise ForbiddenException(messages.MSG_INACTIVE_USER)
    return current_user


async def require_admin_role(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException(messages.MSG_FORBIDDEN_ADMIN_ONLY)
    return current_user


CurrentActiveUserDep = Annotated[User, Depends(get_current_active_user)]
AdminUserDep = Annotated[User, Depends(require_admin_role)]
