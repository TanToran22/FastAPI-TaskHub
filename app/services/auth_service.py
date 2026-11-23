import logging

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants, messages, security
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    UnauthorizedException,
)
from app.models.enums import UserRole
from app.models.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    TokenRefreshRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
)

logger = logging.getLogger("taskhub")


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def register_user(
        self,
        db: AsyncSession,
        payload: UserRegister,
    ) -> User:
        normalized_email = payload.email.lower()
        existing_user = await self.user_repository.get_by_email(
            db, email=normalized_email
        )
        if existing_user:
            raise ConflictException(messages.MSG_EMAIL_ALREADY_EXISTS)

        hashed_password = await run_in_threadpool(
            security.get_password_hash, payload.password
        )
        create_data = {
            "email": normalized_email,
            "full_name": payload.full_name,
            "hashed_password": hashed_password,
            "role": UserRole.MEMBER,
            "is_active": True,
        }
        try:
            return await self.user_repository.create(db, obj_in=create_data)
        except IntegrityError as exc:
            await db.rollback()
            logger.warning(
                "IntegrityError during user registration: %s",
                exc.orig,
            )
            raise ConflictException(messages.MSG_EMAIL_ALREADY_EXISTS) from exc

    async def authenticate_user(
        self,
        db: AsyncSession,
        payload: UserLogin,
    ) -> TokenResponse:
        user = await self.user_repository.get_by_email(db, email=payload.email.lower())
        target_hash = user.hashed_password if user else security.DUMMY_PASSWORD_HASH
        is_password_valid = await run_in_threadpool(
            security.verify_password, payload.password, target_hash
        )

        if not user or not is_password_valid:
            raise UnauthorizedException(messages.MSG_INVALID_CREDENTIALS)

        if not user.is_active:
            raise ForbiddenException(messages.MSG_INACTIVE_USER)

        access_token = security.create_access_token(subject=user.id)
        refresh_token = security.create_refresh_token(subject=user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_tokens(
        self,
        db: AsyncSession,
        payload: TokenRefreshRequest,
    ) -> TokenResponse:
        token_data = security.decode_token(payload.refresh_token)
        if token_data.get("type") != constants.TOKEN_TYPE_REFRESH:
            raise UnauthorizedException(messages.MSG_INVALID_REFRESH_TOKEN)

        sub = token_data.get("sub")
        if sub is None or not str(sub).isdigit():
            raise UnauthorizedException(messages.MSG_INVALID_REFRESH_TOKEN)

        user = await self.user_repository.get_by_id(db, id=int(sub))
        if not user:
            raise UnauthorizedException(messages.MSG_INVALID_REFRESH_TOKEN)

        if not user.is_active:
            raise ForbiddenException(messages.MSG_INACTIVE_USER)

        access_token = security.create_access_token(subject=user.id)
        refresh_token = security.create_refresh_token(subject=user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
