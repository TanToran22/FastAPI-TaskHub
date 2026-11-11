import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.api_router import api_router
from app.core.config import settings
from app.core.exceptions import AppException, BadRequestException, NotFoundException

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


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    @application.exception_handler(NotFoundException)
    async def not_found_handler(
        request: Request, exc: NotFoundException
    ) -> JSONResponse:
        logger.warning(f"NotFound: path={request.url.path} message={exc.message}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @application.exception_handler(BadRequestException)
    async def bad_request_handler(
        request: Request, exc: BadRequestException
    ) -> JSONResponse:
        logger.warning(f"BadRequest: path={request.url.path} message={exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @application.exception_handler(AppException)
    async def generic_app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        logger.error(f"AppException: path={request.url.path} message={exc.message}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": exc.message},
        )

    application.include_router(api_router, prefix=settings.API_V1_STR)
    return application


app = create_application()
