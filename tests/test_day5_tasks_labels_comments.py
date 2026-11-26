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


async def _create_admin_headers(db_session: AsyncSession) -> dict[str, str]:
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
    token = security.create_access_token(subject=admin_user.id)
    return {"Authorization": f"Bearer {token}"}


async def _setup_workspace_env(client: AsyncClient) -> dict[str, object]:
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

    return {
        "ws_id": ws_id,
        "p1_id": p1_id,
        "owner": (owner_id, owner_h),
        "editor1": (editor1_id, editor1_h),
        "editor2": (editor2_id, editor2_h),
        "viewer": (viewer_id, viewer_h),
        "outsider": (outsider_id, outsider_h),
    }


@pytest.mark.asyncio
async def test_auth_401_www_authenticate_header_and_unicode_sub(
    client: AsyncClient,
) -> None:
    res = await client.get("/api/v1/users/me")
    assert res.status_code == 401
    assert res.headers.get("www-authenticate") == "Bearer"

    # Unicode superscript digit '²' must return 401, not 500
    bad_token = security.create_access_token(subject="²")
    res_bad = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert res_bad.status_code == 401
    assert res_bad.headers.get("www-authenticate") == "Bearer"


@pytest.mark.asyncio
async def test_task_viewer_cannot_write_and_outsider_gets_404(
    client: AsyncClient,
) -> None:
    ctx = await _setup_workspace_env(client)
    p1_id = ctx["p1_id"]
    _, editor1_h = ctx["editor1"]
    _, viewer_h = ctx["viewer"]
    _, outsider_h = ctx["outsider"]

    assert (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Viewer Task"},
            headers=viewer_h,
        )
    ).status_code == 403

    task_id = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Editor Task"},
            headers=editor1_h,
        )
    ).json()["id"]

    assert (
        await client.get(f"/api/v1/projects/{p1_id}/tasks", headers=outsider_h)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/tasks/{task_id}", headers=outsider_h)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/tasks/{task_id}", headers=viewer_h)
    ).status_code == 200
    assert (
        await client.patch(
            f"/api/v1/tasks/{task_id}",
            json={"status": "DONE"},
            headers=viewer_h,
        )
    ).status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("null_field", ["title", "status", "priority"])
async def test_task_patch_null_required_fields_returns_422(
    client: AsyncClient,
    null_field: str,
) -> None:
    ctx = await _setup_workspace_env(client)
    p1_id = ctx["p1_id"]
    _, editor1_h = ctx["editor1"]

    task_id = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Valid Task"},
            headers=editor1_h,
        )
    ).json()["id"]

    res = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={null_field: None},
        headers=editor1_h,
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_task_validation_assignee_and_past_due_date(
    client: AsyncClient,
) -> None:
    ctx = await _setup_workspace_env(client)
    p1_id = ctx["p1_id"]
    _, editor1_h = ctx["editor1"]
    outsider_id, _ = ctx["outsider"]

    assert (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Bad Assignee", "assignee_id": outsider_id},
            headers=editor1_h,
        )
    ).status_code == 422

    past = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    assert (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Past Due", "due_date": past},
            headers=editor1_h,
        )
    ).status_code == 422


@pytest.mark.asyncio
async def test_task_filtering_with_status_priority_and_pagination_order(
    client: AsyncClient,
) -> None:
    ctx = await _setup_workspace_env(client)
    p1_id = ctx["p1_id"]
    _, owner_h = ctx["owner"]
    editor1_id, editor1_h = ctx["editor1"]
    _, viewer_h = ctx["viewer"]

    t1 = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "T1", "priority": "HIGH", "assignee_id": editor1_id},
            headers=editor1_h,
        )
    ).json()
    t2 = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "T2", "priority": "URGENT"},
            headers=owner_h,
        )
    ).json()
    t3 = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "T3", "priority": "LOW"},
            headers=owner_h,
        )
    ).json()

    await client.patch(
        f"/api/v1/tasks/{t1['id']}", json={"status": "DONE"}, headers=editor1_h
    )
    await client.patch(
        f"/api/v1/tasks/{t2['id']}",
        json={"status": "IN_PROGRESS"},
        headers=owner_h,
    )

    # Query params use standard ?status= and ?priority=
    res_done = await client.get(
        f"/api/v1/projects/{p1_id}/tasks?status=DONE",
        headers=viewer_h,
    )
    assert res_done.status_code == 200
    assert res_done.json()["total"] == 1
    assert res_done.json()["items"][0]["id"] == t1["id"]

    res_multi = await client.get(
        f"/api/v1/projects/{p1_id}/tasks"
        "?status=DONE&status=IN_PROGRESS&priority=HIGH&priority=URGENT",
        headers=viewer_h,
    )
    assert res_multi.status_code == 200
    assert res_multi.json()["total"] == 2

    # Pagination order: newest (created_at DESC, id DESC) first; limit > max -> 422
    res_page = await client.get(
        f"/api/v1/projects/{p1_id}/tasks?skip=0&limit=2",
        headers=viewer_h,
    )
    assert res_page.status_code == 200
    assert [item["id"] for item in res_page.json()["items"]] == [
        t3["id"],
        t2["id"],
    ]

    assert (
        await client.get(
            f"/api/v1/projects/{p1_id}/tasks?limit=101",
            headers=viewer_h,
        )
    ).status_code == 422


