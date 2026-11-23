import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

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
        if exc.status_code >= 500:
            logger.error("AppException %s: %s", exc.status_code, exc.message)
        else:
            logger.warning("AppException %s: %s", exc.status_code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    application.include_router(api_router, prefix=settings.API_V1_STR)
    return application


app = create_application()
