from fastapi import APIRouter, status

from app.core.dependencies import AuthServiceDep, DbSession
from app.schemas.user import (
    TokenRefreshRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    responses={
        409: {"description": "Email already registered"},
    },
)
async def register(
    payload: UserRegister,
    db: DbSession,
    service: AuthServiceDep,
) -> UserResponse:
    user = await service.register_user(db, payload)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and return JWT tokens",
    responses={
        401: {"description": "Invalid email or password"},
        403: {"description": "Inactive user account"},
    },
)
async def login(
    payload: UserLogin,
    db: DbSession,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.authenticate_user(db, payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token using a valid refresh token",
    responses={
        401: {"description": "Invalid or expired refresh token"},
        403: {"description": "Inactive user account"},
    },
)
async def refresh_token(
    payload: TokenRefreshRequest,
    db: DbSession,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.refresh_tokens(db, payload)
