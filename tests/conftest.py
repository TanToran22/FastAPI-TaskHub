from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def clean_database() -> AsyncGenerator[None, None]:
    """Clean up tasks table before and after each test case."""
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("TRUNCATE TABLE tasks RESTART IDENTITY CASCADE;"))
            await session.commit()
        except Exception:
            await session.rollback()
    yield
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("TRUNCATE TABLE tasks RESTART IDENTITY CASCADE;"))
            await session.commit()
        except Exception:
            await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