@pytest.mark.asyncio
async def test_remove_member_unassigns_their_workspace_tasks(
    client: AsyncClient,
) -> None:
    ctx = await _setup_workspace_env(client)
    ws_id = ctx["ws_id"]
    p1_id = ctx["p1_id"]
    _, owner_h = ctx["owner"]
    editor1_id, editor1_h = ctx["editor1"]

    task_id = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Assigned Task", "assignee_id": editor1_id},
            headers=editor1_h,
        )
    ).json()["id"]

    del_res = await client.delete(
        f"/api/v1/workspaces/{ws_id}/members/{editor1_id}",
        headers=owner_h,
    )
    assert del_res.status_code == 204

    task_after = await client.get(f"/api/v1/tasks/{task_id}", headers=owner_h)
    assert task_after.status_code == 200
    assert task_after.json()["assignee_id"] is None


@pytest.mark.asyncio
async def test_label_cross_workspace_returns_404_and_duplicate_returns_409(
    client: AsyncClient,
) -> None:
    ctx = await _setup_workspace_env(client)
    p1_id = ctx["p1_id"]
    _, editor1_h = ctx["editor1"]
    _, outsider_h = ctx["outsider"]

    # Outsider creates their own workspace, project, and label
    other_ws = (
        await client.post(
            "/api/v1/workspaces",
            json={"name": "Other WS"},
            headers=outsider_h,
        )
    ).json()["id"]
    other_proj = (
        await client.post(
            f"/api/v1/workspaces/{other_ws}/projects",
            json={"name": "Other Proj"},
            headers=outsider_h,
        )
    ).json()["id"]
    other_label = (
        await client.post(
            f"/api/v1/projects/{other_proj}/labels",
            json={"name": "secret-label"},
            headers=outsider_h,
        )
    ).json()["id"]

    task_id = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Label Task"},
            headers=editor1_h,
        )
    ).json()["id"]
    l1_id = (
        await client.post(
            f"/api/v1/projects/{p1_id}/labels",
            json={"name": "bug"},
            headers=editor1_h,
        )
    ).json()["id"]

    # Label from another workspace returns 404 (no existence leak)
    assert (
        await client.post(
            f"/api/v1/tasks/{task_id}/labels/{other_label}",
            headers=editor1_h,
        )
    ).status_code == 404

    # Outsider calling label endpoints returns 404
    assert (
        await client.get(f"/api/v1/projects/{p1_id}/labels", headers=outsider_h)
    ).status_code == 404
    assert (
        await client.patch(
            f"/api/v1/labels/{l1_id}", json={"name": "hack"}, headers=outsider_h
        )
    ).status_code == 404

    # Assign once -> 200; assign twice -> 409; remove unassigned -> 404
    assert (
        await client.post(f"/api/v1/tasks/{task_id}/labels/{l1_id}", headers=editor1_h)
    ).status_code == 200
    assert (
        await client.post(f"/api/v1/tasks/{task_id}/labels/{l1_id}", headers=editor1_h)
    ).status_code == 409
    assert (
        await client.delete(
            f"/api/v1/tasks/{task_id}/labels/{other_label}", headers=editor1_h
        )
    ).status_code == 404


