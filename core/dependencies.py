from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService

_task_repo_singleton = TaskRepository()


def get_task_repository() -> TaskRepository:
    return _task_repo_singleton


def get_task_service() -> TaskService:
    return TaskService(repository=get_task_repository())
