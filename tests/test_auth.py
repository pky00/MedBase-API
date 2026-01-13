import pytest
from httpx import AsyncClient


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

    async def test_login_inactive_user(self, client: AsyncClient, admin_headers: dict):
        """Test login with inactive user returns 403."""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        
        # Create a user first
        create_response = await client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "username": f"inactiveuser_{unique_id}",
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

        # Try to login as inactive user
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": f"inactiveuser_{unique_id}", "password": "password123"},
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
