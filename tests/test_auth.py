import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User


@pytest.mark.asyncio
class TestAuth:
    """Test authentication endpoints."""

    async def test_login_success(self, client: AsyncClient, test_user: dict):
        """Test successful login returns access token."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user["username"], "password": test_user["password"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_updates_last_login(
        self, client: AsyncClient, test_user: dict, db_session: AsyncSession
    ):
        """Test that login updates the last_login_at field."""
        # Get user's last_login before
        result = await db_session.execute(select(User).where(User.id == uuid.UUID(test_user["id"])))
        db_user = result.scalar_one()
        last_login_before = db_user.last_login_at

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user["username"], "password": test_user["password"]},
        )
        assert response.status_code == 200

        # Verify last_login_at was updated in database
        # Need to expire to get fresh data
        db_session.expire_all()
        result = await db_session.execute(select(User).where(User.id == uuid.UUID(test_user["id"])))
        db_user = result.scalar_one()
        
        assert db_user.last_login_at is not None
        if last_login_before is not None:
            assert db_user.last_login_at >= last_login_before

    async def test_login_wrong_password(self, client: AsyncClient, test_user: dict):
        """Test login with wrong password returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user["username"], "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent", "password": "anypassword"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    async def test_login_inactive_user(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession
    ):
        """Test login with inactive user returns 403."""
        unique_id = uuid.uuid4().hex[:8]
        username = f"inactiveuser_{unique_id}"
        
        # Create a user first
        create_response = await client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "username": username,
                "email": f"inactive_{unique_id}@medbase.example",
                "password": "password123",
                "first_name": "Inactive",
                "last_name": "User",
            },
        )
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Update the user to be inactive
        update_response = await client.patch(
            f"/api/v1/users/{user_id}",
            headers=admin_headers,
            json={"is_active": False},
        )
        assert update_response.status_code == 200

        # Verify user is inactive in database
        result = await db_session.execute(select(User).where(User.username == username))
        db_user = result.scalar_one()
        assert db_user.is_active is False

        # Try to login as inactive user
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": "password123"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Inactive user account"

    async def test_login_admin_success(self, client: AsyncClient):
        """Test admin login works with default credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
