import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.models.enums import UserRole
from app.models.models import User
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_register_and_duplicate_email_409(client: AsyncClient) -> None:
    payload = {
        "email": "alice@example.com",
        "full_name": "Alice Nguyen",
        "password": "StrongPassword123",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201
    data = res1.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Nguyen"
    assert data["role"] == "MEMBER"
    assert data["is_active"] is True
    assert "hashed_password" not in data

    # Duplicate email (case-insensitive) -> 409 Conflict
    res2 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ALICE@example.com",
            "full_name": "Alice Clone",
            "password": "StrongPassword123",
        },
    )
    assert res2.status_code == 409


@pytest.mark.asyncio
async def test_login_and_refresh_token_flow(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@example.com",
            "full_name": "Bob Tran",
            "password": "SecretPassword123",
        },
    )

    # Wrong password -> 401
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "WrongPassword"},
    )
    assert bad_login.status_code == 401

    # Valid login -> 200 with access & refresh tokens
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "SecretPassword123"},
    )
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # Using access token as refresh token -> 401
    bad_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["access_token"]},
    )
    assert bad_refresh.status_code == 401

    # Valid refresh -> 200 new token pair
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens


@pytest.mark.asyncio
async def test_user_profile_me_patch_and_change_password(
    client: AsyncClient,
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "charlie@example.com",
            "full_name": "Charlie Le",
            "password": "OldPassword123",
        },
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "charlie@example.com", "password": "OldPassword123"},
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Unauthenticated -> 401
    unauth = await client.get("/api/v1/users/me")
    assert unauth.status_code == 401

    # GET /users/me -> 200
    me_res = await client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "charlie@example.com"

    # PATCH /users/me with null -> 422
    null_patch = await client.patch(
        "/api/v1/users/me",
        json={"full_name": None},
        headers=headers,
    )
    assert null_patch.status_code == 422

    # PATCH /users/me valid -> 200
    ok_patch = await client.patch(
        "/api/v1/users/me",
        json={"full_name": "Charlie Updated"},
        headers=headers,
    )
    assert ok_patch.status_code == 200
    assert ok_patch.json()["full_name"] == "Charlie Updated"

    # Change password with wrong current password -> 400
    bad_pw = await client.post(
        "/api/v1/users/me/change-password",
        json={
            "current_password": "WrongOldPassword",
            "new_password": "NewPassword456",
        },
        headers=headers,
    )
    assert bad_pw.status_code == 400

    # Change password valid -> 204
    ok_pw = await client.post(
        "/api/v1/users/me/change-password",
        json={
            "current_password": "OldPassword123",
            "new_password": "NewPassword456",
        },
        headers=headers,
    )
    assert ok_pw.status_code == 204

    # Login with new password -> 200
    relogin = await client.post(
        "/api/v1/auth/login",
        json={"email": "charlie@example.com", "password": "NewPassword456"},
    )
    assert relogin.status_code == 200


@pytest.mark.asyncio
async def test_rbac_admin_and_inactive_user(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "member@example.com",
            "full_name": "Regular Member",
            "password": "Password123",
        },
    )
    user_id = reg.json()["id"]

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "member@example.com", "password": "Password123"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Member accessing admin endpoint -> 403 Forbidden
    forbidden_res = await client.get("/api/v1/users/admin/check", headers=headers)
    assert forbidden_res.status_code == 403

    # Promote user to ADMIN in DB -> 200 OK
    async with TestingSessionLocal() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(role=UserRole.ADMIN)
        )
        await session.commit()

    admin_res = await client.get("/api/v1/users/admin/check", headers=headers)
    assert admin_res.status_code == 200
    assert admin_res.json()["role"] == "ADMIN"

    # Deactivate user in DB -> 403 Forbidden
    async with TestingSessionLocal() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(is_active=False)
        )
        await session.commit()

    inactive_res = await client.get("/api/v1/users/me", headers=headers)
    assert inactive_res.status_code == 403
