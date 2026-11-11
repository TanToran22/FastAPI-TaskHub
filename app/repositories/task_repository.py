from datetime import UTC, datetime

from app.models.internal_task import InternalTask


class TaskRepository:
    def __init__(self) -> None:
        self._storage: dict[int, InternalTask] = {}
        self._id_counter: int = 1

    def count(self) -> int:
        return len(self._storage)

    def get_by_id(self, task_id: int) -> InternalTask | None:
        return self._storage.get(task_id)

    def get_all(self, skip: int = 0, limit: int = 100) -> list[InternalTask]:
        items = list(self._storage.values())
        return items[skip : skip + limit]

    def create(self, title: str, description: str | None) -> InternalTask:
        task_id = self._id_counter
        self._id_counter += 1
        item = InternalTask.create_new(
            task_id=task_id,
            title=title,
            description=description,
        )
        self._storage[task_id] = item
        return item

    def update(
        self,
        task_id: int,
        title: str | None = None,
        description: str | None = None,
        update_description: bool = False,
    ) -> InternalTask | None:
        item = self.get_by_id(task_id)
        if not item:
            return None
        if title is not None:
            item.title = title
        if update_description:
            item.description = description
        item.updated_at = datetime.now(UTC)
        return item

    def delete(self, task_id: int) -> bool:
        if task_id in self._storage:
            del self._storage[task_id]
            return True
        return False
