from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "tasktester@example.com",
            "full_name": "Task Tester",
            "password": "taskpassword123",
        },
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "tasktester@example.com",
            "password": "taskpassword123",
        },
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_task_success(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    payload = {"title": "Test Title", "description": "Test Description"}
    response = await client.post("/api/v1/tasks", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Test Title"
    assert data["description"] == "Test Description"
    assert data["created_by"] is not None


@pytest.mark.asyncio
async def test_create_task_past_due_date_returns_422(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    past_date = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Past Task", "due_date": past_date},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_invalid_fk_returns_409(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Bad FK Task", "project_id": 99999},
        headers=auth_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_tasks_pagination_and_ordering(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post("/api/v1/tasks", json={"title": "Task 1"}, headers=auth_headers)
    await client.post("/api/v1/tasks", json={"title": "Task 2"}, headers=auth_headers)

    response = await client.get("/api/v1/tasks?skip=0&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Task 2"
    assert data["items"][1]["title"] == "Task 1"


@pytest.mark.asyncio
async def test_get_task_not_found(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/tasks/999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found."


@pytest.mark.asyncio
async def test_patch_task_success(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/tasks", json={"title": "Old Title"}, headers=auth_headers
    )
    task_id = created.json()["id"]

    patch_res = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "New Title"},
        headers=auth_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_patch_task_null_fields_return_422(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/tasks", json={"title": "Valid Title"}, headers=auth_headers
    )
    task_id = created.json()["id"]

    res_title = await client.patch(
        f"/api/v1/tasks/{task_id}", json={"title": None}, headers=auth_headers
    )
    assert res_title.status_code == 422

    res_status = await client.patch(
        f"/api/v1/tasks/{task_id}", json={"status": None}, headers=auth_headers
    )
    assert res_status.status_code == 422


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/tasks", json={"title": "To Delete"}, headers=auth_headers
    )
    task_id = created.json()["id"]

    del_res = await client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert del_res.status_code == 204

    get_res = await client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert get_res.status_code == 404
