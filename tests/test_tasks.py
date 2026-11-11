import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient) -> None:
    payload = {"title": "Test Title", "description": "Test Description"}
    response = await client.post("/api/v1/tasks/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Test Title"
    assert data["description"] == "Test Description"


@pytest.mark.asyncio
async def test_create_task_whitespace_title_stripped(client: AsyncClient) -> None:
    # str_strip_whitespace=True biến "   " thành "" -> vi phạm min_length=1
    payload = {"title": "   ", "description": "Whitespace test"}
    response = await client.post("/api/v1/tasks/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tasks/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found."


@pytest.mark.asyncio
async def test_patch_task_success(client: AsyncClient) -> None:
    # 1. Tạo task ban đầu
    created = await client.post(
        "/api/v1/tasks/",
        json={"title": "Old Title", "description": "Old Desc"},
    )
    task_id = created.json()["id"]

    # 2. Patch title
    patch_res = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "New Title"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "New Title"
    assert patch_res.json()["description"] == "Old Desc"


@pytest.mark.asyncio
async def test_patch_task_null_title_returns_422(client: AsyncClient) -> None:
    """Xác minh: Gửi explicit null cho field bắt buộc phải bị chặn 422 thay vì 500."""
    created = await client.post(
        "/api/v1/tasks/",
        json={"title": "Valid Title"},
    )
    task_id = created.json()["id"]

    # Gửi explicit title: null
    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": None},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/tasks/",
        json={"title": "To Delete"},
    )
    task_id = created.json()["id"]

    del_res = await client.delete(f"/api/v1/tasks/{task_id}")
    assert del_res.status_code == 204

    get_res = await client.get(f"/api/v1/tasks/{task_id}")
    assert get_res.status_code == 404