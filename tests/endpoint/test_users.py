"""Tests for user endpoints."""
import pytest
from httpx import AsyncClient

from app.model.user import User


class TestGetUsers:
    """Tests for GET /api/v1/users"""
    
    @pytest.mark.asyncio
    async def test_get_users_as_admin(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test getting users list as admin."""
        response = await client.get(
            "/api/v1/users",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["total"] >= 1
    
    @pytest.mark.asyncio
    async def test_get_users_as_regular_user(self, client: AsyncClient, user_headers: dict):
        """Test getting users list as regular user (should fail)."""
        response = await client.get(
            "/api/v1/users",
            headers=user_headers
        )
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_users_unauthenticated(self, client: AsyncClient):
        """Test getting users list without authentication."""
        response = await client.get("/api/v1/users")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_users_with_filters(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test getting users with filters."""
        response = await client.get(
            "/api/v1/users",
            params={"role": "admin", "is_active": True},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        for user in data["items"]:
            assert user["role"] == "admin"
            assert user["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_get_users_pagination(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test users pagination."""
        response = await client.get(
            "/api/v1/users",
            params={"page": 1, "size": 5},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5


class TestGetUser:
    """Tests for GET /api/v1/users/{user_id}"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test getting user by ID."""
        response = await client.get(
            f"/api/v1/users/{admin_user.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == admin_user.id
        assert data["username"] == admin_user.username
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent user."""
        response = await client.get(
            "/api/v1/users/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestCreateUser:
    """Tests for POST /api/v1/users"""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test creating a new user."""
        user_data = {
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "newpass123",
            "role": "user",
            "is_active": True
        }
        
        response = await client.post(
            "/api/v1/users",
            json=user_data,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "user"
        assert "password" not in data
        assert "password_hash" not in data
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test creating user with duplicate username."""
        user_data = {
            "username": "testadmin",  # Already exists
            "email": "another@test.com",
            "password": "newpass123",
            "role": "user"
        }
        
        response = await client.post(
            "/api/v1/users",
            json=user_data,
            headers=admin_headers
        )
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test creating user with duplicate email."""
        user_data = {
            "username": "newusername",
            "email": "testadmin@test.com",  # Already exists
            "password": "newpass123",
            "role": "user"
        }
        
        response = await client.post(
            "/api/v1/users",
            json=user_data,
            headers=admin_headers
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_role(self, client: AsyncClient, admin_headers: dict):
        """Test creating user with invalid role."""
        user_data = {
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "newpass123",
            "role": "invalid_role"
        }
        
        response = await client.post(
            "/api/v1/users",
            json=user_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestUpdateUser:
    """Tests for PUT /api/v1/users/{user_id}"""
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session):
        """Test updating a user."""
        # Create a user to update
        from app.utility.security import get_password_hash
        
        user = User(
            username="toupdate",
            email="toupdate@test.com",
            password_hash=get_password_hash("testpass123"),
            role="user",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        update_data = {
            "username": "updated",
            "email": "updated@test.com"
        }
        
        response = await client.put(
            f"/api/v1/users/{user.id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updated"
        assert data["email"] == "updated@test.com"
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent user."""
        response = await client.put(
            "/api/v1/users/99999",
            json={"username": "test"},
            headers=admin_headers
        )
        
        assert response.status_code == 404


class TestDeleteUser:
    """Tests for DELETE /api/v1/users/{user_id}"""
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session):
        """Test deleting a user."""
        from app.utility.security import get_password_hash
        
        user = User(
            username="todelete",
            email="todelete@test.com",
            password_hash=get_password_hash("testpass123"),
            role="user",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        response = await client.delete(
            f"/api/v1/users/{user.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_delete_self_forbidden(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test admin cannot delete themselves."""
        response = await client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 400
        assert "cannot delete themselves" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent user."""
        response = await client.delete(
            "/api/v1/users/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 404
