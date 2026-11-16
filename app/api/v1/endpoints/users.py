from fastapi import APIRouter, status

from app.core.dependencies import (
    AdminUserDep,
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
    summary="Lấy thông tin hồ sơ người dùng hiện tại",
    responses={
        200: {"description": "Thông tin người dùng"},
        401: {"description": "Chưa xác thực"},
        403: {"description": "Tài khoản đã bị vô hiệu hóa"},
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
    summary="Cập nhật hồ sơ người dùng hiện tại",
    responses={
        200: {"description": "Cập nhật hồ sơ thành công"},
        401: {"description": "Chưa xác thực"},
        422: {"description": "Dữ liệu không hợp lệ (ví dụ full_name=null)"},
    },
)
async def update_me(
    payload: UserUpdate,
    current_user: CurrentActiveUserDep,
    db: DbSession,
    service: UserServiceDep,
) -> UserResponse:
    return await service.update_profile(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Đổi mật khẩu người dùng hiện tại",
    responses={
        204: {"description": "Đổi mật khẩu thành công"},
        400: {"description": "Mật khẩu hiện tại không đúng hoặc mật khẩu mới trùng cũ"},
        401: {"description": "Chưa xác thực"},
    },
)
async def change_my_password(
    payload: PasswordChange,
    current_user: CurrentActiveUserDep,
    db: DbSession,
    service: UserServiceDep,
) -> None:
    await service.change_password(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.get(
    "/admin/check",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Kiểm tra quyền quản trị viên hệ thống (RBAC Admin)",
    responses={
        200: {"description": "Xác thực quyền ADMIN thành công"},
        401: {"description": "Chưa xác thực"},
        403: {"description": "Không có quyền quản trị viên"},
    },
)
async def check_admin_access(
    admin_user: AdminUserDep,
) -> UserResponse:
    return UserResponse.model_validate(admin_user)
