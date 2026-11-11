from typing import Any


class AppException(Exception):
    def __init__(self, message: str, details: Any | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundException(AppException):
    pass


class BadRequestException(AppException):
    pass


class ConflictException(AppException):
    pass
