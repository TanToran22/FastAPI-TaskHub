from app.core import constants
from app.core.exceptions import NotFoundException
from app.models.internal_task import InternalTask
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def get_task_or_404(self, task_id: int) -> InternalTask:
        task = self.repository.get_by_id(task_id)
        if not task:
            raise NotFoundException(constants.MSG_TASK_NOT_FOUND)
        return task

    def list_tasks(self, skip: int = 0, limit: int = 100) -> list[InternalTask]:
        return self.repository.get_all(skip=skip, limit=limit)

    def create_task(self, payload: TaskCreate) -> InternalTask:
        return self.repository.create(
            title=payload.title,
            description=payload.description,
        )

    def patch_task(self, task_id: int, payload: TaskUpdate) -> InternalTask:
        self.get_task_or_404(task_id)

        update_data = payload.model_dump(exclude_unset=True)
        title = update_data.get("title")
        description = update_data.get("description")
        update_description = "description" in update_data

        updated = self.repository.update(
            task_id=task_id,
            title=title,
            description=description,
            update_description=update_description,
        )
        if not updated:
            raise NotFoundException(constants.MSG_TASK_NOT_FOUND)
        return updated

    def delete_task(self, task_id: int) -> None:
        deleted = self.repository.delete(task_id)
        if not deleted:
            raise NotFoundException(constants.MSG_TASK_NOT_FOUND)
