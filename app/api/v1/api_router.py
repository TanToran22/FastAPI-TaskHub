from fastapi import APIRouter
 day-2-database

from app.api.v1.endpoints import health, tasks

from app.api.v1.endpoints import health, sample
 main

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
 day-2-database
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])

api_router.include_router(sample.router, prefix="/samples", tags=["Samples"])
 main
