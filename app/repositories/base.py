from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.core.pagination import Pagination

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: Any) -> ModelType | None:
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        pagination: Pagination | None = None,
    ) -> list[ModelType]:
        pag = pagination or Pagination()
        order_cols = [self.model.id.desc()]
        if hasattr(self.model, "created_at"):
            order_cols.insert(0, self.model.created_at.desc())

        query = (
            select(self.model).order_by(*order_cols).offset(pag.skip).limit(pag.limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count(self, db: AsyncSession) -> int:
        query = select(func.count(self.model.id))
        result = await db.execute(query)
        return result.scalar_one()

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchemaType | dict[str, Any]
    ) -> ModelType:
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump(exclude_unset=True)

        db_obj = self.model(**create_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: Any) -> ModelType | None:
        obj = await self.get_by_id(db, id=id)
        if obj:
            await db.delete(obj)
            await db.flush()
        return obj
