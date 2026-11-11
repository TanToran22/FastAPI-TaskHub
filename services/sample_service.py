from app.core import constants
from app.core.exceptions import NotFoundException
from app.models.internal_sample import InternalSample
from app.repositories.sample_repository import SampleRepository
from app.schemas.sample import SampleCreate, SampleUpdate


class SampleService:
    def __init__(self, repository: SampleRepository) -> None:
        # Dependency injection via self.repository instead of global repo
        self.repository = repository

    def get_sample_or_404(self, sample_id: int) -> InternalSample:
        sample = self.repository.get_by_id(sample_id)
        if not sample:
            raise NotFoundException(constants.MSG_SAMPLE_NOT_FOUND)
        return sample

    def list_samples(self, skip: int = 0, limit: int = 100) -> list[InternalSample]:
        return self.repository.get_all(skip=skip, limit=limit)

    def create_sample(self, payload: SampleCreate) -> InternalSample:
        return self.repository.create(
            title=payload.title,
            description=payload.description,
        )

    def patch_sample(self, sample_id: int, payload: SampleUpdate) -> InternalSample:
        # Check existence first
        self.get_sample_or_404(sample_id)

        update_data = payload.model_dump(exclude_unset=True)
        title = update_data.get("title")
        description = update_data.get("description")
        update_description = "description" in update_data

        updated = self.repository.update(
            sample_id=sample_id,
            title=title,
            description=description,
            update_description=update_description,
        )
        if not updated:
            raise NotFoundException(constants.MSG_SAMPLE_NOT_FOUND)
        return updated

    def delete_sample(self, sample_id: int) -> None:
        deleted = self.repository.delete(sample_id)
        if not deleted:
            raise NotFoundException(constants.MSG_SAMPLE_NOT_FOUND)
