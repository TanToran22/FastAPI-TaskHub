from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class InternalTask:
    id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_new(
        cls,
        task_id: int,
        title: str,
        description: str | None,
    ) -> "InternalTask":
        now = datetime.now(UTC)
        return cls(
            id=task_id,
            title=title,
            description=description,
            created_at=now,
            updated_at=now,
        )
