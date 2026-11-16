from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants, messages, security
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    UnauthorizedException,
)
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    TokenRefreshRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def register(
        self,
        db: AsyncSession,
        payload: UserRegister,
    ) -> UserResponse:
        normalized_email = payload.email.lower()
        existing = await self.user_repository.get_by_email(db, normalized_email)
        if existing:
            raise ConflictException(messages.MSG_EMAIL_ALREADY_REGISTERED)

        user_data = {
            "email": normalized_email,
            "full_name": payload.full_name,
            "hashed_password": security.get_password_hash(payload.password),
        }
        try:
            user = await self.user_repository.create(db, obj_in=user_data)
            await db.commit()
            return UserResponse.model_validate(user)
        except IntegrityError as exc:
            await db.rollback()
            raise ConflictException(messages.MSG_EMAIL_ALREADY_REGISTERED) from exc

    async def login(
        self,
        db: AsyncSession,
        payload: UserLogin,
    ) -> TokenResponse:
        user = await self.user_repository.get_by_email(db, payload.email)
        if not user or not security.verify_password(
            payload.password, user.hashed_password
        ):
            raise UnauthorizedException(messages.MSG_INVALID_CREDENTIALS)

        if not user.is_active:
            raise ForbiddenException(messages.MSG_INACTIVE_USER)

        return TokenResponse(
            access_token=security.create_access_token(user.id),
            refresh_token=security.create_refresh_token(user.id),
        )

    async def refresh_tokens(
        self,
        db: AsyncSession,
        payload: TokenRefreshRequest,
    ) -> TokenResponse:
        decoded = security.decode_token(payload.refresh_token)
        if decoded.get("type") != constants.TOKEN_TYPE_REFRESH:
            raise UnauthorizedException(messages.MSG_INVALID_REFRESH_TOKEN)

        sub = decoded.get("sub")
        if sub is None or not str(sub).isdigit():
            raise UnauthorizedException(messages.MSG_INVALID_REFRESH_TOKEN)

        user = await self.user_repository.get_by_id(db, item_id=int(sub))
        if not user:
            raise UnauthorizedException(messages.MSG_INVALID_REFRESH_TOKEN)

        if not user.is_active:
            raise ForbiddenException(messages.MSG_INACTIVE_USER)

        return TokenResponse(
            access_token=security.create_access_token(user.id),
            refresh_token=security.create_refresh_token(user.id),
        )
