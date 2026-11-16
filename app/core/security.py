from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core import constants, messages
from app.core.config import settings
from app.core.exceptions import UnauthorizedException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: int | str) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=constants.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode: dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "type": constants.TOKEN_TYPE_ACCESS,
    }
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=constants.JWT_ALGORITHM,
    )


def create_refresh_token(subject: int | str) -> str:
    expire = datetime.now(UTC) + timedelta(days=constants.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode: dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "type": constants.TOKEN_TYPE_REFRESH,
    }
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=constants.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[constants.JWT_ALGORITHM],
        )
        return payload
    except JWTError as exc:
        raise UnauthorizedException(messages.MSG_INVALID_TOKEN) from exc
