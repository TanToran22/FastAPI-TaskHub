from datetime import UTC, datetime

from app.models.internal_sample import InternalSample


class SampleRepository:
    def __init__(self) -> None:
        self._storage: dict[int, InternalSample] = {}
        self._id_counter: int = 1

    def get_by_id(self, sample_id: int) -> InternalSample | None:
        return self._storage.get(sample_id)

    def get_all(self, skip: int = 0, limit: int = 100) -> list[InternalSample]:
        items = list(self._storage.values())
        return items[skip : skip + limit]

    def create(self, title: str, description: str | None) -> InternalSample:
        sample_id = self._id_counter
        self._id_counter += 1
        item = InternalSample.create_new(
            sample_id=sample_id,
            title=title,
            description=description,
        )
        self._storage[sample_id] = item
        return item

    def update(
        self,
        sample_id: int,
        title: str | None = None,
        description: str | None = None,
        update_description: bool = False,
    ) -> InternalSample | None:
        item = self.get_by_id(sample_id)
        if not item:
            return None
        if title is not None:
            item.title = title
        if update_description:
            item.description = description
        item.updated_at = datetime.now(UTC)
        return item

    def delete(self, sample_id: int) -> bool:
        if sample_id in self._storage:
            del self._storage[sample_id]
            return True
        return False
