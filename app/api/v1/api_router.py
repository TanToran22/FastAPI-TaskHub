from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    comments,
    health,
    labels,
    projects,
    tasks,
    users,
    workspaces,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])
api_router.include_router(
    projects.workspace_projects_router,
    prefix="/workspaces/{workspace_id}/projects",
    tags=["Projects"],
)
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(
    tasks.project_tasks_router,
    prefix="/projects/{project_id}/tasks",
    tags=["Tasks"],
)
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(
    labels.project_labels_router,
    prefix="/projects/{project_id}/labels",
    tags=["Labels"],
)
api_router.include_router(labels.router, prefix="/labels", tags=["Labels"])
api_router.include_router(
    comments.task_comments_router,
    prefix="/tasks/{task_id}/comments",
    tags=["Comments"],
)
api_router.include_router(comments.router, prefix="/comments", tags=["Comments"])
