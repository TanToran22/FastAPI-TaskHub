import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import WorkspaceMember


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


@pytest.mark.asyncio
async def test_workspace_crud_and_owner_membership(
    client: AsyncClient,
) -> None:
    owner_id, owner_headers = await _register_and_login(
        client, "owner@example.com", "Owner User"
    )
    _, outsider_headers = await _register_and_login(
        client, "outsider@example.com", "Outsider User"
    )

    create_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "  Engineering Team  "},
        headers=owner_headers,
    )
    assert create_res.status_code == 201
    ws = create_res.json()
    assert ws["name"] == "Engineering Team"
    assert ws["owner_id"] == owner_id
    ws_id = ws["id"]

    members_res = await client.get(
        f"/api/v1/workspaces/{ws_id}/members", headers=owner_headers
    )
    assert members_res.status_code == 200
    members_data = members_res.json()
    assert members_data["total"] == 1
    assert members_data["items"][0]["user_id"] == owner_id
    assert members_data["items"][0]["role"] == "OWNER"

    outsider_list = await client.get("/api/v1/workspaces", headers=outsider_headers)
    assert outsider_list.status_code == 200
    assert outsider_list.json()["total"] == 0

    outsider_get = await client.get(
        f"/api/v1/workspaces/{ws_id}", headers=outsider_headers
    )
    assert outsider_get.status_code == 403

    null_patch = await client.patch(
        f"/api/v1/workspaces/{ws_id}",
        json={"name": None},
        headers=owner_headers,
    )
    assert null_patch.status_code == 422

    upd_res = await client.patch(
        f"/api/v1/workspaces/{ws_id}",
        json={"name": "Core Platform"},
        headers=owner_headers,
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["name"] == "Core Platform"

    assert (
        await client.delete(f"/api/v1/workspaces/{ws_id}", headers=outsider_headers)
    ).status_code == 403

    assert (
        await client.delete(f"/api/v1/workspaces/{ws_id}", headers=owner_headers)
    ).status_code == 204


@pytest.mark.asyncio
async def test_delete_workspace_cascades_projects_and_members(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, owner_headers = await _register_and_login(
        client, "cascade_owner@example.com", "Cascade Owner"
    )
    _, member_headers = await _register_and_login(
        client, "cascade_member@example.com", "Cascade Member"
    )

    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Cascade Workspace"},
        headers=owner_headers,
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    inv_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "cascade_member@example.com", "role": "EDITOR"},
        headers=owner_headers,
    )
    assert inv_res.status_code == 201

    proj_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Cascade Project"},
        headers=member_headers,
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # Confirm 2 members exist before deletion
    before_count = (
        await db_session.execute(
            select(func.count(WorkspaceMember.id)).where(
                WorkspaceMember.workspace_id == ws_id
            )
        )
    ).scalar_one()
    assert before_count == 2

    # Delete non-empty workspace
    del_res = await client.delete(f"/api/v1/workspaces/{ws_id}", headers=owner_headers)
    assert del_res.status_code == 204

    # Project must be cascade-deleted (404)
    assert (
        await client.get(f"/api/v1/projects/{proj_id}", headers=owner_headers)
    ).status_code == 404

    # Workspace members must be cascade-deleted (0 rows remaining)
    db_session.expire_all()
    after_count = (
        await db_session.execute(
            select(func.count(WorkspaceMember.id)).where(
                WorkspaceMember.workspace_id == ws_id
            )
        )
    ).scalar_one()
    assert after_count == 0


@pytest.mark.asyncio
async def test_workspace_member_invite_role_limits_and_rbac(
    client: AsyncClient,
) -> None:
    owner_id, owner_headers = await _register_and_login(
        client, "wsowner@example.com", "WS Owner"
    )
    editor_id, editor_headers = await _register_and_login(
        client, "wseditor@example.com", "WS Editor"
    )
    viewer_id, viewer_headers = await _register_and_login(
        client, "wsviewer@example.com", "WS Viewer"
    )

    ws_id = (
        await client.post(
            "/api/v1/workspaces",
            json={"name": "RBAC Workspace"},
            headers=owner_headers,
        )
    ).json()["id"]

    owner_invite = await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "wseditor@example.com", "role": "OWNER"},
        headers=owner_headers,
    )
    assert owner_invite.status_code == 422

    inv_editor = await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "wseditor@example.com", "role": "EDITOR"},
        headers=owner_headers,
    )
    assert inv_editor.status_code == 201
    assert inv_editor.json()["role"] == "EDITOR"

    dup_invite = await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "wseditor@example.com", "role": "VIEWER"},
        headers=owner_headers,
    )
    assert dup_invite.status_code == 409

    editor_invite = await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "wsviewer@example.com", "role": "VIEWER"},
        headers=editor_headers,
    )
    assert editor_invite.status_code == 403

    inv_viewer = await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "wsviewer@example.com", "role": "VIEWER"},
        headers=owner_headers,
    )
    assert inv_viewer.status_code == 201

    self_remove = await client.delete(
        f"/api/v1/workspaces/{ws_id}/members/{owner_id}",
        headers=owner_headers,
    )
    assert self_remove.status_code == 400

    role_upd = await client.patch(
        f"/api/v1/workspaces/{ws_id}/members/{viewer_id}",
        json={"role": "EDITOR"},
        headers=owner_headers,
    )
    assert role_upd.status_code == 200
    assert role_upd.json()["role"] == "EDITOR"

    rem_res = await client.delete(
        f"/api/v1/workspaces/{ws_id}/members/{editor_id}",
        headers=owner_headers,
    )
    assert rem_res.status_code == 204

    assert (
        await client.get(f"/api/v1/workspaces/{ws_id}", headers=editor_headers)
    ).status_code == 403


