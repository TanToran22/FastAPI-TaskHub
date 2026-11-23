from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserRegister, UserUpdate


class UserRepository(BaseRepository[User, UserRegister, UserUpdate]):
    def __init__(self) -> None:
        super().__init__(model=User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        query = select(User).where(User.email == email.lower())
        result = await db.execute(query)
        return result.scalars().first()

    async def update_password(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        hashed_password: str,
    ) -> User:
        db_obj.hashed_password = hashed_password
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
