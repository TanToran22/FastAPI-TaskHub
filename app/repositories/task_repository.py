from app.models.models import Task
from app.repositories.base import BaseRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskRepository(BaseRepository[Task, TaskCreate, TaskUpdate]):
    def __init__(self) -> None:
        super().__init__(model=Task)
