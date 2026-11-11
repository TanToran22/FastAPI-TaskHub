from collections.abc import AsyncGenerator
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_task_repository
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def reset_repositories() -> None:
    try:
        task_repo = get_task_repository()
        task_repo._storage.clear()
        task_repo._id_counter = 1
    except Exception:
        pass


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac