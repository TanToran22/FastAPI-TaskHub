from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.models.enums import UserRole
from app.models.models import Comment, User, task_labels


async def _register_and_login(
    client: AsyncClient, email: str, full_name: str
) -> tuple[int, dict[str, str]]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": full_name,
            "password": "password123",
        },
    )
    assert reg.status_code == 201
    user_id = reg.json()["id"]

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    return user_id, headers


async def _setup_workspace_and_project(
    client: AsyncClient,
) -> dict[str, object]:
    owner_id, owner_h = await _register_and_login(
        client, "d5_owner@example.com", "Owner"
    )
    editor1_id, editor1_h = await _register_and_login(
        client, "d5_editor1@example.com", "Editor 1"
    )
    editor2_id, editor2_h = await _register_and_login(
        client, "d5_editor2@example.com", "Editor 2"
    )
    viewer_id, viewer_h = await _register_and_login(
        client, "d5_viewer@example.com", "Viewer"
    )
    outsider_id, outsider_h = await _register_and_login(
        client, "d5_outsider@example.com", "Outsider"
    )

    ws_id = (
        await client.post(
            "/api/v1/workspaces",
            json={"name": "Day 5 WS"},
            headers=owner_h,
        )
    ).json()["id"]

    for email, role in [
        ("d5_editor1@example.com", "EDITOR"),
        ("d5_editor2@example.com", "EDITOR"),
        ("d5_viewer@example.com", "VIEWER"),
    ]:
        res = await client.post(
            f"/api/v1/workspaces/{ws_id}/members",
            json={"email": email, "role": role},
            headers=owner_h,
        )
        assert res.status_code == 201

    p1_id = (
        await client.post(
            f"/api/v1/workspaces/{ws_id}/projects",
            json={"name": "Project 1"},
            headers=owner_h,
        )
    ).json()["id"]
    p2_id = (
        await client.post(
            f"/api/v1/workspaces/{ws_id}/projects",
            json={"name": "Project 2"},
            headers=owner_h,
        )
    ).json()["id"]

    return {
        "ws_id": ws_id,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "owner": (owner_id, owner_h),
        "editor1": (editor1_id, editor1_h),
        "editor2": (editor2_id, editor2_h),
        "viewer": (viewer_id, viewer_h),
        "outsider": (outsider_id, outsider_h),
    }