@pytest.mark.asyncio
async def test_project_archive_unarchive_state_transitions_and_guards(
    client: AsyncClient,
) -> None:
    ctx = await _setup_workspace_env(client)
    p1_id = ctx["p1_id"]
    _, owner_h = ctx["owner"]
    _, editor1_h = ctx["editor1"]
    _, viewer_h = ctx["viewer"]

    # Unarchiving an already ACTIVE project returns 409
    assert (
        await client.post(f"/api/v1/projects/{p1_id}/unarchive", headers=owner_h)
    ).status_code == 409

    # Archive succeeds, archiving again returns 409
    assert (
        await client.post(f"/api/v1/projects/{p1_id}/archive", headers=owner_h)
    ).status_code == 200
    assert (
        await client.post(f"/api/v1/projects/{p1_id}/archive", headers=owner_h)
    ).status_code == 409

    # Permission check (403) runs before archive check (409)
    assert (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Viewer Write"},
            headers=viewer_h,
        )
    ).status_code == 403
    assert (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Editor Write"},
            headers=editor1_h,
        )
    ).status_code == 409

    # Unarchive succeeds -> writes work again
    assert (
        await client.post(f"/api/v1/projects/{p1_id}/unarchive", headers=owner_h)
    ).status_code == 200
    assert (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "After Unarchive"},
            headers=editor1_h,
        )
    ).status_code == 201


@pytest.mark.asyncio
async def test_comment_rbac_demoted_viewer_and_outsider(
    client: AsyncClient,
) -> None:
    ctx = await _setup_workspace_env(client)
    ws_id = ctx["ws_id"]
    p1_id = ctx["p1_id"]
    _, owner_h = ctx["owner"]
    editor1_id, editor1_h = ctx["editor1"]
    _, editor2_h = ctx["editor2"]
    _, outsider_h = ctx["outsider"]

    task_id = (
        await client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Comment Task"},
            headers=editor1_h,
        )
    ).json()["id"]

    c1_id = (
        await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "Original comment"},
            headers=editor1_h,
        )
    ).json()["id"]

    # Outsider gets 404 on comment endpoints
    assert (
        await client.get(f"/api/v1/tasks/{task_id}/comments", headers=outsider_h)
    ).status_code == 404
    assert (
        await client.patch(
            f"/api/v1/comments/{c1_id}",
            json={"content": "Hack"},
            headers=outsider_h,
        )
    ).status_code == 404

    # Another EDITOR cannot edit/delete c1 -> 403
    assert (
        await client.delete(f"/api/v1/comments/{c1_id}", headers=editor2_h)
    ).status_code == 403

    # Demote editor1 to VIEWER -> can no longer edit/delete own comment (403)
    demote = await client.patch(
        f"/api/v1/workspaces/{ws_id}/members/{editor1_id}",
        json={"role": "VIEWER"},
        headers=owner_h,
    )
    assert demote.status_code == 200
    assert (
        await client.patch(
            f"/api/v1/comments/{c1_id}",
            json={"content": "Viewer Edit"},
            headers=editor1_h,
        )
    ).status_code == 403
    assert (
        await client.delete(f"/api/v1/comments/{c1_id}", headers=editor1_h)
    ).status_code == 403

    # OWNER can still delete c1 -> 204
    assert (
        await client.delete(f"/api/v1/comments/{c1_id}", headers=owner_h)
    ).status_code == 204


@pytest.mark.asyncio
async def test_admin_can_write_task_and_delete_cascades(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    ctx = await _setup_workspace_env(client)
    p1_id = ctx["p1_id"]
    admin_h = await _create_admin_headers(db_session)

    # System ADMIN can create, label, comment, and delete task in any workspace
    task_res = await client.post(
        f"/api/v1/projects/{p1_id}/tasks",
        json={"title": "Admin Task"},
        headers=admin_h,
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    label_id = (
        await client.post(
            f"/api/v1/projects/{p1_id}/labels",
            json={"name": "admin-label"},
            headers=admin_h,
        )
    ).json()["id"]
    await client.post(f"/api/v1/tasks/{task_id}/labels/{label_id}", headers=admin_h)
    await client.post(
        f"/api/v1/tasks/{task_id}/comments",
        json={"content": "Admin comment"},
        headers=admin_h,
    )

    assert (
        await client.delete(f"/api/v1/tasks/{task_id}", headers=admin_h)
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
