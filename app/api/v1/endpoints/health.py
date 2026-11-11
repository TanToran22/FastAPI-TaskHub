from typing import Any
 day-2-database

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

from fastapi import APIRouter
from app.core.config import settings
main

router = APIRouter()


day-2-database
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

@router.get("/health", summary="Health check endpoint")
async def health_check() -> Any:
    return {
        "status": "ok",
main
        "app_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }
