from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> Any:
    await db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected",
        "app_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }
