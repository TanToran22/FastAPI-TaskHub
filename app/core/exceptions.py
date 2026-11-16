from typing import Any

from fastapi import status


class AppException(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: Any | None = None,
    ) -> None:
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundException(AppException):
    status_code: int = status.HTTP_404_NOT_FOUND


class BadRequestException(AppException):
    status_code: int = status.HTTP_400_BAD_REQUEST


class ConflictException(AppException):
    status_code: int = status.HTTP_409_CONFLICT
