import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.api_router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("taskhub")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up TaskHub Application...")
    yield
    logger.info("Shutting down TaskHub Application...")
    await engine.dispose()


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    @application.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        log_msg = (
            f"AppException ({exc.status_code}): "
            f"path={request.url.path} message={exc.message}"
        )
        if exc.status_code >= 500:
            logger.error(log_msg)
        else:
            logger.warning(log_msg)

        content: dict[str, Any] = {"detail": exc.message}
        if exc.details is not None:
            content["details"] = exc.details

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
        )

    application.include_router(api_router, prefix=settings.API_V1_STR)
    return application


app = create_application()
