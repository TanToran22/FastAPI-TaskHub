import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.dependencies import require_admin_role
from app.core.exceptions import ForbiddenException
from app.models.enums import UserRole
from app.models.models import User


@pytest.mark.asyncio
async def test_register_and_duplicate_email_returns_409(
    client: AsyncClient,
) -> None:
    payload = {
        "email": "Alice@Example.com",
        "full_name": "  Alice Smith  ",
        "password": "securepassword123",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201
    data = res1.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Smith"
    assert data["role"] == "MEMBER"
    assert data["is_active"] is True
    assert "hashed_password" not in data

    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409


@pytest.mark.asyncio
async def test_password_whitespace_preserved_and_72_byte_limit(
    client: AsyncClient,
) -> None:
    pw_with_spaces = "  secret123  "
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "space@example.com",
            "full_name": "Space User",
            "password": pw_with_spaces,
        },
    )
    assert res.status_code == 201

    fail_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "space@example.com", "password": "secret123"},
    )
    assert fail_login.status_code == 401

    ok_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "space@example.com", "password": pw_with_spaces},
    )
    assert ok_login.status_code == 200

    over_72_bytes_pw = "a" * 73
    res_72 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "longpw@example.com",
            "full_name": "Long PW",
            "password": over_72_bytes_pw,
        },
    )
    assert res_72.status_code == 422


@pytest.mark.asyncio
async def test_login_jwt_claims_and_refresh_token_flow(
    client: AsyncClient,
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@example.com",
            "full_name": "Bob Jones",
            "password": "bobpassword123",
        },
    )

    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "wrongpassword"},
    )
    assert bad_login.status_code == 401

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "bobpassword123"},
    )
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert tokens["token_type"] == "bearer"

    access_payload = security.decode_token(tokens["access_token"])
    assert access_payload["type"] == "access"
    assert "jti" in access_payload
    assert "iat" in access_payload

    bad_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["access_token"]},
    )
    assert bad_refresh.status_code == 401

    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()


@pytest.mark.asyncio
async def test_user_me_profile_password_change_and_protected_tasks(
    client: AsyncClient,
) -> None:
    unauth_res = await client.get("/api/v1/users/me")
    assert unauth_res.status_code == 401

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "charlie@example.com",
            "full_name": "Charlie Brown",
            "password": "oldpassword123",
        },
    )

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "charlie@example.com", "password": "oldpassword123"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    me_res = await client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["full_name"] == "Charlie Brown"

    null_patch = await client.patch(
        "/api/v1/users/me",
        json={"full_name": None},
        headers=headers,
    )
    assert null_patch.status_code == 422

    valid_patch = await client.patch(
        "/api/v1/users/me",
        json={"full_name": "  Charlie Updated  "},
        headers=headers,
    )
    assert valid_patch.status_code == 200
    assert valid_patch.json()["full_name"] == "Charlie Updated"

    pw_res = await client.post(
        "/api/v1/users/me/change-password",
        json={
            "current_password": "oldpassword123",
            "new_password": "newpassword456",
        },
        headers=headers,
    )
    assert pw_res.status_code == 204

    relogin = await client.post(
        "/api/v1/auth/login",
        json={"email": "charlie@example.com", "password": "newpassword456"},
    )
    assert relogin.status_code == 200


@pytest.mark.asyncio
async def test_require_admin_role_dependency(db_session: AsyncSession) -> None:
    member_user = User(
        email="member@example.com",
        full_name="Member User",
        hashed_password="hashed",
        role=UserRole.MEMBER,
        is_active=True,
    )
    with pytest.raises(ForbiddenException):
        await require_admin_role(current_user=member_user)

    admin_user = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="hashed",
        role=UserRole.ADMIN,
        is_active=True,
    )
    verified = await require_admin_role(current_user=admin_user)
    assert verified.role == UserRole.ADMIN