@pytest.mark.asyncio
async def test_tasks_rbac_assignee_validation_and_filtering(
    client: AsyncClient,
) -> None:
    ctx = await _setup_workspace_and_project(client)
    p1_id = ctx["p1_id"]
    _, owner_h = ctx["owner"]
    editor1_id, editor1_h = ctx["editor1"]
    editor2_id, _ = ctx["editor2"]
    _, viewer_h = ctx["viewer"]
    outsider_id, outsider_h = ctx["outsider"]

    # VIEWER cannot create task -> 403
    assert (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Viewer Task"},
            headers=viewer_h,
        )
    ).status_code == 403

    # Outsider gets consistent 404 on list and create
    assert (
        await client.get(f"/api/v1/projects/{p1_id}/tasks", headers=outsider_h)
    ).status_code == 404

    # Assignee outside workspace -> 422
    bad_assignee = await client.post(
        f"/api/v1/projects/{p1_id}/tasks",
        json={"title": "Bad Assignee", "assignee_id": outsider_id},
        headers=editor1_h,
    )
    assert bad_assignee.status_code == 422

    # Past due_date -> 422
    past = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    assert (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Past Due", "due_date": past},
            headers=editor1_h,
        )
    ).status_code == 422

    # Create 3 tasks with different priorities/assignees; status defaults to TODO
    t1 = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={
                "title": "Task 1",
                "priority": "HIGH",
                "assignee_id": editor1_id,
            },
            headers=editor1_h,
        )
    ).json()
    assert t1["status"] == "TODO"
    assert t1["created_by"] == editor1_id

    t2 = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={
                "title": "Task 2",
                "priority": "URGENT",
                "assignee_id": editor2_id,
            },
            headers=owner_h,
        )
    ).json()

    t3 = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Task 3", "priority": "LOW"},
            headers=owner_h,
        )
    ).json()

    # Outsider gets 404 on /tasks/{id}
    assert (
        await client.get(f"/api/v1/tasks/{t1['id']}", headers=outsider_h)
    ).status_code == 404

    # VIEWER can read /tasks/{id} but cannot PATCH/DELETE (403)
    assert (
        await client.get(f"/api/v1/tasks/{t1['id']}", headers=viewer_h)
    ).status_code == 200
    assert (
        await client.patch(
            f"/api/v1/tasks/{t1['id']}",
            json={"status": "DONE"},
            headers=viewer_h,
        )
    ).status_code == 403

    # Update t1 status to IN_PROGRESS and t2 to DONE
    assert (
        await client.patch(
            f"/api/v1/tasks/{t1['id']}",
            json={"status": "IN_PROGRESS"},
            headers=editor1_h,
        )
    ).status_code == 200
    assert (
        await client.patch(
            f"/api/v1/tasks/{t2['id']}",
            json={"status": "DONE"},
            headers=owner_h,
        )
    ).status_code == 200

    # Multi-value filter: status in [IN_PROGRESS, DONE] + priority HIGH/URGENT
    filtered = await client.get(
        f"/api/v1/projects/{p1_id}/tasks"
        "?status_filter=IN_PROGRESS&status_filter=DONE"
        "&priority_filter=HIGH&priority_filter=URGENT",
        headers=viewer_h,
    )
    assert filtered.status_code == 200
    data = filtered.json()
    assert data["total"] == 2
    assert {item["id"] for item in data["items"]} == {t1["id"], t2["id"]}

    # Filter by assignee_id
    by_assignee = await client.get(
        f"/api/v1/projects/{p1_id}/tasks?assignee_id={editor1_id}",
        headers=viewer_h,
    )
    assert by_assignee.status_code == 200
    assert by_assignee.json()["total"] == 1
    assert by_assignee.json()["items"][0]["id"] == t1["id"]
    assert t3["id"] != t1["id"]


@pytest.mark.asyncio
async def test_labels_assignment_archived_project_and_unarchive(
    client: AsyncClient,
) -> None:
    ctx = await _setup_workspace_and_project(client)
    p1_id = ctx["p1_id"]
    p2_id = ctx["p2_id"]
    _, owner_h = ctx["owner"]
    _, editor1_h = ctx["editor1"]
    _, viewer_h = ctx["viewer"]

    task_id = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Labeled Task"},
            headers=editor1_h,
        )
    ).json()["id"]

    # Create label in p1 and p2
    l1 = (
        await client.post(
            f"/api/v1/projects/{p1_id}/labels",
            json={"name": "bug", "color": "#EF4444"},
            headers=editor1_h,
        )
    ).json()
    l2 = (
        await client.post(
            f"/api/v1/projects/{p2_id}/labels",
            json={"name": "other-proj-label"},
            headers=owner_h,
        )
    ).json()

    # Duplicate label name in same project -> 409
    assert (
        await client.post(
            f"/api/v1/projects/{p1_id}/labels",
            json={"name": "bug"},
            headers=editor1_h,
        )
    ).status_code == 409

    # Assign label from different project -> 422
    assert (
        await client.post(
            f"/api/v1/tasks/{task_id}/labels/{l2['id']}",
            headers=editor1_h,
        )
    ).status_code == 422

    # Assign label l1 -> 200 with labels loaded
    assigned = await client.post(
        f"/api/v1/tasks/{task_id}/labels/{l1['id']}",
        headers=editor1_h,
    )
    assert assigned.status_code == 200
    assert len(assigned.json()["labels"]) == 1
    assert assigned.json()["labels"][0]["id"] == l1["id"]

    # Duplicate label assignment -> 409
    assert (
        await client.post(
            f"/api/v1/tasks/{task_id}/labels/{l1['id']}",
            headers=editor1_h,
        )
    ).status_code == 409

    # Remove unassigned label -> 404
    assert (
        await client.delete(
            f"/api/v1/tasks/{task_id}/labels/{l2['id']}",
            headers=editor1_h,
        )
    ).status_code == 404

    # Archive project 1
    assert (
        await client.post(f"/api/v1/projects/{p1_id}/archive", headers=owner_h)
    ).status_code == 200

    # Permission check runs BEFORE archive check: VIEWER still gets 403
    assert (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Viewer on Archived"},
            headers=viewer_h,
        )
    ).status_code == 403

    # EDITOR gets 409 Conflict on archived project writes
    assert (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Blocked by Archive"},
            headers=editor1_h,
        )
    ).status_code == 409
    assert (
        await client.patch(
            f"/api/v1/tasks/{task_id}",
            json={"title": "Blocked"},
            headers=editor1_h,
        )
    ).status_code == 409

    # Unarchive project 1 -> writes work again
    unarch = await client.post(f"/api/v1/projects/{p1_id}/unarchive", headers=owner_h)
    assert unarch.status_code == 200
    assert unarch.json()["status"] == "ACTIVE"

    assert (
        await client.patch(
            f"/api/v1/tasks/{task_id}",
            json={"title": "Unarchived Update"},
            headers=editor1_h,
        )
    ).status_code == 200


