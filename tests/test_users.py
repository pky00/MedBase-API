import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.utils.security import verify_password


@pytest.mark.asyncio
class TestUsersMe:
    """Test /users/me endpoints."""

    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict, test_user: dict):
        """Test getting current user profile."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user["username"]
        assert data["email"] == test_user["email"]

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without auth returns 401."""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401

    async def test_update_current_user(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, db_session: AsyncSession
    ):
        """Test updating current user profile."""
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"first_name": "Updated", "last_name": "Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"

        # Verify in database
        result = await db_session.execute(select(User).where(User.id == uuid.UUID(test_user["id"])))
        db_user = result.scalar_one()
        assert db_user.first_name == "Updated"
        assert db_user.last_name == "Name"

    async def test_change_password_success(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, db_session: AsyncSession
    ):
        """Test changing password successfully."""
        new_password = "newpassword123"
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers=auth_headers,
            json={"current_password": test_user["password"], "new_password": new_password},
        )

        assert response.status_code == 204

        # Verify password was changed in database
        result = await db_session.execute(select(User).where(User.id == uuid.UUID(test_user["id"])))
        db_user = result.scalar_one()
        assert verify_password(new_password, db_user.password_hash)

    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers: dict):
        """Test changing password with wrong current password."""
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers=auth_headers,
            json={"current_password": "wrongpassword", "new_password": "newpassword123"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Current password is incorrect"


@pytest.mark.asyncio
class TestUsersCRUD:
    """Test /users CRUD endpoints."""

    async def test_create_user(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test creating a new user."""
        unique_id = uuid.uuid4().hex[:8]
        username = f"newuser_{unique_id}"
        email = f"newuser_{unique_id}@medbase.example"
        
        response = await client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "username": username,
                "email": email,
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == username
        assert data["email"] == email
        assert "id" in data

        # Verify user exists in database
        result = await db_session.execute(select(User).where(User.username == username))
        db_user = result.scalar_one()
        assert db_user.email == email
        assert db_user.first_name == "New"
        assert db_user.last_name == "User"
        assert db_user.is_active is True

    async def test_create_user_duplicate_username(self, client: AsyncClient, admin_headers: dict, test_user: dict):
        """Test creating user with existing username fails."""
        response = await client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "username": test_user["username"],  # Already exists
                "email": "different@medbase.example",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Username already registered"

    async def test_create_user_duplicate_email(self, client: AsyncClient, admin_headers: dict, test_user: dict):
        """Test creating user with existing email fails."""
        response = await client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "username": "differentuser",
                "email": test_user["email"],  # Already exists
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    async def test_create_user_unauthorized(self, client: AsyncClient):
        """Test creating user without auth fails."""
        response = await client.post(
            "/api/v1/users/",
            json={
                "username": "newuser",
                "email": "new@medbase.example",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
            },
        )

        assert response.status_code == 401

    async def test_list_users(self, client: AsyncClient, admin_headers: dict):
        """Test listing users with pagination."""
        response = await client.get("/api/v1/users/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["data"]) >= 1  # At least admin user

    async def test_list_users_pagination(self, client: AsyncClient, admin_headers: dict):
        """Test listing users with custom pagination."""
        response = await client.get(
            "/api/v1/users/",
            headers=admin_headers,
            params={"page": 1, "size": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5

    async def test_get_user_by_id(self, client: AsyncClient, admin_headers: dict, test_user: dict):
        """Test getting user by ID."""
        response = await client.get(
            f"/api/v1/users/{test_user['id']}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user["id"]
        assert data["username"] == test_user["username"]

    async def test_get_user_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting nonexistent user returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/v1/users/{fake_uuid}",
            headers=admin_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    async def test_update_user(
        self, client: AsyncClient, admin_headers: dict, test_user: dict, db_session: AsyncSession
    ):
        """Test updating user by ID."""
        response = await client.patch(
            f"/api/v1/users/{test_user['id']}",
            headers=admin_headers,
            json={"first_name": "UpdatedFirst"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "UpdatedFirst"

        # Verify in database
        result = await db_session.execute(select(User).where(User.id == uuid.UUID(test_user["id"])))
        db_user = result.scalar_one()
        assert db_user.first_name == "UpdatedFirst"

    async def test_delete_user(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test deleting a user."""
        unique_id = uuid.uuid4().hex[:8]
        username = f"deleteme_{unique_id}"
        
        # Create a user to delete
        create_response = await client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "username": username,
                "email": f"delete_{unique_id}@medbase.example",
                "password": "password123",
                "first_name": "Delete",
                "last_name": "Me",
            },
        )
        assert create_response.status_code == 201
        user_to_delete = create_response.json()

        # Verify user exists in database before deletion
        result = await db_session.execute(select(User).where(User.username == username))
        assert result.scalar_one_or_none() is not None

        response = await client.delete(
            f"/api/v1/users/{user_to_delete['id']}",
            headers=admin_headers,
        )

        assert response.status_code == 204

        # Verify user was removed from database
        result = await db_session.execute(select(User).where(User.username == username))
        assert result.scalar_one_or_none() is None

    async def test_delete_own_account_fails(self, client: AsyncClient, auth_headers: dict, test_user: dict):
        """Test deleting own account is not allowed."""
        response = await client.delete(
            f"/api/v1/users/{test_user['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Cannot delete your own account"
