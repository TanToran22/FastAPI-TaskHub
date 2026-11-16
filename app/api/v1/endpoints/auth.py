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
    summary="Đăng ký tài khoản người dùng mới",
    responses={
        201: {"description": "Đăng ký thành công"},
        409: {"description": "Email đã tồn tại trong hệ thống"},
        422: {"description": "Dữ liệu đầu vào không hợp lệ"},
    },
)
async def register(
    payload: UserRegister,
    db: DbSession,
    service: AuthServiceDep,
) -> UserResponse:
    return await service.register(db=db, payload=payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập và nhận JWT Access + Refresh Token",
    responses={
        200: {"description": "Đăng nhập thành công"},
        401: {"description": "Email hoặc mật khẩu không chính xác"},
        403: {"description": "Tài khoản đã bị vô hiệu hóa"},
    },
)
async def login(
    payload: UserLogin,
    db: DbSession,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.login(db=db, payload=payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Cấp lại cặp Access Token và Refresh Token mới",
    responses={
        200: {"description": "Làm mới token thành công"},
        401: {"description": "Refresh token không hợp lệ hoặc đã hết hạn"},
        403: {"description": "Tài khoản đã bị vô hiệu hóa"},
    },
)
async def refresh_token(
    payload: TokenRefreshRequest,
    db: DbSession,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.refresh_tokens(db=db, payload=payload)
