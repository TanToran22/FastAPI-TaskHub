import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.pagination import Pagination
from app.core.permissions import (
    ALL_WORKSPACE_ROLES,
    WORKSPACE_WRITE_ROLES,
    get_project_access,
    get_task_access,
)
from app.models.enums import TaskPriority, TaskStatus
from app.models.models import Task, User
from app.repositories.label_repository import LabelRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.schemas.base import PaginatedResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

logger = logging.getLogger("taskhub")


class TaskService:
    def __init__(
        self,
        task_repo: TaskRepository,
        label_repo: LabelRepository,
        member_repo: WorkspaceMemberRepository,
    ) -> None:
        self.task_repo = task_repo
        self.label_repo = label_repo
        self.member_repo = member_repo

    async def _validate_assignee(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        assignee_id: int | None,
    ) -> None:
        if assignee_id is None:
            return
        member = await self.member_repo.get_by_workspace_and_user(
            db, workspace_id=workspace_id, user_id=assignee_id
        )
        if not member:
            raise UnprocessableEntityException(
                messages.MSG_ASSIGNEE_NOT_WORKSPACE_MEMBER
            )

    async def create_task(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        payload: TaskCreate,
    ) -> Task:
        project, _ = await get_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
            require_active=True,
        )
        await self._validate_assignee(
            db, workspace_id=project.workspace_id, assignee_id=payload.assignee_id
        )
        create_data = payload.model_dump(exclude_unset=True)
        create_data["project_id"] = project.id
        create_data["created_by"] = current_user.id
        create_data["status"] = TaskStatus.TODO
        task = await self.task_repo.create(db, obj_in=create_data)
        loaded = await self.task_repo.get_by_id_with_labels(db, task_id=task.id)
        return loaded or task

    async def list_tasks(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        pagination: Pagination,
        statuses: list[TaskStatus] | None = None,
        priorities: list[TaskPriority] | None = None,
        assignee_id: int | None = None,
    ) -> PaginatedResponse[TaskResponse]:
        await get_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=ALL_WORKSPACE_ROLES,
        )
        items = await self.task_repo.get_multi_by_project(
            db,
            project_id=project_id,
            pagination=pagination,
            statuses=statuses,
            priorities=priorities,
            assignee_id=assignee_id,
        )
        total = await self.task_repo.count_by_project(
            db,
            project_id=project_id,
            statuses=statuses,
            priorities=priorities,
            assignee_id=assignee_id,
        )
        return PaginatedResponse[TaskResponse](
            items=[TaskResponse.model_validate(item) for item in items],
            total=total,
            skip=pagination.skip,
            limit=pagination.limit,
        )

    async def get_task(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        current_user: User,
    ) -> Task:
        task, _, _ = await get_task_access(
            db,
            task_id=task_id,
            current_user=current_user,
            allowed_roles=ALL_WORKSPACE_ROLES,
            load_labels=True,
        )
        return task

    async def patch_task(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        current_user: User,
        payload: TaskUpdate,
    ) -> Task:
        task, project, _ = await get_task_access(
            db,
            task_id=task_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
            require_active=True,
            load_labels=True,
        )
        update_data = payload.model_dump(exclude_unset=True)
        if "assignee_id" in update_data:
            await self._validate_assignee(
                db,
                workspace_id=project.workspace_id,
                assignee_id=update_data["assignee_id"],
            )
        updated = await self.task_repo.update(db, db_obj=task, obj_in=update_data)
        loaded = await self.task_repo.get_by_id_with_labels(db, task_id=updated.id)
        return loaded or updated

    async def delete_task(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        current_user: User,
    ) -> None:
        task, _, _ = await get_task_access(
            db,
            task_id=task_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
            require_active=True,
        )
        await self.task_repo.delete(db, id=task.id)

    async def assign_label(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        label_id: int,
        current_user: User,
    ) -> Task:
        task, project, _ = await get_task_access(
            db,
            task_id=task_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
            require_active=True,
        )
        label = await self.label_repo.get_by_id_and_project(
            db, label_id=label_id, project_id=project.id
        )
        if not label:
            raise NotFoundException(messages.MSG_LABEL_NOT_FOUND)

        try:
            await self.label_repo.assign_to_task(db, task_id=task.id, label_id=label.id)
        except IntegrityError as exc:
            await db.rollback()
            logger.warning("Duplicate label assignment: %s", exc.orig)
            raise ConflictException(messages.MSG_TASK_LABEL_ALREADY_ASSIGNED) from exc

        loaded = await self.task_repo.get_by_id_with_labels(db, task_id=task.id)
        return loaded or task

    async def remove_label(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        label_id: int,
        current_user: User,
    ) -> None:
        task, _, _ = await get_task_access(
            db,
            task_id=task_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
            require_active=True,
        )
        deleted_rows = await self.label_repo.remove_from_task(
            db, task_id=task.id, label_id=label_id
        )
        if deleted_rows == 0:
            raise NotFoundException(messages.MSG_TASK_LABEL_NOT_ASSIGNED)
