from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import settings
from app.core.dependencies import DbSession

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    database: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
)
async def health_check(db: DbSession) -> HealthResponse:
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"disconnected: {exc}"

    return HealthResponse(
        status="ok",
        app_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        database=db_status,
    )
