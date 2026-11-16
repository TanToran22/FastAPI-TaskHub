from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient) -> None:
    future_due = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    payload = {
        "title": "Test Title",
        "description": "Test Description",
        "due_date": future_due,
    }
    response = await client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Test Title"
    assert data["description"] == "Test Description"
    assert data["status"] == "TODO"


@pytest.mark.asyncio
async def test_create_task_past_due_date_returns_422(client: AsyncClient) -> None:
    past_due = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    payload = {
        "title": "Past Due Task",
        "due_date": past_due,
    }
    response = await client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_invalid_fk_returns_409(client: AsyncClient) -> None:
    payload = {
        "title": "Invalid Project Task",
        "project_id": 99999,
    }
    response = await client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_tasks_pagination_and_ordering(client: AsyncClient) -> None:
    await client.post("/api/v1/tasks", json={"title": "Task 1"})
    await client.post("/api/v1/tasks", json={"title": "Task 2"})
    await client.post("/api/v1/tasks", json={"title": "Task 3"})

    response = await client.get("/api/v1/tasks?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["skip"] == 0
    assert data["limit"] == 2
    assert len(data["items"]) == 2
    # Ordered by created_at desc, id desc -> Task 3 first, Task 2 second
    assert data["items"][0]["title"] == "Task 3"
    assert data["items"][1]["title"] == "Task 2"


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tasks/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found."


@pytest.mark.asyncio
async def test_patch_task_success(client: AsyncClient) -> None:
    created = await client.post("/api/v1/tasks", json={"title": "Old Title"})
    task_id = created.json()["id"]

    patch_res = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "New Title", "status": "IN_PROGRESS"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "New Title"
    assert patch_res.json()["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_patch_task_null_fields_return_422(client: AsyncClient) -> None:
    created = await client.post("/api/v1/tasks", json={"title": "Valid Title"})
    task_id = created.json()["id"]

    res_title = await client.patch(f"/api/v1/tasks/{task_id}", json={"title": None})
    assert res_title.status_code == 422

    res_status = await client.patch(f"/api/v1/tasks/{task_id}", json={"status": None})
    assert res_status.status_code == 422

    res_priority = await client.patch(
        f"/api/v1/tasks/{task_id}", json={"priority": None}
    )
    assert res_priority.status_code == 422


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient) -> None:
    created = await client.post("/api/v1/tasks", json={"title": "To Delete"})
    task_id = created.json()["id"]

    del_res = await client.delete(f"/api/v1/tasks/{task_id}")
    assert del_res.status_code == 204

    get_res = await client.get(f"/api/v1/tasks/{task_id}")
    assert get_res.status_code == 404