@pytest.mark.asyncio
async def test_project_crud_archive_filter_and_rbac(
    client: AsyncClient,
) -> None:
    _, owner_headers = await _register_and_login(
        client, "projowner@example.com", "Proj Owner"
    )
    _, editor_headers = await _register_and_login(
        client, "projeditor@example.com", "Proj Editor"
    )
    _, viewer_headers = await _register_and_login(
        client, "projviewer@example.com", "Proj Viewer"
    )

    ws_id = (
        await client.post(
            "/api/v1/workspaces",
            json={"name": "Product Workspace"},
            headers=owner_headers,
        )
    ).json()["id"]

    await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "projeditor@example.com", "role": "EDITOR"},
        headers=owner_headers,
    )
    await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "projviewer@example.com", "role": "VIEWER"},
        headers=owner_headers,
    )

    viewer_create = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Blocked Project"},
        headers=viewer_headers,
    )
    assert viewer_create.status_code == 403

    p1_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Backend API", "description": "Core API"},
        headers=editor_headers,
    )
    assert p1_res.status_code == 201
    p1 = p1_res.json()
    assert p1["workspace_id"] == ws_id
    assert p1["status"] == "ACTIVE"
    p1_id = p1["id"]

    p2_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Legacy Migration"},
        headers=owner_headers,
    )
    assert p2_res.status_code == 201
    p2_id = p2_res.json()["id"]

    assert (
        await client.get(f"/api/v1/projects/{p1_id}", headers=viewer_headers)
    ).status_code == 200

    assert (
        await client.patch(
            f"/api/v1/projects/{p1_id}",
            json={"name": "Hacked"},
            headers=viewer_headers,
        )
    ).status_code == 403
    assert (
        await client.post(f"/api/v1/projects/{p1_id}/archive", headers=viewer_headers)
    ).status_code == 403

    # PATCH null name returns 422
    assert (
        await client.patch(
            f"/api/v1/projects/{p1_id}",
            json={"name": None},
            headers=editor_headers,
        )
    ).status_code == 422

    # EDITOR archives project 2 via dedicated /archive endpoint
    arch_res = await client.post(
        f"/api/v1/projects/{p2_id}/archive", headers=editor_headers
    )
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == "ARCHIVED"

    # PATCH cannot modify status or reopen archived project
    reopen_attempt = await client.patch(
        f"/api/v1/projects/{p2_id}",
        json={"name": "Legacy Renamed", "status": "ACTIVE"},
        headers=editor_headers,
    )
    assert reopen_attempt.status_code == 200
    assert reopen_attempt.json()["name"] == "Legacy Renamed"
    assert reopen_attempt.json()["status"] == "ARCHIVED"

    active_list = await client.get(
        f"/api/v1/workspaces/{ws_id}/projects?status_filter=ACTIVE",
        headers=viewer_headers,
    )
    assert active_list.status_code == 200
    assert active_list.json()["total"] == 1
    assert active_list.json()["items"][0]["id"] == p1_id

    archived_list = await client.get(
        f"/api/v1/workspaces/{ws_id}/projects?status_filter=ARCHIVED",
        headers=viewer_headers,
    )
    assert archived_list.status_code == 200
    assert archived_list.json()["total"] == 1
    assert archived_list.json()["items"][0]["id"] == p2_id

    assert (
        await client.delete(f"/api/v1/projects/{p1_id}", headers=editor_headers)
    ).status_code == 403

    assert (
        await client.delete(f"/api/v1/projects/{p1_id}", headers=owner_headers)
    ).status_code == 204
    assert (
        await client.get(f"/api/v1/projects/{p1_id}", headers=owner_headers)
    ).status_code == 404
