from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination
from app.core.permissions import (
    ALL_WORKSPACE_ROLES,
    WORKSPACE_WRITE_ROLES,
    get_comment_access,
    get_task_access,
)
from app.models.models import Comment, User
from app.repositories.comment_repository import CommentRepository
from app.schemas.base import PaginatedResponse
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate


class CommentService:
    def __init__(self, comment_repo: CommentRepository) -> None:
        self.comment_repo = comment_repo

    async def create_comment(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        current_user: User,
        payload: CommentCreate,
    ) -> Comment:
        task, _, _ = await get_task_access(
            db,
            task_id=task_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
            require_active=True,
        )
        return await self.comment_repo.create(
            db,
            obj_in={
                "task_id": task.id,
                "author_id": current_user.id,
                "content": payload.content,
            },
        )

    async def list_comments(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        current_user: User,
        pagination: Pagination,
    ) -> PaginatedResponse[CommentResponse]:
        task, _, _ = await get_task_access(
            db,
            task_id=task_id,
            current_user=current_user,
            allowed_roles=ALL_WORKSPACE_ROLES,
        )
        items = await self.comment_repo.get_multi_by_task(
            db, task_id=task.id, pagination=pagination
        )
        total = await self.comment_repo.count_by_task(db, task_id=task.id)
        return PaginatedResponse[CommentResponse](
            items=[CommentResponse.model_validate(item) for item in items],
            total=total,
            skip=pagination.skip,
            limit=pagination.limit,
        )

    async def update_comment(
        self,
        db: AsyncSession,
        *,
        comment_id: int,
        current_user: User,
        payload: CommentUpdate,
    ) -> Comment:
        comment, _, _ = await get_comment_access(
            db,
            comment_id=comment_id,
            current_user=current_user,
            require_write=True,
            require_active=True,
        )
        return await self.comment_repo.update(db, db_obj=comment, obj_in=payload)

    async def delete_comment(
        self,
        db: AsyncSession,
        *,
        comment_id: int,
        current_user: User,
    ) -> None:
        comment, _, _ = await get_comment_access(
            db,
            comment_id=comment_id,
            current_user=current_user,
            require_write=True,
            require_active=True,
        )
        await self.comment_repo.delete(db, id=comment.id)
