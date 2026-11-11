from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class InternalSample:
    id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_new(
        cls, sample_id: int, title: str, description: str | None
    ) -> "InternalSample":
        now = datetime.now(UTC)
        return cls(
            id=sample_id,
            title=title,
            description=description,
            created_at=now,
            updated_at=now,
        )
