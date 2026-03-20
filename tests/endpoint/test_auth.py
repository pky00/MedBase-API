"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient

from app.model.user import User


class TestAuthLogin:
    """Tests for POST /api/v1/auth/login"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, admin_user: User):
        """Test successful login with valid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testadmin", "password": "TestPass123!"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, admin_user: User):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testadmin", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent", "password": "TestPass123!"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, db_session):
        """Test login with inactive user."""
        from app.utility.security import get_password_hash
        from app.model.third_party import ThirdParty

        tp = ThirdParty(
            name="inactiveuser",
            email="inactive@test.com",
            is_active=False,
        )
        db_session.add(tp)
        await db_session.flush()
        await db_session.refresh(tp)

        user = User(
            third_party_id=tp.id,
            username="inactiveuser",
            password_hash=get_password_hash("TestPass123!"),
            role="user",
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "inactiveuser", "password": "TestPass123!"}
        )
        
        assert response.status_code == 401


class TestAuthLogout:
    """Tests for POST /api/v1/auth/logout"""
    
    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, admin_headers: dict):
        """Test successful logout."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_logout_unauthenticated(self, client: AsyncClient):
        """Test logout without authentication."""
        response = await client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401


class TestAuthMe:
    """Tests for GET /api/v1/auth/me"""
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test getting current user info."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testadmin"
        assert data["role"] == "admin"
        # third_party may or may not be loaded depending on query path
        if data.get("third_party"):
            assert data["third_party"]["email"] == "testadmin@test.com"
        assert "password_hash" not in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthenticated(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
