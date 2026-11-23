from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages, security
from app.core.exceptions import BadRequestException
from app.models.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import PasswordChange, UserUpdate


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def update_profile(
        self,
        db: AsyncSession,
        current_user: User,
        payload: UserUpdate,
    ) -> User:
        return await self.user_repository.update(
            db, db_obj=current_user, obj_in=payload
        )

    async def change_password(
        self,
        db: AsyncSession,
        current_user: User,
        payload: PasswordChange,
    ) -> None:
        is_valid = await run_in_threadpool(
            security.verify_password,
            payload.current_password,
            current_user.hashed_password,
        )
        if not is_valid:
            raise BadRequestException(messages.MSG_INCORRECT_CURRENT_PASSWORD)

        new_hashed = await run_in_threadpool(
            security.get_password_hash, payload.new_password
        )
        await self.user_repository.update_password(
            db, db_obj=current_user, hashed_password=new_hashed
        )