@pytest.mark.asyncio
async def test_comments_rbac_admin_bypass_and_task_cascade_delete(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    ctx = await _setup_workspace_and_project(client)
    p1_id = ctx["p1_id"]
    _, owner_h = ctx["owner"]
    editor1_id, editor1_h = ctx["editor1"]
    _, editor2_h = ctx["editor2"]
    _, viewer_h = ctx["viewer"]

    task_id = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Discussion Task"},
            headers=editor1_h,
        )
    ).json()["id"]

    label_id = (
        await client.post(
            f"/api/v1/projects/{p1_id}/labels",
            json={"name": "discussion"},
            headers=editor1_h,
        )
    ).json()["id"]
    await client.post(f"/api/v1/tasks/{task_id}/labels/{label_id}", headers=editor1_h)

    # VIEWER cannot post comment -> 403
    assert (
        await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "Viewer comment"},
            headers=viewer_h,
        )
    ).status_code == 403

    # EDITOR 1 posts comment
    c1 = (
        await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "First comment"},
            headers=editor1_h,
        )
    ).json()
    assert c1["author_id"] == editor1_id

    # EDITOR 2 cannot edit or delete EDITOR 1's comment -> 403
    assert (
        await client.patch(
            f"/api/v1/comments/{c1['id']}",
            json={"content": "Tampered"},
            headers=editor2_h,
        )
    ).status_code == 403
    assert (
        await client.delete(
            f"/api/v1/comments/{c1['id']}",
            headers=editor2_h,
        )
    ).status_code == 403

    # EDITOR 1 can edit own comment -> 200
    assert (
        await client.patch(
            f"/api/v1/comments/{c1['id']}",
            json={"content": "Edited comment"},
            headers=editor1_h,
        )
    ).status_code == 200

    # Create second comment and let OWNER delete c1 -> 204
    c2 = (
        await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "Second comment"},
            headers=editor2_h,
        )
    ).json()
    assert (
        await client.delete(f"/api/v1/comments/{c1['id']}", headers=owner_h)
    ).status_code == 204

    # System ADMIN bypasses workspace membership check
    admin_user = User(
        email="sysadmin@example.com",
        full_name="System Admin",
        hashed_password=security.get_password_hash("adminpass123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    admin_token = security.create_access_token(subject=admin_user.id)
    admin_h = {"Authorization": f"Bearer {admin_token}"}

    assert (
        await client.get(f"/api/v1/tasks/{task_id}", headers=admin_h)
    ).status_code == 200

    # Deleting task cascades comments and task_labels cleanly (204)
    assert (
        await client.delete(f"/api/v1/tasks/{task_id}", headers=editor1_h)
    ).status_code == 204

    db_session.expire_all()
    rem_comments = (
        await db_session.execute(
            select(func.count(Comment.id)).where(Comment.task_id == task_id)
        )
    ).scalar_one()
    rem_links = (
        await db_session.execute(
            select(func.count())
            .select_from(task_labels)
            .where(task_labels.c.task_id == task_id)
        )
    ).scalar_one()
    assert rem_comments == 0
    assert rem_links == 0
    assert c2["id"] > 0
