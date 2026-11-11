from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, HTTPException, status
from app.schemas.sample import SampleCreate, SampleResponse

router = APIRouter()

_FAKE_DB: dict[int, dict[str, Any]] = {}
_ID_COUNTER = 1


@router.post("/", response_model=SampleResponse, status_code=status.HTTP_201_CREATED)
async def create_sample(payload: SampleCreate) -> Any:
    global _ID_COUNTER
    sample_id = _ID_COUNTER
    _ID_COUNTER += 1

    item = {
        "id": sample_id,
        "title": payload.title,
        "description": payload.description,
        "created_at": datetime.now(timezone.utc),
    }
    _FAKE_DB[sample_id] = item
    return item


@router.get("/{sample_id}", response_model=SampleResponse)
async def get_sample(sample_id: int) -> Any:
    if sample_id not in _FAKE_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample not found",
        )
    return _FAKE_DB[sample_id]
