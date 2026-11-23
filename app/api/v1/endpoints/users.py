from fastapi import APIRouter, status

from app.core.dependencies import (
    CurrentActiveUserDep,
    DbSession,
    UserServiceDep,
)
from app.schemas.user import PasswordChange, UserResponse, UserUpdate

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Inactive user account"},
    },
)
async def get_me(
    current_user: CurrentActiveUserDep,
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current authenticated user profile",
    responses={
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error (e.g., null full_name)"},
    },
)
async def update_me(
    payload: UserUpdate,
    current_user: CurrentActiveUserDep,
    db: DbSession,
    service: UserServiceDep,
) -> UserResponse:
    updated_user = await service.update_profile(db, current_user, payload)
    return UserResponse.model_validate(updated_user)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change current authenticated user password",
    responses={
        400: {"description": "Incorrect current password"},
        401: {"description": "Not authenticated"},
    },
)
async def change_my_password(
    payload: PasswordChange,
    current_user: CurrentActiveUserDep,
    db: DbSession,
    service: UserServiceDep,
) -> None:
    await service.change_password(db, current_user, payload)
