import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient) -> None:
    payload = {"title": "Test Title", "description": "Test Description"}
    response = await client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Test Title"
    assert data["description"] == "Test Description"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient) -> None:
    await client.post("/api/v1/tasks", json={"title": "Task 1"})
    await client.post("/api/v1/tasks", json={"title": "Task 2"})

    response = await client.get("/api/v1/tasks?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2


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
        f"/api/v1/tasks/{task_id}", json={"title": "New Title"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_patch_task_null_title_returns_422(client: AsyncClient) -> None:
    created = await client.post("/api/v1/tasks", json={"title": "Valid Title"})
    task_id = created.json()["id"]

    response = await client.patch(f"/api/v1/tasks/{task_id}", json={"title": None})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient) -> None:
    created = await client.post("/api/v1/tasks", json={"title": "To Delete"})
    task_id = created.json()["id"]

    del_res = await client.delete(f"/api/v1/tasks/{task_id}")
    assert del_res.status_code == 204

    get_res = await client.get(f"/api/v1/tasks/{task_id}")
    assert get_res.status_code == 404
