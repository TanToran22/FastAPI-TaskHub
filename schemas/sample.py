from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SampleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class SampleCreate(SampleBase):
    pass


class SampleResponse(SampleBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
