import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import ConflictException
from app.core.pagination import Pagination
from app.core.permissions import (
    ALL_WORKSPACE_ROLES,
    WORKSPACE_WRITE_ROLES,
    get_label_access,
    get_project_access,
)
from app.models.models import Label, User
from app.repositories.label_repository import LabelRepository
from app.schemas.base import PaginatedResponse
from app.schemas.label import LabelCreate, LabelResponse, LabelUpdate

logger = logging.getLogger("taskhub")


class LabelService:
    def __init__(self, label_repo: LabelRepository) -> None:
        self.label_repo = label_repo

    async def create_label(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        payload: LabelCreate,
    ) -> Label:
        await get_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
            require_active=True,
        )
        create_data = payload.model_dump()
        create_data["project_id"] = project_id
        try:
            return await self.label_repo.create(db, obj_in=create_data)
        except IntegrityError as exc:
            await db.rollback()
            logger.warning("Duplicate label name in project: %s", exc.orig)
            raise ConflictException(messages.MSG_LABEL_ALREADY_EXISTS) from exc

    async def list_labels(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        pagination: Pagination,
    ) -> PaginatedResponse[LabelResponse]:
        await get_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
            allowed_roles=ALL_WORKSPACE_ROLES,
        )
        items = await self.label_repo.get_multi_by_project(
            db, project_id=project_id, pagination=pagination
        )
        total = await self.label_repo.count_by_project(db, project_id=project_id)
        return PaginatedResponse[LabelResponse](
            items=[LabelResponse.model_validate(item) for item in items],
            total=total,
            skip=pagination.skip,
            limit=pagination.limit,
        )

    async def update_label(
        self,
        db: AsyncSession,
        *,
        label_id: int,
        current_user: User,
        payload: LabelUpdate,
    ) -> Label:
        label, _, _ = await get_label_access(
            db,
            label_id=label_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
            require_active=True,
        )
        try:
            return await self.label_repo.update(db, db_obj=label, obj_in=payload)
        except IntegrityError as exc:
            await db.rollback()
            logger.warning("Duplicate label name on update: %s", exc.orig)
            raise ConflictException(messages.MSG_LABEL_ALREADY_EXISTS) from exc

    async def delete_label(
        self,
        db: AsyncSession,
        *,
        label_id: int,
        current_user: User,
    ) -> None:
        label, _, _ = await get_label_access(
            db,
            label_id=label_id,
            current_user=current_user,
            allowed_roles=WORKSPACE_WRITE_ROLES,
            require_active=True,
        )
        await self.label_repo.delete(db, id=label.id)
