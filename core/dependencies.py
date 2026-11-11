from app.repositories.sample_repository import SampleRepository
from app.services.sample_service import SampleService

# Singleton repository provider for in-memory persistence across requests in Day 1
_sample_repo_singleton = SampleRepository()


def get_sample_repository() -> SampleRepository:
    return _sample_repo_singleton


def get_sample_service() -> SampleService:
    return SampleService(repository=get_sample_repository())
