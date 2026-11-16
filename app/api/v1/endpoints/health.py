from fastapi import APIRouter, status
from sqlalchemy import text

from app.core.config import settings
from app.core.dependencies import DbSession
from app.schemas.base import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
)
async def health_check(db: DbSession) -> HealthResponse:
    await db.execute(text("SELECT 1"))
    return HealthResponse(
        status="ok",
        database="connected",
        app_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
    )
