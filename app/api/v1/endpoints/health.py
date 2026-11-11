from typing import Any
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Health check endpoint")
async def health_check() -> Any:
    return {
        "status": "ok",
        "app_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }
