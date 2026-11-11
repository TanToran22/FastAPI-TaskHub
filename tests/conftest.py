from collections.abc import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_sample_repository, get_task_repository
from app.main import app


@pytest.fixture(autouse=True)
def reset_repositories() -> None:
    """Reset in-memory storage before each test case."""
    try:
        task_repo = get_task_repository()
        task_repo._storage.clear()
        task_repo._id_counter = 1
    except Exception:
        pass

    try:
        sample_repo = get_sample_repository()
        sample_repo._storage.clear()
        sample_repo._id_counter = 1
    except Exception:
        pass


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac